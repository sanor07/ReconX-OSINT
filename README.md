# ReconX v2.0 — OSINT Intelligence Framework

```
██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗██╗  ██╗  v2.0
██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║╚██╗██╔╝
██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║ ╚███╔╝
██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║ ██╔██╗
██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║██╔╝ ██╗
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
```

> ⚠️ **For educational and authorized use only.**

---

## What's New in v2.0

| Feature | Description |
|---|---|
| 🔎 **Subdomain Finder** | DNS brute-force (200-word list) + crt.sh CT logs + HackerTarget API with live feed |
| ⚙ **Tech Detector** | 80+ signatures across 7 categories: CMS, JS frameworks, CDN, analytics, security, e-commerce |
| 📞 **Phone Intelligence** | Full ITU validation, carrier, geolocation, timezone via `phonenumbers` library |
| 🕵 **Breach Intelligence** | Multi-source: HIBP, LeakCheck, psbdmp paste search + 30-entry breach reference DB |
| 🕸 **Graph Visualizer** | Interactive force-directed node graph — drag, zoom, click-to-inspect, auto-layout |
| 📄 **PDF Reports** | Professional dark-themed PDF export via ReportLab for all scan types |

---

## Full Feature Set (v1 + v2)

| Module | Capabilities |
|---|---|
| 👤 Username | 35+ platforms concurrent (GitHub, Reddit, TikTok, Steam…) |
| ✉ Email | Format, MX, SPF/DKIM, provider detection, risk scoring |
| 🌐 Domain | WHOIS, full DNS, HTTP headers, hosting geo, common subdomains |
| 🔍 IP | Geolocation, ISP, ASN, reverse DNS, Google Maps link |
| 🔎 Subdomains | DNS brute-force + CT transparency + HackerTarget, live feed |
| ⚙ Tech Detect | 80+ tech signatures, security posture scoring |
| 📞 Phone | E.164/international/national formats, carrier, region, VOIP flag |
| 🕵 Breach | HIBP, LeakCheck, paste search, 30-record breach reference |
| 🖼 Metadata | Full EXIF, GPS decimal coords, camera fingerprint |
| 🕸 Graph | Force-directed visualization, drag/zoom/inspect, demo graph |
| 📄 Reports | JSON + HTML + PDF export for every module |

---

## Project Structure

```
reconx/
├── main.py
├── requirements.txt
├── README.md
│
├── gui/
│   ├── dashboard.py          # Main window — grouped sidebar, 10 tabs
│   ├── theme.py              # Color palette & font constants
│   ├── components.py         # Shared widgets: SearchBar, ResultsPanel, StatusBar
│   ├── username_tab.py
│   ├── email_tab.py
│   ├── domain_tab.py
│   ├── ip_tab.py
│   ├── subdomain_tab.py      # NEW v2
│   ├── tech_tab.py           # NEW v2
│   ├── phone_tab.py          # NEW v2
│   ├── breach_tab.py         # NEW v2
│   ├── metadata_tab.py
│   └── graph_tab.py          # NEW v2 — tkinter Canvas force-directed graph
│
├── modules/
│   ├── username_search.py
│   ├── email_lookup.py
│   ├── domain_lookup.py
│   ├── ip_lookup.py
│   ├── subdomain_finder.py   # NEW v2 — crt.sh + HackerTarget + DNS BF
│   ├── tech_detector.py      # NEW v2 — 80+ regex/header signatures
│   ├── phone_lookup.py       # NEW v2 — phonenumbers + carrier/geo
│   ├── breach_checker.py     # NEW v2 — HIBP + LeakCheck + psbdmp
│   └── metadata_extractor.py
│
└── utils/
    ├── logger.py
    ├── api_clients.py
    └── report_generator.py   # UPDATED — JSON + HTML + PDF (ReportLab)
```

---

## Installation

```bash
# 1. Unzip
unzip reconx_v2_osint_framework.zip && cd reconx

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Launch
python main.py
```

### Dependencies

| Package | Purpose |
|---|---|
| `customtkinter` | Modern dark-theme GUI |
| `Pillow` | Image EXIF extraction |
| `requests` | HTTP client |
| `dnspython` | DNS record lookups |
| `python-whois` | WHOIS queries |
| `phonenumbers` | Phone number parsing & enrichment |
| `reportlab` | PDF report generation |

---

## Graph Visualizer — Controls

| Action | Effect |
|---|---|
| **Click** node | Select — inspect metadata in detail panel |
| **Drag** node | Reposition (auto-pins the node) |
| **Scroll** | Zoom in / out |
| **＋ Add Node** | Add a custom node (any type) |
| **⟳ Re-layout** | Restart force-directed simulation |
| **◉ Demo** | Load the built-in demo graph |
| **🗑 Clear** | Wipe the graph |

---

## PDF Export

Every module has a **📄 Export PDF** button. Reports feature:
- Dark-themed pages (ReportLab `onPage` background painter)
- ReconX cyan accent header bar
- Meta block: target, scan type, timestamp
- Two-column data table with alternating row colours
- Legal/disclaimer footer

---

## Ethical Use

ReconX is designed for **authorized** security research, bug bounty recon (in scope), and educational OSINT study. Never use it to stalk, harass, or investigate targets without permission.
