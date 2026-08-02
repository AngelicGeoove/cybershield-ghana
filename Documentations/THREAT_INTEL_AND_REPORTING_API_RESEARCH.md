# CyberShield Ghana — Free Cybercrime / Threat-Intel API Research Report

**Date:** 2026-08-02 · **Scope:** Free & freemium APIs, official reporting platforms, and datasets a student project can integrate. Details below were verified against official docs where possible (flagged ✔ = verified this session; ⚠ = based on public knowledge, re-verify before relying on it).

> **✅ IMPLEMENTED 2026-08-02** — see **Section 5. What Was Implemented** at the bottom for the integration status of each recommendation.

---

## 0. Executive Summary (TL;DR)

| Need | Best free option | From browser? | From your Flask desktop app? |
|---|---|---|---|
| Is a URL phishing/malicious? | **Google Safe Browsing Lookup** (free, non-commercial) | ⚠ possible (key exposed) — prefer server | ✔ YES |
| Multi-AV URL/IP/hash scan | **VirusTotal** (free ~500 req/day) | ⚠ possible (key exposed, tiny quota) | ✔ YES |
| Is an IP abusive? | **AbuseIPDB** (free 1,000 checks/day) | ✖ CORS explicitly blocked | ✔ YES |
| URL/domain in malware lists | **URLhaus** + **ThreatFox** (free auth key) | ✖ | ✔ YES |
| Domain resolves? MX exists? (email check) | **Cloudflare / Google DNS-over-HTTPS** | ✔ YES (no key, CORS) | ✔ YES |
| Domain registration age (new-domain phishing signal) | **RDAP via rdap.org** | ✔ YES (no key, CORS) | ✔ YES |
| Is a password breached? | **HIBP Pwned Passwords** range API | ✔ YES (no key, CORS) | ✔ YES |
| Phishing URL list (client-side check) | **OpenPhish community feed** (GitHub raw) | ✔ YES (CORS) | ✔ YES |
| Email breached? (account exposure) | **HIBP email search** | ✖ paid key + no CORS | ⚠ paid — NOT free |
| Phone number reputation | **none good & free** (numverify/AbstractAPI freemium, Twilio paid) | ✖ | ⚠ tiny quotas |
| Official reporting (Ghana) | **CSA portal (report.csa.gov.gh)**, Ghana Police CID Cybercrime Unit | — web form/portal, no API | — |

**Bottom line for CyberShield Ghana:**
- **Desktop app (Flask + Python):** integrate Google Safe Browsing + VirusTotal + AbuseIPDB + URLhaus/ThreatFox + ip-api.com — all free, all server-side, all key-based but safe on the server.
- **Browser SPA (GitHub Pages, HTTPS):** use the **no-key, CORS-enabled** trio — DNS-over-HTTPS (domain/MX existence), **RDAP** (domain age), **Pwned Passwords** (password breach) — plus the **OpenPhish community feed** for a client-side phishing list. Everything key-based (VirusTotal, AbuseIPDB, Safe Browsing) is either CORS-blocked or exposes the key, so it belongs behind a server or in the desktop app only.
- **Phone lookup:** skip. Do local format + country-code validation instead (free, private, no quota).

---

## 1. Threat-Intel APIs for Validating User Reports

### 1.1 URL / Domain scanning

#### ✔ Google Safe Browsing Lookup API (v4) — **RECOMMENDED (server-side)**
- **Host:** `POST https://safebrowsing.googleapis.com/v4/threatMatches:find?key=API_KEY`
- **Key:** Yes, free Google Cloud API key. **Cost:** Free; **non-commercial use only** (commercial = paid Web Risk). No cost for the API itself. ✔ (usage-limits page: "There is no cost for use of this API", "non-commercial use only")
- **CORS:** Google APIs send CORS headers, so a browser call technically works, but the key would be embedded in the page (quota theft + ToS grey area) → **use from the Flask server**.
- **Rate limit:** Default quota per project/key (commonly 10,000 lookups/day; viewable/changeable in Cloud console). Up to **500 URLs per request**. ✔
- **Data returned:** list of matching `threatType` (MALWARE, SOCIAL_ENGINEERING/phishing, UNWANTED_SOFTWARE, POTENTIALLY_HARMFUL_APPLICATION) + `cacheDuration`. If no match, empty `{}`. ✔
- **Why:** the single most authoritative free phishing/malware URL check. Zero maintenance, huge coverage.
- ⚠ Must show warning language ("Advisory provided by Google", "Deceptive site ahead" etc.) and never claim 100% certainty — Google's usage guidelines require qualifying language. ✔

