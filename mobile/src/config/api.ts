import { Platform } from "react-native";

import { normalizeApiBase } from "../api/client";

const ANDROID_EMULATOR_BASE = "http://10.0.2.2:8000";
const IOS_SIMULATOR_BASE = "http://127.0.0.1:8000";

export function resolveDefaultApiBase(): string {
  const envBase = normalizeApiBase(process.env.EXPO_PUBLIC_MPESA_API_BASE || "");
  if (envBase) return envBase;

  if (Platform.OS === "android") {
    return ANDROID_EMULATOR_BASE;
  }

  return IOS_SIMULATOR_BASE;
}
