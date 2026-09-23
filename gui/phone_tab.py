"""
ReconX – Phone Number Intelligence Tab
"""

import threading
import customtkinter as ctk
from gui.theme import *
from gui.components import SearchBar, ResultsPanel, SectionLabel, InfoCard
from modules.phone_lookup import analyze_phone
from utils.report_generator import save_json_report, generate_html_report
from utils.logger import get_logger

logger = get_logger("phone_tab")


class PhoneTab(ctk.CTkFrame):
    def __init__(self, parent, status_bar, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.status_bar = status_bar
        self._last_results = None
        self._target = ""
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_XL, pady=(PAD_XL, PAD_MD))
        ctk.CTkLabel(header, text="📞  PHONE NUMBER INTELLIGENCE",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")

        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.search_bar = SearchBar(sf,
            placeholder="Enter phone number (e.g. +1-555-867-5309 or +917890123456)",
            button_text="⚡ Analyze",
            on_search=self._start_scan)
        self.search_bar.pack(fill="x")

        # Format hint bar
        hint = ctk.CTkFrame(self, fg_color=BG_PANEL,
                            border_color=BORDER_COLOR, border_width=1,
                            corner_radius=CORNER_RADIUS, height=40)
        hint.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        hint.pack_propagate(False)
        ctk.CTkLabel(hint,
            text="Accepted formats:  +1 555 867 5309   •   +44 20 7946 0958   "
                 "•   +91 98765 43210   •   001-800-555-0199",
            font=ctk.CTkFont("Consolas", 10), text_color=TEXT_DIM
        ).pack(expand=True)

        sr = ctk.CTkFrame(self, fg_color="transparent")
        sr.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.card_valid   = InfoCard(sr, "VALID",      "—", accent=True)
        self.card_country = InfoCard(sr, "COUNTRY",    "—")
        self.card_type    = InfoCard(sr, "LINE TYPE",  "—")
        self.card_carrier = InfoCard(sr, "CARRIER",    "—")
        for c in (self.card_valid, self.card_country, self.card_type, self.card_carrier):
            c.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_MD))
        split.columnconfigure(0, weight=3)
        split.columnconfigure(1, weight=2)
        split.rowconfigure(0, weight=1)

        rf = ctk.CTkFrame(split, fg_color="transparent")
        rf.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))
        SectionLabel(rf, "■ ANALYSIS RESULTS").pack(anchor="w", pady=(0, PAD_XS))
        self.results_panel = ResultsPanel(rf)
        self.results_panel.pack(fill="both", expand=True)

        # OSINT links panel
        lf = ctk.CTkFrame(split, fg_color="transparent")
        lf.grid(row=0, column=1, sticky="nsew")
        SectionLabel(lf, "■ OSINT RESOURCES").pack(anchor="w", pady=(0, PAD_XS))
        self.links_frame = ctk.CTkScrollableFrame(lf,
            fg_color=BG_PANEL, border_color=BORDER_COLOR,
            border_width=1, corner_radius=CORNER_RADIUS)
        self.links_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.links_frame,
                     text="Run a scan to see\nOSINT resource links.",
                     font=ctk.CTkFont("Consolas", 11),
                     text_color=TEXT_DIM).pack(pady=PAD_XL)

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
        number = self.search_bar.get_value()
        if not number:
            self.results_panel.set_text("⚠  Please enter a phone number.")
            return
        self._target = number
        self._last_results = None
        self.search_bar.set_state("disabled")
        self.status_bar.set_scanning(number)
        self.results_panel.clear()
        threading.Thread(target=self._run, args=(number,), daemon=True).start()

    def _run(self, number):
        try:
            results = analyze_phone(number)
            self._last_results = results
            self.after(0, self._display_results, results)
        except Exception as e:
            logger.error(f"Phone analysis error: {e}", exc_info=True)
            self.after(0, self._on_error, str(e))

    def _display_results(self, r):
        lines = [
            "━" * 60,
            "  ReconX Phone Number Intelligence",
            f"  Input     : {r['raw_input']}",
            "━" * 60, "",
            "  ── VALIDATION ──────────────────────────────────────────",
            f"  Valid             : {'✓ Yes' if r.get('valid') else '✗ No'}",
            f"  E.164 Format      : {r.get('formatted_e164','N/A')}",
            f"  National Format   : {r.get('formatted_national','N/A')}",
            f"  International     : {r.get('formatted_international','N/A')}",
            "",
            "  ── LOCATION & CARRIER ───────────────────────────────────",
            f"  Country Code      : +{r.get('country_code','?')}",
            f"  Country           : {r.get('country','Unknown')}",
            f"  Region            : {r.get('region','Unknown')}",
            f"  Carrier           : {r.get('carrier','Unknown')}",
            f"  Line Type         : {r.get('line_type','Unknown')}",
            "",
            "  ── TIMEZONE ─────────────────────────────────────────────",
        ]
        tzs = r.get("time_zones", [])
        if tzs:
            for tz in tzs:
                lines.append(f"  {tz}")
        else:
            lines.append("  Unknown")

        lines += ["", "  ── RISK INDICATORS ──────────────────────────────────────"]
        for note in r.get("risk_notes", []):
            lines.append(f"  {note}")

        lines += ["", "  ── OSINT RESOURCE LINKS ─────────────────────────────────"]
        for link in r.get("osint_links", []):
            lines.append(f"  {link}")

        lines.append("\n" + "━" * 60)
        self.results_panel.set_text("\n".join(lines))
        self._populate_links_panel(r.get("osint_links", []))

        self.card_valid.set_value("✓ Valid" if r.get("valid") else "✗ Invalid")
        self.card_country.set_value(r.get("country","—")[:22])
        self.card_type.set_value(r.get("line_type","—")[:18])
        self.card_carrier.set_value(r.get("carrier","—")[:18])

        self.search_bar.set_state("normal")
        self.status_bar.set_ready("Phone analysis complete")

    def _populate_links_panel(self, links):
        for w in self.links_frame.winfo_children():
            w.destroy()
        if not links:
            ctk.CTkLabel(self.links_frame, text="No links available.",
                         font=ctk.CTkFont("Consolas", 11),
                         text_color=TEXT_DIM).pack(pady=PAD_XL)
            return
        ctk.CTkLabel(self.links_frame,
                     text="Open these in your browser\nfor deeper OSINT research:",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=TEXT_SECONDARY).pack(padx=PAD_SM, pady=PAD_SM)
        for link in links:
            site = link.split("/")[2] if "//" in link else link
            def open_link(url=link):
                import webbrowser; webbrowser.open(url)
            ctk.CTkButton(self.links_frame, text=f"🔗 {site}",
                          font=ctk.CTkFont("Segoe UI", 11),
                          fg_color=BG_INPUT, hover_color=BG_HOVER,
                          text_color=ACCENT_CYAN,
                          corner_radius=BUTTON_RADIUS, height=32,
                          anchor="w", command=open_link
                          ).pack(fill="x", padx=PAD_SM, pady=2)

    def _on_error(self, err):
        self.results_panel.set_text(f"✗  Analysis failed:\n\n{err}")
        self.search_bar.set_state("normal")
        self.status_bar.set_error("Analysis failed")

    def _export_json(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first."); return
        path = save_json_report(self._last_results, "phone", self._target)
        self.results_panel.append_text(f"\n\n✓  JSON saved → {path}")

    def _export_html(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first."); return
        path = generate_html_report(self._last_results, "phone", self._target)
        self.results_panel.append_text(f"\n\n✓  HTML report saved → {path}")
