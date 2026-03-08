import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";

import type { AuthUser } from "../api/types";

const TOKEN_KEY = "mpesa_mobile_auth_token";
const USER_KEY = "mpesa_mobile_auth_user";
const API_BASE_KEY = "mpesa_mobile_api_base";

export async function saveToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
}

export async function loadToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function clearToken(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
}

export async function saveUser(user: AuthUser): Promise<void> {
  await AsyncStorage.setItem(USER_KEY, JSON.stringify(user));
}

export async function loadUser(): Promise<AuthUser | null> {
  const raw = await AsyncStorage.getItem(USER_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export async function clearUser(): Promise<void> {
  await AsyncStorage.removeItem(USER_KEY);
}

export async function saveApiBase(apiBase: string): Promise<void> {
  await AsyncStorage.setItem(API_BASE_KEY, apiBase);
}

export async function loadApiBase(): Promise<string | null> {
  return AsyncStorage.getItem(API_BASE_KEY);
}
