import { ActivityIndicator, SafeAreaView, StyleSheet, Text } from "react-native";
import { StatusBar } from "expo-status-bar";

import { AuthProvider, useAuth } from "./src/auth/AuthContext";
import { AuthScreen } from "./src/screens/AuthScreen";
import { HomeScreen } from "./src/screens/HomeScreen";

function AppContent() {
  const { booting, token } = useAuth();

  if (booting) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0d8a43" />
        <Text style={styles.loadingText}>Starting app...</Text>
      </SafeAreaView>
    );
  }

  return token ? <HomeScreen /> : <AuthScreen />;
}

export default function App() {
  return (
    <AuthProvider>
      <StatusBar style="dark" />
      <AppContent />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f2f6fb",
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: "#2f4155",
  },
});
