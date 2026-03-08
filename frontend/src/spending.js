function splitBulkMessages(text) {
  return text
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

function setInputMode(mode) {
  const tabSingle = byId("tabSingle");
  const tabBulk = byId("tabBulk");
  const panelSingle = byId("panelSingle");
  const panelBulk = byId("panelBulk");
  if (!tabSingle || !tabBulk || !panelSingle || !panelBulk) return;

  const isSingle = mode === "single";
  tabSingle.classList.toggle("active", isSingle);
  tabBulk.classList.toggle("active", !isSingle);
  tabSingle.setAttribute("aria-selected", isSingle ? "true" : "false");
  tabBulk.setAttribute("aria-selected", !isSingle ? "true" : "false");
  panelSingle.classList.toggle("d-none", !isSingle);
  panelBulk.classList.toggle("d-none", isSingle);
}

document.addEventListener("DOMContentLoaded", () => {
  setInputMode("single");

  byId("tabSingle")?.addEventListener("click", () => setInputMode("single"));
  byId("tabBulk")?.addEventListener("click", () => setInputMode("bulk"));

  byId("btnAnalyzeSingle")?.addEventListener("click", async () => {
    const out = byId("singleOutput");
    if (out) out.textContent = "";
    try {
      const sms = (byId("singleInput")?.value ?? "").trim();
      const userNote = (byId("singlePurpose")?.value ?? "").trim();
      if (!sms) throw new Error("Paste one message first.");
      const payload = { message: sms };
      if (userNote) payload.user_note = userNote;
      const data = await window.mpesaApi.post("/analyze", payload);
      if (out) out.textContent = pretty(data);
    } catch (e) {
      if (out) out.textContent = `Error: ${e.message}`;
    }
  });

  byId("btnClearSingle")?.addEventListener("click", () => {
    const input = byId("singleInput");
    const purpose = byId("singlePurpose");
    const out = byId("singleOutput");
    if (input) input.value = "";
    if (purpose) purpose.value = "";
    if (out) out.textContent = "";
  });

  byId("btnAnalyzeBulk")?.addEventListener("click", async () => {
    const out = byId("bulkOutput");
    if (out) out.textContent = "";
    try {
      const messages = splitBulkMessages(byId("bulkInput")?.value ?? "");
      const userNote = (byId("bulkPurpose")?.value ?? "").trim();
      if (!messages.length) throw new Error("Paste at least one message (one per line).");
      const payload = { messages };
      if (userNote) payload.user_note = userNote;
      const data = await window.mpesaApi.post("/analyze/bulk", payload);
      if (out) out.textContent = pretty(data);
    } catch (e) {
      if (out) out.textContent = `Error: ${e.message}`;
    }
  });

  byId("btnClearBulk")?.addEventListener("click", () => {
    const input = byId("bulkInput");
    const purpose = byId("bulkPurpose");
    const out = byId("bulkOutput");
    if (input) input.value = "";
    if (purpose) purpose.value = "";
    if (out) out.textContent = "";
  });
});
