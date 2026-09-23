"""
ReconX – Subdomain Finder Tab
"""

import threading
import customtkinter as ctk
from gui.theme import *
from gui.components import SearchBar, ResultsPanel, SectionLabel, InfoCard
from modules.subdomain_finder import find_subdomains
from utils.report_generator import save_json_report, generate_html_report
from utils.logger import get_logger

logger = get_logger("subdomain_tab")


class SubdomainTab(ctk.CTkFrame):
    def __init__(self, parent, status_bar, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.status_bar = status_bar
        self._last_results = None
        self._target = ""
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_XL, pady=(PAD_XL, PAD_MD))
        ctk.CTkLabel(header, text="🔎  SUBDOMAIN FINDER",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="WORDLIST + CRT.SH",
                     font=ctk.CTkFont("Consolas", 10, "bold"),
                     text_color=ACCENT_CYAN, fg_color=BG_INPUT,
                     corner_radius=4, width=130, height=22).pack(side="right")

        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.search_bar = SearchBar(sf,
            placeholder="Enter domain (e.g. example.com)",
            button_text="⚡ Enumerate",
            on_search=self._start_scan)
        self.search_bar.pack(fill="x")

        sr = ctk.CTkFrame(self, fg_color="transparent")
        sr.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.card_found   = InfoCard(sr, "FOUND",        "—", accent=True)
        self.card_checked = InfoCard(sr, "WORDLIST",     "—")
        self.card_crtsh   = InfoCard(sr, "FROM CRT.SH",  "—")
        self.card_wl      = InfoCard(sr, "FROM WORDLIST","—")
        for c in (self.card_found, self.card_checked, self.card_crtsh, self.card_wl):
            c.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_MD))
        split.columnconfigure(0, weight=3)
        split.columnconfigure(1, weight=2)
        split.rowconfigure(0, weight=1)

        rf = ctk.CTkFrame(split, fg_color="transparent")
        rf.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))
        SectionLabel(rf, "■ SCAN OUTPUT").pack(anchor="w", pady=(0, PAD_XS))
        self.results_panel = ResultsPanel(rf)
        self.results_panel.pack(fill="both", expand=True)

        lf = ctk.CTkFrame(split, fg_color="transparent")
        lf.grid(row=0, column=1, sticky="nsew")
        SectionLabel(lf, "■ LIVE RESULTS").pack(anchor="w", pady=(0, PAD_XS))
        self.live_list = ctk.CTkScrollableFrame(lf,
            fg_color=BG_PANEL, border_color=BORDER_COLOR,
            border_width=1, corner_radius=CORNER_RADIUS)
        self.live_list.pack(fill="both", expand=True)

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
        self._clear_live_list()
        self.card_found.set_value("0")
        threading.Thread(target=self._run, args=(domain,), daemon=True).start()

    def _run(self, domain: str):
        def progress_cb(checked, total, found):
            pct = checked / total if total else 0
            self.after(0, self.status_bar.set_progress, pct,
                       f"Checking wordlist {checked}/{total}")
            self.after(0, self.card_checked.set_value, str(total))
            self.after(0, self.card_found.set_value, str(found))

        try:
            results = find_subdomains(domain, progress_callback=progress_cb)
            self._last_results = results
            self.after(0, self._display_results, results)
        except Exception as e:
            logger.error(f"Subdomain scan error: {e}", exc_info=True)
            self.after(0, self._on_error, str(e))

    def _display_results(self, r: dict):
        subs = r.get("subdomains", [])
        sources = r.get("sources", {})
        lines = [
            "━" * 60,
            "  ReconX Subdomain Enumeration Report",
            f"  Domain     : {r['domain']}",
            f"  Total Found: {r['total_found']}",
            f"  From crt.sh: {sources.get('crt.sh', 0)}",
            f"  From WL    : {sources.get('wordlist', 0)}",
            "━" * 60, "",
        ]
        if subs:
            lines.append("  ✅  DISCOVERED SUBDOMAINS:\n")
            for item in subs:
                src = item.get("source", "")
                ip  = item.get("ip", "Unresolved")
                lines.append(
                    f"  [{src:<9}] {item['subdomain']:<40}  {ip}")
        else:
            lines.append("  No subdomains discovered.")
        lines.append("\n" + "━" * 60)
        self.results_panel.set_text("\n".join(lines))

        self._clear_live_list()
        for item in subs:
            self._add_live_item(
                item["subdomain"], item.get("ip",""), item.get("source",""))

        self.card_found.set_value(str(r["total_found"]))
        self.card_crtsh.set_value(str(sources.get("crt.sh", 0)))
        self.card_wl.set_value(str(sources.get("wordlist", 0)))
        self.search_bar.set_state("normal")
        self.status_bar.set_ready(f"Found {r['total_found']} subdomains")

    def _add_live_item(self, subdomain, ip, source):
        row = ctk.CTkFrame(self.live_list, fg_color="transparent")
        row.pack(fill="x", padx=PAD_SM, pady=1)
        color = ACCENT_CYAN if source == "crt.sh" else SUCCESS
        ctk.CTkLabel(row, text="●", font=ctk.CTkFont("Consolas", 10),
                     text_color=color, width=14).pack(side="left")
        ctk.CTkLabel(row, text=subdomain[:36],
                     font=ctk.CTkFont("Consolas", 10),
                     text_color=TEXT_PRIMARY, anchor="w").pack(
                         side="left", fill="x", expand=True)
        if ip:
            ctk.CTkLabel(row, text=ip[:15],
                         font=ctk.CTkFont("Consolas", 9),
                         text_color=TEXT_DIM).pack(side="right")

    def _clear_live_list(self):
        for w in self.live_list.winfo_children():
            w.destroy()

    def _on_error(self, err):
        self.results_panel.set_text(f"✗  Scan failed:\n\n{err}")
        self.search_bar.set_state("normal")
        self.status_bar.set_error("Scan failed")

    def _export_json(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first.")
            return
        path = save_json_report(self._last_results, "subdomain", self._target)
        self.results_panel.append_text(f"\n\n✓  JSON saved → {path}")

    def _export_html(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a scan first.")
            return
        path = generate_html_report(self._last_results, "subdomain", self._target)
        self.results_panel.append_text(f"\n\n✓  HTML report saved → {path}")
