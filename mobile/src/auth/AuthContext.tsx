import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { ApiError, getCurrentUser, loginUser, normalizeApiBase, registerUser } from "../api/client";
import type { AuthUser, LoginPayload, RegisterPayload } from "../api/types";
import { resolveDefaultApiBase } from "../config/api";
import {
  clearToken,
  clearUser,
  loadApiBase,
  loadToken,
  loadUser,
  saveApiBase,
  saveToken,
  saveUser,
} from "../storage/session";

type AuthContextValue = {
  booting: boolean;
  busy: boolean;
  token: string | null;
  user: AuthUser | null;
  apiBase: string;
  setApiBase: (value: string) => Promise<void>;
  login: (payload: LoginPayload, apiBaseOverride?: string) => Promise<void>;
  register: (payload: RegisterPayload, apiBaseOverride?: string) => Promise<void>;
  refreshUser: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

type Props = {
  children: ReactNode;
};

export function AuthProvider({ children }: Props) {
  const [booting, setBooting] = useState(true);
  const [busy, setBusy] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [apiBase, setApiBaseState] = useState(resolveDefaultApiBase());

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      try {
        const persistedApiBase = normalizeApiBase((await loadApiBase()) || resolveDefaultApiBase());
        const persistedToken = await loadToken();
        const persistedUser = await loadUser();

        if (!mounted) return;

        setApiBaseState(persistedApiBase || resolveDefaultApiBase());
        setToken(persistedToken);
        setUser(persistedUser);

        if (persistedToken) {
          try {
            const freshUser = await getCurrentUser(persistedApiBase, persistedToken);
            if (!mounted) return;
            setUser(freshUser);
            await saveUser(freshUser);
          } catch (error) {
            if (error instanceof ApiError && error.status === 401) {
              await Promise.all([clearToken(), clearUser()]);
              if (!mounted) return;
              setToken(null);
              setUser(null);
            }
          }
        }
      } finally {
        if (!mounted) return;
        setBooting(false);
      }
    }

    void bootstrap();

    return () => {
      mounted = false;
    };
  }, []);

  const setApiBase = useCallback(async (value: string) => {
    const normalized = normalizeApiBase(value);
    if (!normalized) {
      throw new Error("API base URL is required.");
    }

    setApiBaseState(normalized);
    await saveApiBase(normalized);
  }, []);

  const persistAuth = useCallback(async (nextToken: string, nextUser: AuthUser) => {
    setToken(nextToken);
    setUser(nextUser);
    await Promise.all([saveToken(nextToken), saveUser(nextUser)]);
  }, []);

  const resolveRequestApiBase = useCallback(
    (apiBaseOverride?: string) => {
      const resolved = normalizeApiBase(apiBaseOverride ?? apiBase);
      if (!resolved) {
        throw new Error("API base URL is required.");
      }
      return resolved;
    },
    [apiBase],
  );

  const login = useCallback(
    async (payload: LoginPayload, apiBaseOverride?: string) => {
      setBusy(true);
      try {
        const result = await loginUser(resolveRequestApiBase(apiBaseOverride), payload);
        await persistAuth(result.access_token, result.user);
      } finally {
        setBusy(false);
      }
    },
    [persistAuth, resolveRequestApiBase],
  );

  const register = useCallback(
    async (payload: RegisterPayload, apiBaseOverride?: string) => {
      setBusy(true);
      try {
        const result = await registerUser(resolveRequestApiBase(apiBaseOverride), payload);
        await persistAuth(result.access_token, result.user);
      } finally {
        setBusy(false);
      }
    },
    [persistAuth, resolveRequestApiBase],
  );

  const refreshUser = useCallback(async () => {
    if (!token) {
      throw new Error("No active session.");
    }
    const freshUser = await getCurrentUser(apiBase, token);
    setUser(freshUser);
    await saveUser(freshUser);
  }, [apiBase, token]);

  const logout = useCallback(async () => {
    setToken(null);
    setUser(null);
    await Promise.all([clearToken(), clearUser()]);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      booting,
      busy,
      token,
      user,
      apiBase,
      setApiBase,
      login,
      register,
      refreshUser,
      logout,
    }),
    [apiBase, booting, busy, login, logout, refreshUser, register, setApiBase, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
