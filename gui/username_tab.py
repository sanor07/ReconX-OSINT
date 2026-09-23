"""
ReconX – Username Intelligence Tab
GUI for multi-platform username searches.
"""

import threading
import customtkinter as ctk
from gui.theme import *
from gui.components import SearchBar, ResultsPanel, SectionLabel, InfoCard
from modules.username_search import search_username, PLATFORMS
from utils.report_generator import save_json_report, generate_html_report
from utils.logger import get_logger

logger = get_logger("username_tab")


class UsernameTab(ctk.CTkFrame):
    def __init__(self, parent, status_bar, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.status_bar = status_bar
        self._last_results = None
        self._username = ""
        self._build()

    def _build(self):
        # ── Title ──────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_XL, pady=(PAD_XL, PAD_MD))

        ctk.CTkLabel(
            header,
            text="👤  USERNAME INTELLIGENCE",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"{len(PLATFORMS)} PLATFORMS",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            text_color=ACCENT_CYAN,
            fg_color=BG_INPUT,
            corner_radius=4,
            width=90, height=22
        ).pack(side="right")

        # ── Search bar ────────────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))

        self.search_bar = SearchBar(
            search_frame,
            placeholder="Enter username to search (e.g. john_doe)",
            button_text="⚡ Scan Now",
            on_search=self._start_scan,
        )
        self.search_bar.pack(fill="x")

        # ── Stats row ─────────────────────────────────────────────────────────
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))

        self.card_found    = InfoCard(stats_row, "FOUND",    "—", accent=True)
        self.card_total    = InfoCard(stats_row, "CHECKED",  "—")
        self.card_errors   = InfoCard(stats_row, "ERRORS",   "—")
        self.card_status   = InfoCard(stats_row, "STATUS",   "Idle")

        for card in (self.card_found, self.card_total, self.card_errors, self.card_status):
            card.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

        # ── Main split: results + platform list ────────────────────────────────
        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_MD))
        split.columnconfigure(0, weight=3)
        split.columnconfigure(1, weight=1)
        split.rowconfigure(0, weight=1)

        # Results panel
        results_frame = ctk.CTkFrame(split, fg_color="transparent")
        results_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))

        SectionLabel(results_frame, "■ SCAN RESULTS").pack(anchor="w", pady=(0, PAD_XS))
        self.results_panel = ResultsPanel(results_frame)
        self.results_panel.pack(fill="both", expand=True)

        # Platform list (right sidebar)
        pf_frame = ctk.CTkFrame(split, fg_color="transparent")
        pf_frame.grid(row=0, column=1, sticky="nsew")
        SectionLabel(pf_frame, "■ PLATFORMS").pack(anchor="w", pady=(0, PAD_XS))

        scroll = ctk.CTkScrollableFrame(
            pf_frame, fg_color=BG_PANEL,
            border_color=BORDER_COLOR, border_width=1,
            corner_radius=CORNER_RADIUS,
            scrollbar_button_color=BG_HOVER,
        )
        scroll.pack(fill="both", expand=True)

        self._platform_labels = {}
        for name in sorted(PLATFORMS.keys()):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=PAD_SM, pady=1)
            dot = ctk.CTkLabel(row, text="●", font=ctk.CTkFont("Consolas", 10), text_color=TEXT_DIM, width=16)
            dot.pack(side="left")
            lbl = ctk.CTkLabel(row, text=name, font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_SECONDARY, anchor="w")
            lbl.pack(side="left", fill="x")
            self._platform_labels[name] = (dot, lbl)

        # ── Export buttons ────────────────────────────────────────────────────
        export_row = ctk.CTkFrame(self, fg_color="transparent")
        export_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))

        ctk.CTkButton(
            export_row, text="💾 Export JSON",
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color=BG_INPUT, hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            corner_radius=BUTTON_RADIUS, height=34, width=130,
            command=self._export_json
        ).pack(side="left", padx=(0, PAD_SM))

        ctk.CTkButton(
            export_row, text="📄 Export HTML Report",
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color=BG_INPUT, hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            corner_radius=BUTTON_RADIUS, height=34, width=160,
            command=self._export_html
        ).pack(side="left")

    # ── Scan logic ─────────────────────────────────────────────────────────────

    def _start_scan(self):
        username = self.search_bar.get_value()
        if not username:
            self.results_panel.set_text("⚠  Please enter a username to search.")
            return

        self._username = username
        self._last_results = None
        self.search_bar.set_state("disabled")
        self.status_bar.set_scanning(username)
        self.card_status.set_value("Scanning...")
        self.card_found.set_value("—")
        self.card_total.set_value(str(len(PLATFORMS)))
        self.card_errors.set_value("—")
        self.results_panel.clear()
        self._reset_platform_indicators()

        # Run in background thread
        thread = threading.Thread(target=self._run_scan, args=(username,), daemon=True)
        thread.start()

    def _run_scan(self, username: str):
        found_count = [0]
        checked_count = [0]

        def progress_cb(platform, result):
            checked_count[0] += 1
            found = result.get("found", False)
            if found:
                found_count[0] += 1
            # Update platform indicator on main thread
            self.after(0, self._update_platform_indicator, platform, found, result.get("error"))
            # Update progress cards
            progress = checked_count[0] / len(PLATFORMS)
            self.after(0, self.status_bar.set_progress, progress,
                       f"Checking {platform}...")
            self.after(0, self.card_found.set_value, str(found_count[0]))
            self.after(0, self.card_errors.set_value,
                       str(len([r for r in [result] if r.get("error")])))

        try:
            results = search_username(username, progress_callback=progress_cb)
            self._last_results = results
            self.after(0, self._display_results, results)
        except Exception as e:
            logger.error(f"Username scan error: {e}", exc_info=True)
            self.after(0, self._on_scan_error, str(e))

    def _display_results(self, results: dict):
        lines = [
            "━" * 60,
            f"  ReconX Username Intelligence Report",
            f"  Target  : @{results['username']}",
            f"  Found   : {len(results['found'])} / {results['total']} platforms",
            f"  Errors  : {len(results['errors'])}",
            "━" * 60,
            "",
        ]

        if results["found"]:
            lines.append("  ✅  FOUND ON PLATFORMS:\n")
            for platform, url in sorted(results["found"].items()):
                lines.append(f"  [{platform:<20}]  {url}")
            lines.append("")

        if results["not_found"]:
            lines.append("  ✗  NOT FOUND:\n")
            chunk = [f"  {p}" for p in sorted(results["not_found"])]
            lines.extend(chunk)
            lines.append("")

        if results["errors"]:
            lines.append("  ⚠  ERRORS:\n")
            for p, err in results["errors"].items():
                lines.append(f"  {p:<20}  {err[:80]}")
            lines.append("")

        lines.append("━" * 60)

        self.results_panel.set_text("\n".join(lines))
        self.card_found.set_value(str(len(results["found"])))
        self.card_total.set_value(str(results["total"]))
        self.card_errors.set_value(str(len(results["errors"])))
        self.card_status.set_value("Complete ✓")
        self.search_bar.set_state("normal")
        self.status_bar.set_ready(f"Scan complete — {len(results['found'])} profiles found")

    def _on_scan_error(self, error: str):
        self.results_panel.set_text(f"✗  Scan failed:\n\n{error}")
        self.card_status.set_value("Error")
        self.search_bar.set_state("normal")
        self.status_bar.set_error("Scan failed")

    def _update_platform_indicator(self, platform: str, found: bool, error=None):
        if platform not in self._platform_labels:
            return
        dot, lbl = self._platform_labels[platform]
        if error:
            dot.configure(text_color=WARNING)
            lbl.configure(text_color=TEXT_DIM)
        elif found:
            dot.configure(text_color=SUCCESS)
            lbl.configure(text_color=ACCENT_CYAN)
        else:
            dot.configure(text_color=DANGER)
            lbl.configure(text_color=TEXT_DIM)

    def _reset_platform_indicators(self):
        for dot, lbl in self._platform_labels.values():
            dot.configure(text_color=TEXT_DIM)
            lbl.configure(text_color=TEXT_SECONDARY)

    def _export_json(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  No results to export. Run a scan first.")
            return
        path = save_json_report(self._last_results, "username", self._username)
        self.results_panel.append_text(f"\n\n✓  JSON saved → {path}")
        self.status_bar.set_ready("JSON exported")

    def _export_html(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  No results to export. Run a scan first.")
            return
        path = generate_html_report(self._last_results, "username", self._username)
        self.results_panel.append_text(f"\n\n✓  HTML report saved → {path}")
        self.status_bar.set_ready("HTML report exported")
