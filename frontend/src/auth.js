function byId(id) {
  return document.getElementById(id);
}

function setOutput(id, text, isError = false) {
  const node = byId(id);
  if (!node) return;
  node.textContent = text;
  node.classList.toggle("text-danger", isError);
  node.classList.toggle("text-success", !isError && Boolean(text));
}

function redirectAfterAuth() {
  window.location.href = "./index.html";
}

document.addEventListener("DOMContentLoaded", () => {
  byId("btnRegister")?.addEventListener("click", async () => {
    setOutput("registerOutput", "");
    try {
      const email = (byId("registerEmail")?.value ?? "").trim();
      const username = (byId("registerUsername")?.value ?? "").trim();
      const password = (byId("registerPassword")?.value ?? "").trim();
      if (!email || !username || !password) {
        throw new Error("Email, username, and password are required.");
      }

      const data = await window.mpesaApi.register({ email, username, password });
      setOutput("registerOutput", `Account created for ${data?.user?.username || username}. Redirecting...`);
      setTimeout(redirectAfterAuth, 300);
    } catch (error) {
      setOutput("registerOutput", `Error: ${error.message}`, true);
    }
  });

  byId("btnLogin")?.addEventListener("click", async () => {
    setOutput("loginOutput", "");
    try {
      const identifier = (byId("loginIdentifier")?.value ?? "").trim();
      const password = (byId("loginPassword")?.value ?? "").trim();
      if (!identifier || !password) {
        throw new Error("Identifier and password are required.");
      }

      const data = await window.mpesaApi.login({ identifier, password });
      setOutput("loginOutput", `Signed in as ${data?.user?.username || identifier}. Redirecting...`);
      setTimeout(redirectAfterAuth, 300);
    } catch (error) {
      setOutput("loginOutput", `Error: ${error.message}`, true);
    }
  });
});
