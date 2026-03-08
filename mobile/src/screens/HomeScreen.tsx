import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { getSummary } from "../api/client";
import type { SummaryResponse } from "../api/types";
import { useAuth } from "../auth/AuthContext";

function formatAmount(value: number, currency: string): string {
  const normalized = Number.isFinite(value) ? value : 0;
  return `${currency} ${normalized.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

export function HomeScreen() {
  const { apiBase, setApiBase, token, user, refreshUser, logout } = useAuth();

  const [apiBaseInput, setApiBaseInput] = useState(apiBase);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [screenMessage, setScreenMessage] = useState<string | null>(null);
  const [screenError, setScreenError] = useState<string | null>(null);

  const topCategories = useMemo(() => summary?.categories ?? [], [summary]);

  useEffect(() => {
    setApiBaseInput(apiBase);
  }, [apiBase]);

  async function loadSummary() {
    if (!token) return;

    setLoadingSummary(true);
    setScreenError(null);
    try {
      const data = await getSummary(apiBase, token);
      setSummary(data);
    } catch (error) {
      setScreenError(error instanceof Error ? error.message : "Failed to load summary.");
    } finally {
      setLoadingSummary(false);
    }
  }

  async function saveApiBase() {
    setScreenError(null);
    setScreenMessage(null);
    try {
      await setApiBase(apiBaseInput);
      setScreenMessage("API base updated. Tap Refresh Summary.");
    } catch (error) {
      setScreenError(error instanceof Error ? error.message : "Could not update API base.");
    }
  }

  async function refreshProfile() {
    setScreenError(null);
    setScreenMessage(null);
    try {
      await refreshUser();
      setScreenMessage("User profile refreshed.");
    } catch (error) {
      setScreenError(error instanceof Error ? error.message : "Could not refresh profile.");
    }
  }

  useEffect(() => {
    void loadSummary();
  }, [apiBase, token]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>M-PESA Dashboard</Text>
        <Text style={styles.subtitle}>Phase 1: auth + API connection + summary</Text>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Signed in user</Text>
          <Text style={styles.metaText}>Username: {user?.username ?? "-"}</Text>
          <Text style={styles.metaText}>Email: {user?.email ?? "-"}</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>API Settings</Text>
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
          <View style={styles.row}>
            <Pressable onPress={saveApiBase} style={styles.secondaryButton}>
              <Text style={styles.secondaryButtonText}>Save API Base</Text>
            </Pressable>
            <Pressable onPress={refreshProfile} style={styles.secondaryButton}>
              <Text style={styles.secondaryButtonText}>Refresh Profile</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.card}>
          <View style={styles.summaryHeaderRow}>
            <Text style={styles.sectionTitle}>Summary</Text>
            <Pressable onPress={loadSummary} style={styles.refreshButton}>
              <Text style={styles.refreshButtonText}>Refresh Summary</Text>
            </Pressable>
          </View>

          {loadingSummary ? (
            <View style={styles.loadingRow}>
              <ActivityIndicator color="#0d8a43" />
              <Text style={styles.loadingText}>Loading summary...</Text>
            </View>
          ) : null}

          {!loadingSummary ? (
            <>
              <Text style={styles.totalLabel}>Total spent</Text>
              <Text style={styles.totalValue}>
                {summary ? formatAmount(summary.total_spent, summary.currency) : "No summary yet"}
              </Text>

              <Text style={styles.categoryTitle}>Categories</Text>
              {topCategories.length === 0 ? <Text style={styles.metaText}>No category data yet.</Text> : null}

              {topCategories.map((item) => (
                <View key={`${item.category}-${item.amount}`} style={styles.categoryRow}>
                  <Text style={styles.categoryName}>{item.category}</Text>
                  <Text style={styles.categoryAmount}>{formatAmount(item.amount, summary?.currency ?? "KES")}</Text>
                </View>
              ))}
            </>
          ) : null}
        </View>

        <Pressable onPress={logout} style={styles.signOutButton}>
          <Text style={styles.signOutText}>Sign Out</Text>
        </Pressable>

        {screenError ? <Text style={styles.errorText}>{screenError}</Text> : null}
        {screenMessage ? <Text style={styles.infoText}>{screenMessage}</Text> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f2f6fb",
  },
  container: {
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#0f1722",
  },
  subtitle: {
    fontSize: 14,
    color: "#44556a",
    marginTop: 4,
    marginBottom: 12,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: "#d6dee8",
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1b2a3a",
    marginBottom: 10,
  },
  metaText: {
    fontSize: 14,
    color: "#32465a",
    marginBottom: 4,
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
    marginBottom: 10,
  },
  row: {
    flexDirection: "row",
    gap: 10,
  },
  summaryHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  refreshButton: {
    borderRadius: 9,
    borderWidth: 1,
    borderColor: "#96a6b9",
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  refreshButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#2f4155",
  },
  secondaryButton: {
    flex: 1,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#96a6b9",
    paddingVertical: 10,
    alignItems: "center",
  },
  secondaryButtonText: {
    color: "#2f4155",
    fontWeight: "600",
    fontSize: 13,
  },
  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 10,
  },
  loadingText: {
    fontSize: 14,
    color: "#2f4155",
  },
  totalLabel: {
    color: "#566779",
    fontSize: 13,
  },
  totalValue: {
    fontSize: 26,
    fontWeight: "700",
    color: "#0d8a43",
    marginTop: 2,
    marginBottom: 10,
  },
  categoryTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#1c2c3e",
    marginBottom: 6,
  },
  categoryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#edf2f7",
  },
  categoryName: {
    fontSize: 14,
    color: "#2d3f53",
  },
  categoryAmount: {
    fontSize: 14,
    fontWeight: "600",
    color: "#2d3f53",
  },
  signOutButton: {
    backgroundColor: "#1f2f42",
    borderRadius: 10,
    alignItems: "center",
    paddingVertical: 12,
    marginBottom: 10,
  },
  signOutText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "700",
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
