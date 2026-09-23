"""
ReconX – Technology Detection Tab
"""

import threading
import customtkinter as ctk
from gui.theme import *
from gui.components import SearchBar, ResultsPanel, SectionLabel, InfoCard
from modules.tech_detector import detect_technologies
from utils.report_generator import save_json_report, generate_html_report
from utils.logger import get_logger

logger = get_logger("tech_tab")

CATEGORY_ICONS = {
    "CMS": "🗂", "JavaScript Framework": "⚡", "Web Server": "🖥",
    "Backend / Language": "🔧", "Analytics": "📊", "CDN / Cloud": "☁",
    "Security": "🛡", "UI Framework": "🎨", "E-commerce": "🛒",
}


class TechTab(ctk.CTkFrame):
    def __init__(self, parent, status_bar, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.status_bar = status_bar
        self._last_results = None
        self._target = ""
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_XL, pady=(PAD_XL, PAD_MD))
        ctk.CTkLabel(header, text="⚙  TECHNOLOGY DETECTION",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="9 CATEGORIES • 60+ SIGNATURES",
                     font=ctk.CTkFont("Consolas", 10, "bold"),
                     text_color=ACCENT_CYAN, fg_color=BG_INPUT,
                     corner_radius=4, width=190, height=22).pack(side="right")

        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.search_bar = SearchBar(sf,
            placeholder="Enter target URL or domain (e.g. github.com)",
            button_text="⚡ Fingerprint",
            on_search=self._start_scan)
        self.search_bar.pack(fill="x")

        sr = ctk.CTkFrame(self, fg_color="transparent")
        sr.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.card_total  = InfoCard(sr, "DETECTED",    "—", accent=True)
        self.card_status = InfoCard(sr, "HTTP STATUS", "—")
        self.card_server = InfoCard(sr, "SERVER",      "—")
        self.card_url    = InfoCard(sr, "URL SCANNED", "—")
        for c in (self.card_total, self.card_status, self.card_server, self.card_url):
            c.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_MD))
        split.columnconfigure(0, weight=3)
        split.columnconfigure(1, weight=2)
        split.rowconfigure(0, weight=1)

        rf = ctk.CTkFrame(split, fg_color="transparent")
        rf.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))
        SectionLabel(rf, "■ DETECTION RESULTS").pack(anchor="w", pady=(0, PAD_XS))
        self.results_panel = ResultsPanel(rf)
        self.results_panel.pack(fill="both", expand=True)

        cf = ctk.CTkFrame(split, fg_color="transparent")
        cf.grid(row=0, column=1, sticky="nsew")
        SectionLabel(cf, "■ TECH STACK").pack(anchor="w", pady=(0, PAD_XS))
        self.tech_scroll = ctk.CTkScrollableFrame(cf,
            fg_color=BG_PANEL, border_color=BORDER_COLOR,
            border_width=1, corner_radius=CORNER_RADIUS)
        self.tech_scroll.pack(fill="both", expand=True)
        ctk.CTkLabel(self.tech_scroll,
                     text="Run a scan to see\ndetected technologies.",
                     font=ctk.CTkFont("Consolas", 11), text_color=TEXT_DIM
                     ).pack(pady=PAD_XL)

        er = ctk.CTkFrame(self, fg_color="transparent")
        er.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        ctk.CTkButton(er, text="💾 Export JSON",
                      font=ctk.CTkFont("Segoe UI", 11),
                      fg_color=BG_INPUT, hover_color=BG_HOVER,
                      text_color=TEXT_SECONDARY,
                      corner_radius=BUTTON_RADIUS, height=34, width=130,
                      command=self._export_json).pack(side="left", padx=(0, PAD_SM))
        ctk.CTkButton(er, text="📄 Export HTML Report",
                      font=ctk.CTkFont("Segoe UI", 11),
                      fg_color=BG_INPUT, hover_color=BG_HOVER,
                      text_color=TEXT_SECONDARY,
                      corner_radius=BUTTON_RADIUS, height=34, width=160,
                      command=self._export_html).pack(side="left")

    def _start_scan(self):
        domain = self.search_bar.get_value()
        if not domain:
            self.results_panel.set_text("⚠  Please enter a domain.")
            return
        self._target = domain
        self._last_results = None
        self.search_bar.set_state("disabled")
        self.status_bar.set_scanning(domain)
        self.results_panel.clear()
        threading.Thread(target=self._run, args=(domain,), daemon=True).start()

    def _run(self, domain):
        try:
            results = detect_technologies(domain)
            self._last_results = results
            self.after(0, self._display_results, results)
        except Exception as e:
            logger.error(f"Tech detection error: {e}", exc_info=True)
            self.after(0, self._on_error, str(e))

    def _display_results(self, r):
        detected = r.get("detected", {})
        headers  = r.get("headers_collected", {})
        lines = [
            "━" * 60,
            "  ReconX Technology Detection Report",
            f"  Target     : {r['domain']}",
            f"  URL Scanned: {r.get('url_scanned','N/A')}",
            f"  HTTP Status: {r.get('http_status','N/A')}",
            f"  Total Found: {r['total_detected']}",
            "━" * 60, "",
        ]
        if r.get("error"):
            lines.append(f"  ⚠ {r['error']}")
        else:
            for cat, techs in detected.items():
                icon = CATEGORY_ICONS.get(cat, "▸")
                lines.append(f"  {icon}  {cat.upper()}")
                for t in techs:
                    lines.append(f"      ✓ {t}")
                lines.append("")
            if not detected:
                lines.append("  No technologies detected. WAF may be blocking fingerprinting.")
            lines.append("  ── HTTP HEADERS ─────────────────────────────────────────")
            for k, v in headers.items():
                lines.append(f"  {k:<34}: {v[:60]}")
        lines.append("\n" + "━" * 60)
        self.results_panel.set_text("\n".join(lines))

        self._populate_tech_panel(detected)
        self.card_total.set_value(str(r["total_detected"]))
        self.card_status.set_value(str(r.get("http_status","—")))
        self.card_server.set_value(headers.get("Server", headers.get("server","—"))[:22])
        self.card_url.set_value(r.get("url_scanned","—")[:28])
        self.search_bar.set_state("normal")
        self.status_bar.set_ready(f"Detected {r['total_detected']} technologies")

    def _populate_tech_panel(self, detected):
        for w in self.tech_scroll.winfo_children():
            w.destroy()
        if not detected:
            ctk.CTkLabel(self.tech_scroll, text="No technologies detected.",
                         font=ctk.CTkFont("Consolas", 11),
                         text_color=TEXT_DIM).pack(pady=PAD_XL)
            return
        colors = [ACCENT_CYAN, ACCENT_BLUE, ACCENT_PURPLE, SUCCESS,
                  WARNING, "#ec4899", "#f97316", "#06b6d4", "#84cc16"]
        for idx, (cat, techs) in enumerate(detected.items()):
            color = colors[idx % len(colors)]
            icon = CATEGORY_ICONS.get(cat, "▸")
            ctk.CTkLabel(self.tech_scroll,
                         text=f"{icon} {cat}",
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=color, fg_color=BG_INPUT,
                         corner_radius=4).pack(fill="x", padx=PAD_SM,
                                               pady=(PAD_SM, 2))
            for tech in techs:
                row = ctk.CTkFrame(self.tech_scroll, fg_color="transparent")
                row.pack(fill="x", padx=PAD_SM, pady=1)
                ctk.CTkLabel(row, text="  ✓",
                             font=ctk.CTkFont("Consolas", 10),
                             text_color=SUCCESS, width=24).pack(side="left")
                ctk.CTkLabel(row, text=tech,
                             font=ctk.CTkFont("Segoe UI", 11),
                             text_color=TEXT_PRIMARY,
                             anchor="w").pack(side="left")

    def _on_error(self, err):
        self.results_panel.set_text(f"✗  Detection failed:\n\n{err}")
        self.search_bar.set_state("normal")
        self.status_bar.set_error("Detection failed")

    def _export_json(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first."); return
        path = save_json_report(self._last_results, "tech", self._target)
        self.results_panel.append_text(f"\n\n✓  JSON saved → {path}")

    def _export_html(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first."); return
        path = generate_html_report(self._last_results, "tech", self._target)
        self.results_panel.append_text(f"\n\n✓  HTML report saved → {path}")
