"""
ReconX – IP Intelligence Tab
"""

import threading
import customtkinter as ctk
from gui.theme import *
from gui.components import SearchBar, ResultsPanel, SectionLabel, InfoCard
from modules.ip_lookup import analyze_ip
from utils.report_generator import save_json_report, generate_html_report
from utils.logger import get_logger

logger = get_logger("ip_tab")


class IPTab(ctk.CTkFrame):
    def __init__(self, parent, status_bar, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.status_bar = status_bar
        self._last_results = None
        self._target = ""
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_XL, pady=(PAD_XL, PAD_MD))
        ctk.CTkLabel(
            header, text="🔍  IP INTELLIGENCE",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.search_bar = SearchBar(
            search_frame,
            placeholder="Enter IP address (e.g. 8.8.8.8 or 2001:4860:4860::8888)",
            button_text="⚡ Trace IP",
            on_search=self._start_scan,
        )
        self.search_bar.pack(fill="x")

        # Info cards
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.card_country = InfoCard(stats_row, "COUNTRY",  "—", accent=True)
        self.card_isp     = InfoCard(stats_row, "ISP",      "—")
        self.card_city    = InfoCard(stats_row, "CITY",     "—")
        self.card_asn     = InfoCard(stats_row, "ASN",      "—")
        for c in (self.card_country, self.card_isp, self.card_city, self.card_asn):
            c.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

        # Results panel
        res_frame = ctk.CTkFrame(self, fg_color="transparent")
        res_frame.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_MD))
        SectionLabel(res_frame, "■ IP ANALYSIS").pack(anchor="w", pady=(0, PAD_XS))
        self.results_panel = ResultsPanel(res_frame)
        self.results_panel.pack(fill="both", expand=True)

        # Export
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

        # Google Maps hint button
        self._map_btn = ctk.CTkButton(
            export_row, text="🗺 View on Map",
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color="transparent", hover_color=BG_HOVER, text_color=NEON_CYAN, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=BUTTON_RADIUS, height=34, width=130,
            command=self._open_map, state="disabled"
        )
        self._map_btn.pack(side="left", padx=(PAD_SM, 0))

    def _start_scan(self):
        ip = self.search_bar.get_value()
        if not ip:
            self.results_panel.set_text("⚠  Please enter an IP address.")
            return
        self._target = ip
        self._last_results = None
        self._map_url = ""
        self.search_bar.set_state("disabled")
        self._map_btn.configure(state="disabled")
        self.status_bar.set_scanning(ip)
        self.results_panel.clear()
        threading.Thread(target=self._run, args=(ip,), daemon=True).start()

    def _run(self, ip: str):
        try:
            results = analyze_ip(ip)
            self._last_results = results
            self.after(0, self._display_results, results)
        except Exception as e:
            logger.error(f"IP analysis error: {e}", exc_info=True)
            self.after(0, self._on_error, str(e))

    def _display_results(self, r: dict):
        geo = r.get("geolocation", {})
        net = r.get("network", {})

        self._map_url = r.get("map_url", "")

        lines = [
            "━" * 60,
            "  ReconX IP Intelligence Report",
            f"  Target IP : {r['ip']}",
            "━" * 60,
            "",
            "  ── GEOLOCATION ──────────────────────────────────────────",
            f"  Country       : {geo.get('country', 'N/A')} ({geo.get('country_code', '')})",
            f"  Region        : {geo.get('region', 'N/A')}",
            f"  City          : {geo.get('city', 'N/A')}",
            f"  ZIP / Postal  : {geo.get('zip', 'N/A')}",
            f"  Latitude      : {geo.get('latitude', 'N/A')}",
            f"  Longitude     : {geo.get('longitude', 'N/A')}",
            f"  Timezone      : {geo.get('timezone', 'N/A')}",
            "",
            "  ── NETWORK ──────────────────────────────────────────────",
            f"  ISP           : {net.get('isp', 'N/A')}",
            f"  Organization  : {net.get('organization', 'N/A')}",
            f"  ASN           : {net.get('asn', 'N/A')}",
            f"  Hostname      : {net.get('hostname', 'N/A')}",
            "",
            "  ── REVERSE DNS ──────────────────────────────────────────",
            f"  PTR Record    : {r.get('reverse_dns', 'N/A')}",
        ]

        if self._map_url:
            lines += [
                "",
                "  ── MAP ──────────────────────────────────────────────────",
                f"  Google Maps   : {self._map_url}",
            ]

        if r.get("risk_notes"):
            lines += ["", "  ── RISK ANALYSIS ────────────────────────────────────────"]
            for note in r["risk_notes"]:
                lines.append(f"  {note}")

        if geo.get("error"):
            lines.append(f"\n  ⚠ Geolocation error: {geo['error']}")

        lines.append("\n" + "━" * 60)
        self.results_panel.set_text("\n".join(lines))

        # Update cards
        self.card_country.set_value(f"{geo.get('country', '—')} {geo.get('country_code', '')}")
        self.card_isp.set_value(net.get("isp", "—")[:22])
        self.card_city.set_value(f"{geo.get('city', '—')}, {geo.get('region', '')}"[:22])
        self.card_asn.set_value(net.get("asn", "—")[:22])

        if self._map_url:
            self._map_btn.configure(state="normal")

        self.search_bar.set_state("normal")
        self.status_bar.set_ready("IP analysis complete")

    def _open_map(self):
        if self._map_url:
            import webbrowser
            webbrowser.open(self._map_url)

    def _on_error(self, err: str):
        self.results_panel.set_text(f"✗  Analysis failed:\n\n{err}")
        self.search_bar.set_state("normal")
        self.status_bar.set_error("Analysis failed")

    def _export_json(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first.")
            return
        path = save_json_report(self._last_results, "ip", self._target)
        self.results_panel.append_text(f"\n\n✓  JSON saved → {path}")

    def _export_html(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first.")
            return
        path = generate_html_report(self._last_results, "ip", self._target)
        self.results_panel.append_text(f"\n\n✓  HTML report saved → {path}")
