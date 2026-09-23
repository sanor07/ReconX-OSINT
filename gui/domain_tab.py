"""
ReconX – Domain Intelligence Tab
"""

import threading
import customtkinter as ctk
from gui.theme import *
from gui.components import SearchBar, ResultsPanel, SectionLabel, InfoCard
from modules.domain_lookup import analyze_domain
from utils.report_generator import save_json_report, generate_html_report
from utils.logger import get_logger

logger = get_logger("domain_tab")


class DomainTab(ctk.CTkFrame):
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
            header, text="🌐  DOMAIN INTELLIGENCE",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.search_bar = SearchBar(
            search_frame,
            placeholder="Enter domain (e.g. example.com or https://example.com)",
            button_text="⚡ Investigate",
            on_search=self._start_scan,
        )
        self.search_bar.pack(fill="x")

        # Info cards
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.card_ip        = InfoCard(stats_row, "PRIMARY IP",     "—", accent=True)
        self.card_registrar = InfoCard(stats_row, "REGISTRAR",      "—")
        self.card_created   = InfoCard(stats_row, "CREATED",        "—")
        self.card_expires   = InfoCard(stats_row, "EXPIRES",        "—")
        for c in (self.card_ip, self.card_registrar, self.card_created, self.card_expires):
            c.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

        # Split layout: results + DNS records
        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_MD))
        split.columnconfigure(0, weight=3)
        split.columnconfigure(1, weight=1)
        split.rowconfigure(0, weight=1)

        # Results panel
        res_frame = ctk.CTkFrame(split, fg_color="transparent")
        res_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))
        SectionLabel(res_frame, "■ DOMAIN ANALYSIS").pack(anchor="w", pady=(0, PAD_XS))
        self.results_panel = ResultsPanel(res_frame)
        self.results_panel.pack(fill="both", expand=True)

        # DNS quick-view panel
        dns_frame = ctk.CTkFrame(split, fg_color="transparent")
        dns_frame.grid(row=0, column=1, sticky="nsew")
        SectionLabel(dns_frame, "■ DNS RECORDS").pack(anchor="w", pady=(0, PAD_XS))
        self.dns_panel = ctk.CTkScrollableFrame(
            dns_frame, fg_color=BG_PANEL,
            border_color=BORDER_COLOR, border_width=1,
            corner_radius=CORNER_RADIUS,
        )
        self.dns_panel.pack(fill="both", expand=True)
        self._dns_placeholder = ctk.CTkLabel(
            self.dns_panel, text="Run a scan to\nsee DNS records.",
            font=ctk.CTkFont("Consolas", 11), text_color=TEXT_DIM
        )
        self._dns_placeholder.pack(pady=PAD_XL)

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

    def _start_scan(self):
        domain = self.search_bar.get_value()
        if not domain:
            self.results_panel.set_text("⚠  Please enter a domain name.")
            return
        self._target = domain
        self._last_results = None
        self.search_bar.set_state("disabled")
        self.status_bar.set_scanning(domain)
        self.results_panel.clear()
        threading.Thread(target=self._run, args=(domain,), daemon=True).start()

    def _run(self, domain: str):
        try:
            results = analyze_domain(domain)
            self._last_results = results
            self.after(0, self._display_results, results)
        except Exception as e:
            logger.error(f"Domain analysis error: {e}", exc_info=True)
            self.after(0, self._on_error, str(e))

    def _display_results(self, r: dict):
        whois = r.get("whois", {})
        dns   = r.get("dns", {})
        host  = r.get("hosting", {})
        web   = r.get("web_info", {})
        geo   = host.get("geolocation", {})

        lines = [
            "━" * 60,
            "  ReconX Domain Intelligence Report",
            f"  Domain    : {r['domain']}",
            "━" * 60,
            "",
            "  ── WHOIS ────────────────────────────────────────────────",
            f"  Registrar     : {whois.get('registrar', 'N/A')}",
            f"  Created       : {whois.get('creation_date', 'N/A')}",
            f"  Expires       : {whois.get('expiration_date', 'N/A')}",
            f"  Updated       : {whois.get('updated_date', 'N/A')}",
            f"  Name Servers  : {whois.get('name_servers', 'N/A')}",
            f"  Status        : {whois.get('status', 'N/A')}",
            f"  Registrant Org: {whois.get('org', 'N/A')}",
            f"  Country       : {whois.get('country', 'N/A')}",
            f"  Emails        : {whois.get('emails', 'N/A')}",
            "",
            "  ── HOSTING & GEOLOCATION ────────────────────────────────",
            f"  Primary IP    : {host.get('primary_ip', 'N/A')}",
            f"  Country       : {geo.get('country', 'N/A')} ({geo.get('city', '')})",
            f"  ISP           : {geo.get('isp', 'N/A')}",
            f"  Organization  : {geo.get('org', 'N/A')}",
            f"  Coordinates   : {geo.get('lat', '')} , {geo.get('lon', '')}",
            "",
            "  ── WEB SERVER ───────────────────────────────────────────",
            f"  HTTP Status   : {web.get('http_status', 'N/A')}",
            f"  Server        : {web.get('server', 'N/A')}",
            f"  X-Powered-By  : {web.get('x_powered_by', 'N/A')}",
            f"  HSTS          : {web.get('strict_transport_security', 'N/A')}",
            f"  X-Frame-Opts  : {web.get('x_frame_options', 'N/A')}",
            f"  CSP           : {web.get('content_security_policy', 'N/A')[:80]}",
            "",
            "  ── SUBDOMAINS (Common Check) ────────────────────────────",
        ]
        subs = r.get("subdomains_found", [])
        if subs:
            for s in subs:
                lines.append(f"  ✓ {s}")
        else:
            lines.append("  No common subdomains found.")

        if whois.get("error"):
            lines.append(f"\n  ⚠ WHOIS Error: {whois['error']}")

        lines.append("\n" + "━" * 60)
        self.results_panel.set_text("\n".join(lines))

        # Update DNS quick-view
        self._populate_dns_panel(dns)

        # Update cards
        ip_str = str(host.get("primary_ip", "N/A"))
        reg_str = str(whois.get("registrar", "N/A"))[:22]
        cre_str = str(whois.get("creation_date", "N/A"))[:20]
        exp_str = str(whois.get("expiration_date", "N/A"))[:20]
        self.card_ip.set_value(ip_str)
        self.card_registrar.set_value(reg_str)
        self.card_created.set_value(cre_str)
        self.card_expires.set_value(exp_str)

        self.search_bar.set_state("normal")
        self.status_bar.set_ready("Domain analysis complete")

    def _populate_dns_panel(self, dns: dict):
        for widget in self.dns_panel.winfo_children():
            widget.destroy()

        record_colors = {
            "A": ACCENT_CYAN, "AAAA": ACCENT_BLUE,
            "MX": ACCENT_PURPLE, "NS": SUCCESS,
            "TXT": WARNING, "CNAME": INFO, "SOA": TEXT_SECONDARY,
        }
        for rtype, records in dns.items():
            color = record_colors.get(rtype, TEXT_SECONDARY)
            ctk.CTkLabel(
                self.dns_panel, text=rtype,
                font=ctk.CTkFont("Consolas", 10, "bold"),
                text_color=color,
                fg_color=BG_INPUT, corner_radius=3, width=40
            ).pack(anchor="w", padx=PAD_SM, pady=(PAD_SM, 0))

            if records:
                for rec in records:
                    ctk.CTkLabel(
                        self.dns_panel,
                        text=f"  {rec[:45]}",
                        font=ctk.CTkFont("Consolas", 10),
                        text_color=TEXT_SECONDARY,
                        anchor="w", wraplength=180
                    ).pack(anchor="w", padx=PAD_SM)
            else:
                ctk.CTkLabel(
                    self.dns_panel, text="  —",
                    font=ctk.CTkFont("Consolas", 10),
                    text_color=TEXT_DIM
                ).pack(anchor="w", padx=PAD_SM)

    def _on_error(self, err: str):
        self.results_panel.set_text(f"✗  Analysis failed:\n\n{err}")
        self.search_bar.set_state("normal")
        self.status_bar.set_error("Analysis failed")

    def _export_json(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first.")
            return
        path = save_json_report(self._last_results, "domain", self._target)
        self.results_panel.append_text(f"\n\n✓  JSON saved → {path}")

    def _export_html(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first.")
            return
        path = generate_html_report(self._last_results, "domain", self._target)
        self.results_panel.append_text(f"\n\n✓  HTML report saved → {path}")