#### ✔ VirusTotal API v3 — **RECOMMENDED (server-side only)**
- **Host:** `https://www.virustotal.com/api/v3/urls/{base64url}`, `/ip_addresses/{ip}`, `/domains/{domain}`, `/files/{hash}` + `/urls` (POST to submit new scan). ✔
- **Key:** Yes (free account). **Cost:** Free tier — public API ≈ **4 requests/min, ~500 requests/day** (check your account's quota page) ⚠.
- **CORS:** Response headers are CORS-enabled, so browser calls *work*, but your key is exposed and the 4/min quota makes it useless for a public page → **server-side only**.
- **Data returned:** detection ratio across 70+ AV engines/blocklists for URLs, IPs, domains, hashes; last analysis stats (`harmless/malicious/suspicious` counts). Ideal for showing "9/74 engines flag this URL" — great demo feature.
- **Why:** the richest free multi-engine reputation source. Pairs perfectly with Safe Browsing.

#### ✔ urlscan.io — ⚠ CONDITIONAL (free tier, key, server-side)
- **Host:** `https://urlscan.io/api/v1/scan/` (submit) + `/result/{uuid}` (poll) + `/search/?q=domain:x`.
- **Key:** Yes, free account. Unauthenticated users get only minor quotas. ✔
- **Cost:** Free tier with per-minute/hour/day quotas (see `/user/quotas/`). ✔
- **CORS:** Not advertised; designed for server-side use.
- **Data returned:** full headless-browser scan — verdict, screenshot, DOM, redirects, IPs, hashes. Powerful but **slow (10–30 s)** and quota-hungry → best as an on-demand "deep scan" button in the desktop app, not per-report.
- **Why:** great for screenshots/evidence and "brand" phishing detection (Pro). Overkill for a quick verdict.

#### ✔ URLhaus (abuse.ch) — **RECOMMENDED (server-side, free)**
- **Host:** `https://urlhaus-api.abuse.ch/v1/url/` (POST `url=`) and other bulk-query endpoints. Community API free under fair-use; **commercial use requires paid abuse.ch API**. ✔
- **Key:** Free **Auth-Key** from `auth.abuse.ch` (required for dumps and now recommended for queries). ✔
- **CORS:** No — server-side.
- **Data returned:** whether a URL/domain is currently distributing malware, first/last seen, tags, payload hashes. High signal, very low false-positive (Tranco top-1M excluded). Note: **phishing URLs are intentionally NOT in URLhaus** (they point you to PhishTank/OpenPhish/APWG) — so pair it with a phishing source. ✔

#### ✔ ThreatFox (abuse.ch) — **RECOMMENDED (server-side, free)**
- **Host:** `POST https://threatfox-api.abuse.ch/api/v1/` with `{"query":"search_ioc","search_term":...,"exact_match":true}`. ✔
- **Key:** Free Auth-Key (auth.abuse.ch). **Cost:** free community API. ✔
- **CORS:** No — server-side.
- **Data returned:** IOCs (URLs, domains, IP:port, hashes) tagged with threat type (botnet C&C, payload delivery, phishing, etc.), malware family, confidence level, first/last seen. Complements URLhaus with **phishing and C&C IOCs**. ✔

#### ⚠ OpenPhish Community Feed — **RECOMMENDED (browser-safe, free, list-based)**
- **Host:** `https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt` (plain-text, one URL per line). ✔
- **Key:** None. **Cost:** Free community feed, updated **every 12 h**, **non-commercial** use (premium feeds = paid). ✔
- **CORS:** `raw.githubusercontent.com` sends `Access-Control-Allow-Origin: *` → **fetchable directly from the browser SPA** and cached in localStorage/IndexedDB. ✔
- **Data:** URLs only (no brand/IP/ASN — those are Premium). ✔
- **Why:** the only genuinely browser-callable phishing *list* here. Client-side check: `feed.includes(reportedUrl)` (normalize protocol/host). Note 12 h freshness and URL-only coverage.

#### ✔ PhishTank (Cisco Talos) — ⚠ CONDITIONAL (dataset, not on-demand API)
- **Host:** `https://data.phishtank.com/data/{app_key}/online-valid.json` (+ CSV/XML, hourly refresh). ✔
- **Key:** Free application key (register at `phishtank.org/api_register.php`); without key limited to a few downloads/day. ✔
- **CORS:** Not supported — **server-side download only**.
- **Data:** verified+online phishing URLs with phish_id, submission/verification time, target brand, IP. Community-verified (no false-positive flood), hourly updates. ✔
- **No per-URL lookup API anymore** (the old `checkurl` endpoint is gone) — you download the dump and search it. ✔
- **Why:** best free *verified* phishing dataset; schedule a server-side hourly fetch (desktop app or a cron), or pre-bundle a snapshot in the app.

### 1.2 IP address abuse / geolocation

#### ✔ AbuseIPDB — **RECOMMENDED (server-side only)**
- **Host:** `GET https://api.abuseipdb.com/api/v2/check?ipAddress=...` (+ `reports`, `blacklist`, `report` endpoints). ✔
- **Key:** Yes, free account key. **Cost:** Free tier = **1,000 `check` calls/day**; paid tiers up to 50k/day. ✔
- **CORS:** **Explicitly blocked** — docs: "CORS headers cannot be set… APIv2 keys should be treated as private and are not intended for client side calls." ✔ → **cannot be used from the browser**; perfect for the Flask backend.
- **Data:** `abuseConfidenceScore` (0–100), totalReports, lastReportedAt, usageType (e.g. "Data Center/Web Hosting"), country, ISP, isTor/isWhitelisted, report categories. ✔
- **Why:** the best free "is this IP a known attacker/hosting provider" score — a strong signal for scam reports (e.g. report contains an attacker IP).

#### ✔ ip-api.com (JSON) — ⚠ CONDITIONAL (free, no key, but HTTP-only on free tier)
- **Host:** `http://ip-api.com/json/{ip}`. ✔
- **Key:** **None.** 45 requests/min/IP, **no commercial use**, HTTPS (SSL) requires paid Pro. ✔
- **CORS:** Supports **JSONP callback** and is browser-callable — but the free endpoint is **HTTP only**, so **HTTPS pages (GitHub Pages) block it as mixed content** in the browser. ✔ → use from the Flask server (server→HTTP is fine), or upgrade.
- **Data:** country, city, ISP/org, AS number, `proxy` (VPN/Tor), `hosting`, `mobile` flags — excellent free IP risk signals.

#### ✔ ipinfo.io — ⚠ CONDITIONAL (free tier needs key; CORS-enabled)
- **Host:** `https://ipinfo.io/{ip}?token=...`
- **Key:** Yes (free **Lite** tier — country-level geo, privacy detection; ≈50–100k requests/month, no card). ✔
- **CORS:** Enabled → browser calls work, but the token is exposed in the page (quota abuse risk).
- **Data:** country/city, org/ASN, and Lite privacy detection (VPN/Tor/proxy boolean). ✔
- **Why:** nice, but AbuseIPDB + ip-api cover the same signals for free with less risk. Optional.

#### ⚠ AlienVault OTX — **RECOMMENDED (server-side, free)**
- **Host:** `https://otx.alienvault.com/api/v1/indicators/{type}/{indicator}/general` (type = url/domain/IPv4/hostname/file). Key required (free). Rate limit ~1 req/sec ⚠.
- **Data:** pulses/communities tagging the indicator (malware, phishing, CnC…). Good free multi-source reputation; server-side only (no CORS).

### 1.3 Email / domain reputation

#### ⚠ EmailRep.io (Sublime Security) — ⚠ CONDITIONAL (freemium, server-side)
- **Host:** `https://emailrep.io/{email}`; key optional but limits are very small without/with free key (≈10 req/min, low daily cap; check current docs). CORS appears enabled but the free quota is tiny — **server-side**.
- **Data:** `reputation` (high/low), `suspicious`, `details`: disposable, free_provider, spam, deliverable, valid_mx, spoofable, credentials_leaked, domain_reputation, profiles. Excellent signals for "is this reporter-supplied email a throwaway?" but quota-limited.

#### ✔ HIBP Pwned Passwords — **RECOMMENDED (browser-safe, free, no key)**
- **Host:** `GET https://api.pwnedpasswords.com/range/{first-5-chars-of-SHA1}`. ✔
- **Key:** **None. Free. No rate limit.** CORS: HIBP docs state CORS is supported for non-authenticated APIs → **works from the browser**. ✔
- **Data:** count of times a password hash suffix appears in breach corpus (k-anonymity — you never send the full password). ✔
- **Why:** perfect "check the password the victim used" feature in both the SPA and desktop; privacy-safe; zero cost.

#### ✖ HIBP email breach search (v3) — **NOT SUITABLE (free plan)**
- `GET /breachedAccount/{email}` requires a **paid subscription key**; the free/test key only works on test addresses. CORS explicitly **not** supported for authenticated endpoints ("APIs requiring a key should not be hit directly from the client side"). ✔ → NOT SUITABLE for a free student project. (The free Pwned Passwords API above is the exception.)

### 1.4 Phone number lookup

- **numverify.com** (APILayer): free 250 lookups/month, key, HTTPS; **no CORS**; carrier lookup is paid. ⚠
- **AbstractAPI Phone Validation:** free ~100/month, key, server-side. ⚠
- **Twilio Lookup:** **paid** per lookup (fees per check), requires account/billing. ✖
- **IPQualityScore Phone:** freemium (small monthly free allowance), key, no CORS. ⚠
- **Verdict: NOT SUITABLE for this project.** No good free, CORS-enabled phone API exists. Do **local validation** instead (regex per country, E.164 formatting, MTN/Vodafone/AirtelTigo prefixes for Ghana) — free, private, unlimited.

### 1.5 Browser-safe "free, no key, CORS" bonus APIs (no registration at all)

These are the ideal SPA integrations — no key, no CORS problem, no quota anxiety:

- ✔ **Cloudflare DNS-over-HTTPS:** `GET https://cloudflare-dns.com/dns-query?name=example.com&type=A` (or `type=MX` / `TXT`), header `Accept: application/dns-json`. Free, no key, CORS-enabled, high limits. → check a reported domain *resolves* and whether the email domain has MX records (strong spam/scam signal).
- ✔ **Google DNS-over-HTTPS:** `GET https://dns.google/resolve?name=...&type=...`. Same properties.
- ✔ **RDAP via rdap.org:** `GET https://rdap.org/domain/example.com`. Free, no key, CORS-enabled. Returns registrar + **registration/expiry dates** → "domain registered 3 days ago" is a top phishing indicator.
- ✔ **Pwned Passwords** (see 1.3).

---

## 2. Official Cybercrime Reporting Platforms (for "where to also report" guidance)

All are **web forms / portals / email / hotlines** — **none offer public APIs** for filing reports (that's by design; official intake is human-reviewed). Your app should *link out* to these, which is exactly what your `ReportingChannel` table already does (csa-online-form, mailto, wa.me).

| Platform | Region | How to report | Public API? |
|---|---|---|---|
| **Ghana Cyber Security Authority (CSA)** — `csa.gov.gh` | Ghana 🇬🇭 | Incident/cybercrime reporting portal **`report.csa.gov.gh`**; CSA also operates the national incident-response/CERT-GH channels; check the site for current phone/email (site is JS-heavy — verify directly). | ❌ None |
| **Ghana Police Service — CID Cybercrime Unit** | Ghana 🇬🇭 | Report at police stations / CID headquarters, Accra; dedicated cybercrime unit email/phone published by the Police Service. (Verify current contacts on police.gov.gh — the unit is the formal law-enforcement intake for cybercrime.) | ❌ None |
| **AFRIPOL (INTERPOL's African desk)** | Africa 🌍 | Coordination via national police; no direct public reporting — goes through your country's police/NCB. | ❌ None |
| **INTERPOL Cybercrime** (`interpol.int`) | Global | Reports go to **national police** (INTERPOL doesn't take public complaints); awareness resources free to link. | ❌ None |
| **IC3 — FBI** (`ic3.gov`) | US / global victims | Online complaint form ("File A Complaint"). No API. Note: IC3 is US-jurisdiction; useful for cross-border scams. | ❌ None |
| **Action Fraud → reportfraud.police.uk** | UK | Online form (Action Fraud was folded into the new UK service — `actionfraud.police.uk` now redirects there). | ❌ None |
| **APWG — Anti-Phishing Working Group** (`apwg.org/reportphishing`, `reportphishing.apwg.org`) | Global | Submit phishing emails/URLs for member analysis; **eCrime eXchange (eCX)** data feeds are **member-only**. | ❌ Public none |
| **PhishTank** (`phishtank.org`) | Global | Web form to submit a phish; **data dump API is public/free** (see 1.1). | ✔ Dumps only |
| **OpenPhish** (`openphish.com`) | Global | Web form + free community feed (see 1.1). | ✔ Feed only |
| **URLhaus / ThreatFox (abuse.ch)** | Global | Submit malware URLs / IOCs via free API (see 1.1). | ✔ Free API |
| **Europol EC3** | EU | Reporting through national authorities; EC3 coordinates. | ❌ None |
| **CISA** (`cisa.gov`) | US | Incident reporting forms; ransomware & cyber incidents. | ❌ None |
| **ACSC ReportCyber** (Australia) | AU | Online form. | ❌ None |
| **CAFC / Canadian Anti-Fraud Centre** | CA | Online form / phone. | ❌ None |
| **NITDA / NCC-CSIRT (Nigeria), National KE-CIRT (Kenya), SAPS (SA)** | Africa | National CERTs & police portals — good for regional awareness content. | ❌ None |

> **Best practice for CyberShield Ghana:** on the confirmation page, after a user submits, show "Also report to official channels" with links: **CSA portal**, **Ghana Police CID**, and — for cross-border scams — **IC3 / Interpol guidance**. Keep these as *guidance links*, never file on the user's behalf (no APIs exist, and it would misrepresent the user).

---

## 3. Free Datasets / Feeds (bundle into the app)

| Dataset | Host / URL | Free? | Update | Use |
|---|---|---|---|---|
| PhishTank online-valid | `data.phishtank.com/data/{key}/online-valid.json` | ✔ free key | hourly | verified phishing URLs (server-side download) |
| OpenPhish community | `raw.githubusercontent.com/openphish/public_feed/.../feed.txt` | ✔ | 12 h | phishing URLs, **browser-safe** |
| URLhaus dumps | `urlhaus-api.abuse.ch/v2/files/exports/{key}/...` | ✔ | 5 min | malware URLs/domains |
| ThreatFox exports | `threatfox.abuse.ch/export/#json` | ✔ | — | IOCs (URL/domain/IP/hash) |
| Spamhaus DROP/EDROP | `spamhaus.org/drop/drop.txt` | ✔ | daily | malicious/rogue netblocks (blocklist) ⚠ |
| HIBP Pwned Passwords corpus | downloadable | ✔ | — | offline password checking (optional) |

---

## 4. Recommended Integration Map for CyberShield Ghana

Your app has two runtimes (Flask EXE with Firebase Admin SDK; static GitHub Pages SPA with client SDK). Split integrations accordingly:

**Desktop Flask app (server-side Python, `requests`):**
1. **Google Safe Browsing** — on report submit, check any URL(s) in the report. Show "⚠ This URL is flagged as phishing/malware by Google Safe Browsing" on the review step.
2. **VirusTotal** — enrich the same URL/IP/hash with engine-detection counts (nice demo visual: "9/74 engines flag this").
3. **AbuseIPDB** — score any attacker IP the victim provides.
4. **URLhaus + ThreatFox** — cross-check URL/domain/IP against malware & C&C IOCs.
5. **ip-api.com** — geo/ISP + proxy/hosting flags for IPs (free, no key).
6. **Pwned Passwords** — optional "check if your password was leaked" utility.
7. Cache all responses in Firestore (per-indicator docs) to avoid burning quotas.

**Browser SPA (GitHub Pages, HTTPS, client-side JS):**
1. **DNS-over-HTTPS (Cloudflare/Google)** — verify reported domain resolves; MX records for email-domain checks.
2. **RDAP (rdap.org)** — domain age; flag domains < 30 days old.
3. **Pwned Passwords range API** — breached-password check (no key).
4. **OpenPhish community feed** — fetch + cache client-side, string-match reported URLs.
5. Everything else: either route through a tiny serverless proxy (Cloudflare Worker/Firebase Functions — note: user wants 100% free; a Worker on the free plan can proxy one or two keyed calls like Safe Browsing) or leave to the desktop app.

**Phone numbers:** local validation only (regex + Ghanaian prefixes). Do not spend quota on phone APIs.

---

## 5. Final Recommendation Table

| # | Service | Type | Free? | Key? | Browser (CORS) | Rate limit | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Google Safe Browsing Lookup | URL check | ✔ non-commercial | ✔ | ⚠ works but key exposed | ~10k/day default | ✅ **RECOMMENDED** (server) |
| 2 | VirusTotal v3 | URL/IP/hash rep | ✔ | ✔ | ⚠ works but key exposed | 4/min, ~500/day | ✅ **RECOMMENDED** (server) |
| 3 | AbuseIPDB | IP abuse score | ✔ | ✔ | ❌ explicitly blocked | 1,000 checks/day | ✅ **RECOMMENDED** (server) |
| 4 | URLhaus (abuse.ch) | malware URL DB | ✔ | ✔ free | ❌ | fair use | ✅ **RECOMMENDED** (server) |
| 5 | ThreatFox (abuse.ch) | IOC DB | ✔ | ✔ free | ❌ | fair use | ✅ **RECOMMENDED** (server) |
| 6 | AlienVault OTX | multi-source rep | ✔ | ✔ | ❌ | ~1 req/s | ✅ **RECOMMENDED** (server, optional) |
| 7 | ip-api.com | IP geo/proxy | ✔ | none | ⚠ HTTP-only (mixed content) | 45/min | ✅ server; ❌ browser HTTPS |
| 8 | OpenPhish community feed | phishing list | ✔ non-commercial | none | ✅ | n/a | ✅ **RECOMMENDED** (browser cache) |
| 9 | Cloudflare/Google DNS-over-HTTPS | DNS/MX lookup | ✔ | none | ✅ | high | ✅ **RECOMMENDED** (browser) |
| 10 | RDAP (rdap.org) | domain age/whois | ✔ | none | ✅ | generous | ✅ **RECOMMENDED** (browser) |
| 11 | HIBP Pwned Passwords | password breach | ✔ | none | ✅ | none | ✅ **RECOMMENDED** (both) |
| 12 | PhishTank dumps | verified phish list | ✔ | ✔ free | ❌ | few/day no key | ✅ server-side only |
| 13 | urlscan.io | full URL scan | ✔ | ✔ | ⚠ | per-min/hour/day | ⚠ CONDITIONAL (deep scan button) |
| 14 | ipinfo.io | IP geo/privacy | ✔ Lite | ✔ | ✅ | ~50–100k/mo | ⚠ CONDITIONAL (key exposed) |
| 15 | EmailRep.io | email rep | ✔ tiny | ✔ | ⚠ | ~250/mo | ⚠ CONDITIONAL (server) |
| 16 | HIBP email search | breach search | ❌ paid | ✔ | ❌ | paid tiers | ❌ **NOT SUITABLE** |
| 17 | numverify / AbstractAPI / Twilio / IPQS phone | phone lookup | ❌ freemium/paid | ✔ | ❌ | tiny | ❌ **NOT SUITABLE** — validate locally |
| 18 | CSA / Police / IC3 / AFRIPOL / Interpol / APWG / Europol | official reporting | n/a | n/a | web form | n/a | ✅ as **link-out guidance only** |

---

## 5. What Was Implemented (2026-08-02)

| # | Integration | Where | Status |
|---|---|---|---|
| 1 | **Security Check card on the desktop review step** — button calls `/report/security-check`, scans description + metadata for URLs/IPs, checks them via free sources, shows a colour-coded table with a disclaimer | `services/threat_intel.py`, `routes/report.py`, `templates/report/step_review.html` | ✅ Done & verified |
| 2 | **ip-api.com (keyless)** — IP geolocation/ISP lookup | `threat_intel.check_ip_ipapi` | ✅ Done (HTTP-only on free tier — handled) |
| 3 | **URLhaus (optional `URLHAUS_KEY`)** — malware URL check; skipped gracefully when no key | `threat_intel.check_url_urlhaus` | ✅ Done (abuse.ch now requires a free auth key; 401 otherwise) |
| 4 | **Google Safe Browsing (optional `GOOGLE_SAFE_BROWSING_KEY`)** | `threat_intel.check_url_safe_browsing` | ✅ Done (no-op without key) |
| 5 | **AbuseIPDB (optional `ABUSEIPDB_KEY`)** — IP abuse score | `threat_intel.check_ip_abuseipdb` | ✅ Done (no-op without key) |
| 6 | **SSL fallback** — unverified TLS retry so PyInstaller EXEs without a CA bundle still work | `threat_intel._http_json` | ✅ Done & verified |
| 7 | **Client-side URL checks in the web wizard** (step 3) — DNS-over-HTTPS (domain resolves? MX exists?) + RDAP (domain age < 30 days = scam signal), debounced as you type | `docs/report.html` | ✅ Done, no keys needed |
| 8 | **"Also report to official channels" card** — CSA portal, Ghana Police CID, IC3 links | web detail view (`docs/reports.html`) + desktop confirmation page (`templates/report/confirmation.html`) | ✅ Done |
| 9 | **Pwned Passwords (HIBP range API, no key)** — live "has this password been breached?" check under the password field on registration | web (`docs/register.html`) + desktop (`templates/auth/register.html`) + server helper `threat_intel.check_password_pwned()` | ✅ Done & verified |

**To enable the optional desktop checks**, set these env vars before starting the app (all free):
```
GOOGLE_SAFE_BROWSING_KEY=...   # console.cloud.google.com -> Safe Browsing API
ABUSEIPDB_KEY=...              # abuseipdb.com free account
URLHAUS_KEY=...                # urlhaus.abuse.ch free account (API section)
```
Without any keys, the desktop still runs the keyless ip-api.com IP lookup; the web runs the keyless DoH + RDAP checks.

---

## 6. Sources (verified this session)

- Google Safe Browsing Lookup API & usage limits — developers.google.com/safe-browsing/v4/lookup-api, /usage-limits
- VirusTotal API v3 overview + URL report reference — docs.virustotal.com, virustotal.readme.io
- urlscan.io API v1 — urlscan.io/docs/api/
- URLhaus, MalwareBazaar, ThreatFox community APIs — urlhaus.abuse.ch/api, bazaar.abuse.ch/api, threatfox.abuse.ch/api
- OpenPhish feeds — openphish.com/phishing_feeds.html
- PhishTank developer info — phishtank.org/developer_info.php
- AbuseIPDB docs — docs.abuseipdb.com (incl. CORS + daily limits)
- ip-api.com JSON docs — ip-api.com/docs/api:json
- ipinfo.io pricing — ipinfo.io/pricing
- Have I Been Pwned API v3 — haveibeenpwned.com/API/v3 (CORS + rate limits)
- emailrep.io — emailrep.io
- IC3 — ic3.gov; Action Fraud → reportfraud.police.uk; Interpol — interpol.int; APWG — apwg.org; CSA Ghana — csa.gov.gh (JS-heavy; verify portal contacts directly)
