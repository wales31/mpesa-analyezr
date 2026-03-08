window.mpesaApp = window.mpesaApp ?? {};

function isAuthPage() {
  return window.location.pathname.toLowerCase().endsWith("/auth.html");
}

function redirectToAuthPage() {
  window.location.href = "./auth.html";
}

function redirectToDashboard() {
  window.location.href = "./index.html";
}

function wireSignOutButton() {
  const btn = document.getElementById("btnSignOut");
  if (!btn) return;

  const hasToken = Boolean(window.mpesaApi?.getToken?.());
  btn.classList.toggle("d-none", !hasToken);
  btn.addEventListener("click", () => {
    window.mpesaApi?.logout?.();
    redirectToAuthPage();
  });
}

function ensureAuthNotice(hasToken) {
  const root = document.querySelector("main.container");
  if (!root) return;

  const existing = document.getElementById("appAuthNotice");
  if (hasToken) {
    if (existing) existing.remove();
    return;
  }

  if (existing) return;

  const notice = document.createElement("section");
  notice.id = "appAuthNotice";
  notice.className = "alert alert-warning border-0 shadow-sm mb-3";
  notice.innerHTML = `
    <div class="d-flex align-items-start justify-content-between gap-3 flex-wrap">
      <div>
        <div class="fw-semibold">Sign in required for live data</div>
        <div class="small mb-0">
          You can view the interface now, but loading insights and transactions requires authentication.
        </div>
      </div>
      <a class="btn btn-outline-secondary btn-sm" href="./auth.html">Open Sign In</a>
    </div>
  `;
  root.prepend(notice);
}

document.addEventListener("DOMContentLoaded", () => {
  const hasToken = Boolean(window.mpesaApi?.getToken?.());
  window.mpesaApp.hasToken = hasToken;
  window.mpesaApp.authRequired = !isAuthPage() && !hasToken;

  if (isAuthPage() && hasToken) {
    window.mpesaApi
      ?.me?.()
      .then(() => {
        redirectToDashboard();
      })
      .catch(() => {
        window.mpesaApi?.clearToken?.();
        window.mpesaApp.hasToken = false;
      });
  }

  wireSignOutButton();
  ensureAuthNotice(Boolean(window.mpesaApi?.getToken?.()));

  if (typeof CustomEvent === "function") {
    document.dispatchEvent(
      new CustomEvent("mpesa:auth", { detail: { hasToken: Boolean(window.mpesaApi?.getToken?.()) } }),
    );
  }
});

if (!window.mpesaApp.apiCheckPromise) {
  window.mpesaApp.apiCheckPromise = window.mpesaApi?.check?.() ?? Promise.resolve(null);
}

window.mpesaApp.apiCheckPromise.then((data) => {
  if (typeof CustomEvent !== "function") return;
  document.dispatchEvent(new CustomEvent("mpesa:api", { detail: { online: Boolean(data), data } }));
});
