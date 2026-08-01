// CyberShield Ghana - shared browser logic (auth guard, nav, helpers)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";
import { firebaseConfig } from "./firebase-config.js";

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

// ---------- auth guard ----------
export function requireAuth(callback) {
  onAuthStateChanged(auth, (user) => {
    if (!user) {
      window.location.replace("login.html");
      return;
    }
    callback(user);
  });
}

export function redirectIfSignedIn(callback) {
  onAuthStateChanged(auth, (user) => {
    if (user) {
      window.location.replace("dashboard.html");
      return;
    }
    if (typeof callback === "function") callback();
  });
}

// ---------- navigation (mirrors the desktop base.html navbar) ----------
const NAV_ITEMS = [
  ["dashboard.html", "Home"],
  ["report.html", "Report"],
  ["reports.html", "Cyber Log"],
  ["awareness.html", "Stay Safe"],
];

export function renderNav(activePage) {
  const host = document.getElementById("navbar");
  if (!host) return;
  const user = auth.currentUser;
  const fullName = user && user.displayName ? user.displayName : (user && user.email ? user.email.split("@")[0] : "");
  const firstName = fullName ? fullName.split(" ")[0] : "";

  const links = NAV_ITEMS
    .map(([href, label]) =>
      `<li class="nav-item"><a class="nav-link ${href === activePage ? "active" : ""}" href="${href}">${label}</a></li>`)
    .join("");

  host.innerHTML = `
  <nav class="navbar navbar-expand-lg navbar-light sticky-top">
    <div class="container">
      <a class="navbar-brand" href="dashboard.html">🛡️ Cyber<span>Shield</span></a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          ${links}
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item">
            <a class="nav-link" href="notifications.html">🔔 Notifications</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="profile.html">👤 ${esc(firstName)}</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#" id="logoutLink">Logout</a>
          </li>
        </ul>
      </div>
    </div>
  </nav>`;

  document.getElementById("logoutLink").addEventListener("click", async (e) => {
    e.preventDefault();
    await signOut(auth);
    window.location.replace("index.html");
  });
}

// ---------- helpers ----------
export function showFlash(msg, type = "info") {
  const el = document.getElementById("flash");
  if (!el) return;
  const cls = { info: "alert-info", success: "alert-success", error: "alert-danger" }[type] || "alert-info";
  el.className = `alert ${cls} mb-4`;
  el.textContent = msg;
  el.classList.remove("d-none");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

export function clearFlash() {
  const el = document.getElementById("flash");
  if (el) el.classList.add("d-none");
}

export function fmtDate(ts) {
  if (!ts) return "N/A";
  if (ts.toDate) ts = ts.toDate();
  const d = ts instanceof Date ? ts : new Date(ts);
  return d.toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
  });
}

export function statusLabel(s) {
  return String(s || "").split("_").map(w => w[0].toUpperCase() + w.slice(1)).join(" ");
}

export function statusBadge(s) {
  return `<span class="badge badge-status badge-${esc(s || "draft")}">${esc(statusLabel(s))}</span>`;
}

export function fmtDay(ts) {
  if (!ts) return "N/A";
  if (ts.toDate) ts = ts.toDate();
  const d = ts instanceof Date ? ts : new Date(ts);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function esc(str) {
  if (str == null) return "";
  return String(str).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}
