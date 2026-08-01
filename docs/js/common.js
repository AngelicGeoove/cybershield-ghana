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
      window.location.replace("index.html");
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

// ---------- navigation ----------
const NAV_ITEMS = [
  ["dashboard.html", "Dashboard"],
  ["report.html", "Report Incident"],
  ["reports.html", "My Reports"],
  ["notifications.html", "Notifications"],
  ["awareness.html", "Stay Safe"],
  ["channels.html", "Contact CSA"],
];

export function renderNav(activePage) {
  const navbar = document.getElementById("navbar");
  if (!navbar) return;
  const user = auth.currentUser;
  const links = NAV_ITEMS.map(([href, label]) =>
    `<a href="${href}" class="${href === activePage ? "active" : ""}">${label}</a>`
  ).join("");
  const fullName = user && user.displayName ? user.displayName : (user && user.email ? user.email.split("@")[0] : "");
  const firstName = fullName ? fullName.split(" ")[0] : "";
  navbar.innerHTML = `
    <a class="brand" href="dashboard.html">Cyber<span>Shield</span> Ghana</a>
    <div class="nav-links">
      ${links}
      <a href="profile.html">Profile</a>
      <span class="nav-user">${firstName ? `👤 ${firstName}` : ""}</span>
      <a href="#" id="logoutLink" title="Sign out">Logout</a>
    </div>`;
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
  el.className = `alert alert-${type}`;
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
  return `<span class="badge badge-${s || "draft"}">${statusLabel(s)}</span>`;
}

export function esc(str) {
  if (str == null) return "";
  return String(str).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}
