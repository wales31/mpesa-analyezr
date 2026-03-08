import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { checkHealth, normalizeApiBase } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type Mode = "login" | "register";

export function AuthScreen() {
  const { apiBase, setApiBase, login, register, busy } = useAuth();

  const [mode, setMode] = useState<Mode>("login");
  const [apiBaseInput, setApiBaseInput] = useState(apiBase);

  const [identifier, setIdentifier] = useState("");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  const submitLabel = useMemo(() => (mode === "login" ? "Sign In" : "Create Account"), [mode]);

  useEffect(() => {
    setApiBaseInput(apiBase);
  }, [apiBase]);

  async function syncApiBaseInput(): Promise<string> {
    const normalized = normalizeApiBase(apiBaseInput);
    if (!normalized) {
      throw new Error("API base URL is required.");
    }

    if (normalized !== apiBase) {
      await setApiBase(normalized);
    }

    setApiBaseInput(normalized);
    return normalized;
  }

  async function saveApiBase() {
    setErrorMessage(null);
    setInfoMessage(null);
    try {
      await syncApiBaseInput();
      setInfoMessage("API base updated.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Could not update API base.");
    }
  }

  async function testApiBase() {
    setErrorMessage(null);
    setInfoMessage(null);
    try {
      const normalized = normalizeApiBase(apiBaseInput);
      if (!normalized) {
        throw new Error("API base URL is required.");
      }

      setApiBaseInput(normalized);
      const data = await checkHealth(normalized);
      setInfoMessage(data?.message ? `API reachable: ${data.message}` : "API reachable.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "API test failed.");
    }
  }

  async function submit() {
    setErrorMessage(null);
    setInfoMessage(null);

    try {
      const requestApiBase = await syncApiBaseInput();

      if (!password.trim()) {
        throw new Error("Password is required.");
      }

      if (mode === "login") {
        if (!identifier.trim()) {
          throw new Error("Email or username is required.");
        }

        await login(
          {
            identifier: identifier.trim(),
            password: password.trim(),
          },
          requestApiBase,
        );
        return;
      }

      if (!email.trim() || !username.trim()) {
        throw new Error("Email and username are required.");
      }

      await register(
        {
          email: email.trim(),
          username: username.trim(),
          password: password.trim(),
        },
        requestApiBase,
      );
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Authentication failed.");
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.select({ ios: "padding", android: undefined })}
        style={styles.container}
      >
        <Text style={styles.title}>M-PESA Analyzer</Text>
        <Text style={styles.subtitle}>Phase 1 mobile foundation</Text>

        <View style={styles.card}>
          <Text style={styles.label}>API Base URL</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            onChangeText={setApiBaseInput}
            placeholder="http://192.168.1.24:8000"
            placeholderTextColor="#6f7d8c"
            style={styles.input}
            value={apiBaseInput}
          />
          <View style={styles.apiRow}>
            <Pressable onPress={saveApiBase} style={styles.secondaryButton}>
              <Text style={styles.secondaryButtonText}>Save API Base</Text>
            </Pressable>
            <Pressable onPress={testApiBase} style={styles.secondaryButton}>
              <Text style={styles.secondaryButtonText}>Test API</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.modeRow}>
          <Pressable
            onPress={() => setMode("login")}
            style={[styles.modeButton, mode === "login" && styles.modeButtonActive]}
          >
            <Text style={[styles.modeText, mode === "login" && styles.modeTextActive]}>Login</Text>
          </Pressable>
          <Pressable
            onPress={() => setMode("register")}
            style={[styles.modeButton, mode === "register" && styles.modeButtonActive]}
          >
            <Text style={[styles.modeText, mode === "register" && styles.modeTextActive]}>Register</Text>
          </Pressable>
        </View>

        <View style={styles.card}>
          {mode === "login" ? (
            <>
              <Text style={styles.label}>Email or Username</Text>
              <TextInput
                autoCapitalize="none"
                autoCorrect={false}
                onChangeText={setIdentifier}
                placeholder="you@example.com"
                placeholderTextColor="#6f7d8c"
                style={styles.input}
                value={identifier}
              />
            </>
          ) : (
            <>
              <Text style={styles.label}>Email</Text>
              <TextInput
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
                onChangeText={setEmail}
                placeholder="you@example.com"
                placeholderTextColor="#6f7d8c"
                style={styles.input}
                value={email}
              />

              <Text style={styles.label}>Username</Text>
              <TextInput
                autoCapitalize="none"
                autoCorrect={false}
                onChangeText={setUsername}
                placeholder="yourname"
                placeholderTextColor="#6f7d8c"
                style={styles.input}
                value={username}
              />
            </>
          )}

          <Text style={styles.label}>Password</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={setPassword}
            placeholder="Your password"
            placeholderTextColor="#6f7d8c"
            secureTextEntry
            style={styles.input}
            value={password}
          />

          <Pressable disabled={busy} onPress={submit} style={[styles.primaryButton, busy && styles.buttonBusy]}>
            {busy ? <ActivityIndicator color="#ffffff" /> : <Text style={styles.primaryButtonText}>{submitLabel}</Text>}
          </Pressable>
        </View>

        {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
        {infoMessage ? <Text style={styles.infoText}>{infoMessage}</Text> : null}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f3f6fa",
  },
  container: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 18,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#0f1722",
  },
  subtitle: {
    fontSize: 14,
    color: "#3f4f63",
    marginTop: 4,
    marginBottom: 14,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: "#d6dee8",
    marginBottom: 12,
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1f2d3d",
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderColor: "#c8d3df",
    backgroundColor: "#f9fbfd",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    color: "#0f1722",
    marginBottom: 12,
  },
  modeRow: {
    flexDirection: "row",
    marginBottom: 12,
    gap: 10,
  },
  apiRow: {
    flexDirection: "row",
    gap: 10,
  },
  modeButton: {
    flex: 1,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#bcc9d8",
    paddingVertical: 10,
    alignItems: "center",
    backgroundColor: "#ffffff",
  },
  modeButtonActive: {
    backgroundColor: "#0d8a43",
    borderColor: "#0d8a43",
  },
  modeText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#33455a",
  },
  modeTextActive: {
    color: "#ffffff",
  },
  primaryButton: {
    backgroundColor: "#0d8a43",
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
  },
  primaryButtonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
  },
  secondaryButton: {
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#96a6b9",
    paddingVertical: 10,
    alignItems: "center",
  },
  secondaryButtonText: {
    color: "#2f4155",
    fontWeight: "600",
    fontSize: 14,
  },
  buttonBusy: {
    opacity: 0.7,
  },
  errorText: {
    color: "#b23a3a",
    fontSize: 13,
  },
  infoText: {
    color: "#0d7a3c",
    fontSize: 13,
  },
});
