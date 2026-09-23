"""
ReconX – Email Intelligence Tab
"""

import threading
import customtkinter as ctk
from gui.theme import *
from gui.components import SearchBar, ResultsPanel, SectionLabel, InfoCard
from modules.email_lookup import analyze_email
from utils.report_generator import save_json_report, generate_html_report
from utils.logger import get_logger

logger = get_logger("email_tab")


class EmailTab(ctk.CTkFrame):
    def __init__(self, parent, status_bar, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.status_bar = status_bar
        self._last_results = None
        self._target = ""
        self._build()

    def _build(self):
        # Title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_XL, pady=(PAD_XL, PAD_MD))
        ctk.CTkLabel(
            header, text="✉  EMAIL INTELLIGENCE",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.search_bar = SearchBar(
            search_frame,
            placeholder="Enter email address (e.g. user@example.com)",
            button_text="⚡ Analyze",
            on_search=self._start_scan,
        )
        self.search_bar.pack(fill="x")

        # Info cards
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.card_valid   = InfoCard(stats_row, "FORMAT",    "—")
        self.card_mx      = InfoCard(stats_row, "MX RECORD", "—", accent=True)
        self.card_disp    = InfoCard(stats_row, "DISPOSABLE","—")
        self.card_prov    = InfoCard(stats_row, "PROVIDER",  "—")
        for c in (self.card_valid, self.card_mx, self.card_disp, self.card_prov):
            c.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

        # Results panel
        res_frame = ctk.CTkFrame(self, fg_color="transparent")
        res_frame.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_MD))
        SectionLabel(res_frame, "■ ANALYSIS RESULTS").pack(anchor="w", pady=(0, PAD_XS))
        self.results_panel = ResultsPanel(res_frame)
        self.results_panel.pack(fill="both", expand=True)

        # Export buttons
        export_row = ctk.CTkFrame(self, fg_color="transparent")
        export_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        ctk.CTkButton(
            export_row, text="💾 Export JSON",
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color="transparent", hover_color=BG_HOVER, text_color=NEON_CYAN, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=BUTTON_RADIUS, height=34, width=130,
            command=self._export_json
        ).pack(side="left", padx=(0, PAD_SM))
        ctk.CTkButton(
            export_row, text="📄 Export HTML Report",
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color="transparent", hover_color=BG_HOVER, text_color=NEON_CYAN, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=BUTTON_RADIUS, height=34, width=160,
            command=self._export_html
        ).pack(side="left")

    def _start_scan(self):
        email = self.search_bar.get_value()
        if not email:
            self.results_panel.set_text("⚠  Please enter an email address.")
            return
        self._target = email
        self._last_results = None
        self.search_bar.set_state("disabled")
        self.status_bar.set_scanning(email)
        self.results_panel.clear()
        threading.Thread(target=self._run, args=(email,), daemon=True).start()

    def _run(self, email: str):
        try:
            results = analyze_email(email)
            self._last_results = results
            self.after(0, self._display_results, results)
        except Exception as e:
            logger.error(f"Email analysis error: {e}", exc_info=True)
            self.after(0, self._on_error, str(e))

    def _display_results(self, r: dict):
        val = r.get("validation", {})
        lines = [
            "━" * 60,
            "  ReconX Email Intelligence Report",
            f"  Target    : {r['email']}",
            "━" * 60,
            "",
            "  ── VALIDATION ──────────────────────────────────────────",
            f"  Format Valid  : {'✓ Yes' if val.get('format_valid') else '✗ No'}",
            f"  Domain        : {val.get('domain', 'N/A')}",
            f"  MX Records    : {'✓ Found' if val.get('mx_found') else '✗ Not Found'}",
            f"  Disposable    : {'⚠ Yes — suspicious!' if val.get('is_disposable') else '✓ No'}",
            "",
            "  ── PROVIDER ─────────────────────────────────────────────",
            f"  Email Provider: {r.get('provider_guess', 'Unknown')}",
            "",
            "  ── MX RECORDS ───────────────────────────────────────────",
        ]
        mx = r.get("mx_records", [])
        if mx:
            for rec in mx:
                lines.append(f"  • {rec}")
        else:
            lines.append("  No MX records found.")

        lines += [
            "",
            "  ── DNS TXT (SPF / DMARC hints) ──────────────────────────",
        ]
        txt = r.get("dns_txt_records", [])
        for t in txt[:8]:
            lines.append(f"  • {t[:100]}")
        if not txt:
            lines.append("  No TXT records found.")

        lines += [
            "",
            "  ── DOMAIN INFO ──────────────────────────────────────────",
            f"  Resolved IP   : {r.get('domain_info', {}).get('resolved_ip', 'N/A')}",
            "",
            "  ── RISK INDICATORS ──────────────────────────────────────",
        ]
        for ri in r.get("risk_indicators", []):
            lines.append(f"  {ri}")
        if not r.get("risk_indicators"):
            lines.append("  ✓ No risk indicators found.")

        lines += [
            "",
            "  ── BREACH CHECK ─────────────────────────────────────────",
            f"  ℹ {r.get('breach_check_note', '')}",
            "",
            "━" * 60,
        ]
        self.results_panel.set_text("\n".join(lines))

        # Update info cards
        self.card_valid.set_value("✓ Valid" if val.get("format_valid") else "✗ Invalid")
        self.card_mx.set_value("✓ Found" if val.get("mx_found") else "✗ None")
        self.card_disp.set_value("⚠ Yes" if val.get("is_disposable") else "✓ No")
        self.card_prov.set_value(r.get("provider_guess", "Unknown")[:20])

        self.search_bar.set_state("normal")
        self.status_bar.set_ready("Email analysis complete")

    def _on_error(self, err: str):
        self.results_panel.set_text(f"✗  Analysis failed:\n\n{err}")
        self.search_bar.set_state("normal")
        self.status_bar.set_error("Analysis failed")

    def _export_json(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first.")
            return
        path = save_json_report(self._last_results, "email", self._target)
        self.results_panel.append_text(f"\n\n✓  JSON saved → {path}")

    def _export_html(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first.")
            return
        path = generate_html_report(self._last_results, "email", self._target)
        self.results_panel.append_text(f"\n\n✓  HTML report saved → {path}")
