"""
ReconX – Breach Intelligence Tab
Connects to modules/breach_checker.py
"""

import threading
import customtkinter as ctk
from gui.theme import *
from gui.components import SearchBar, ResultsPanel, SectionLabel, InfoCard
from modules.breach_checker import check_breach, KNOWN_BREACHES
from utils.report_generator import save_json_report, generate_html_report
from utils.logger import get_logger

logger = get_logger("breach_tab")

RISK_COLORS = {
    "CRITICAL": NEON_PINK,
    "HIGH":     NEON_ORANGE,
    "MEDIUM":   NEON_BLUE,
    "LOW":      NEON_GREEN,
    "Unknown":  TEXT_DIM,
}


class BreachTab(ctk.CTkFrame):
    def __init__(self, parent, status_bar, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.status_bar = status_bar
        self._last_results = None
        self._target = ""
        self._build()

    def _build(self):
        # ── Title ──────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_XL, pady=(PAD_XL, PAD_MD))
        ctk.CTkLabel(
            header, text="🕵  BREACH INTELLIGENCE",
            font=ctk.CTkFont("Consolas", 16, "bold"),
            text_color=NEON_GREEN
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=f"{len(KNOWN_BREACHES)} BREACH RECORDS  •  MULTI-SOURCE",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            text_color=NEON_GREEN,
            fg_color=BG_INPUT, corner_radius=4, width=240, height=22
        ).pack(side="right")

        # ── Warning banner ────────────────────────────────────────────────────
        warn_frame = ctk.CTkFrame(
            self, fg_color="#0d0600",
            border_color=NEON_ORANGE, border_width=1,
            corner_radius=CORNER_RADIUS
        )
        warn_frame.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        ctk.CTkLabel(
            warn_frame,
            text="⚠  EDUCATIONAL USE ONLY — Only check accounts you own or have explicit authorization to investigate.",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            text_color=NEON_ORANGE
        ).pack(padx=PAD_MD, pady=PAD_SM)

        # ── Search + type toggle ──────────────────────────────────────────────
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))

        self._type_var = ctk.StringVar(value="email")
        type_frame = ctk.CTkFrame(sf, fg_color="transparent")
        type_frame.pack(side="left", padx=(0, PAD_SM))
        ctk.CTkLabel(
            type_frame, text="TYPE:",
            font=ctk.CTkFont("Consolas", 9, "bold"),
            text_color=TEXT_DIM
        ).pack(anchor="w")
        ctk.CTkSegmentedButton(
            type_frame,
            values=["email", "username"],
            variable=self._type_var,
            font=ctk.CTkFont("Consolas", 10),
            fg_color=BG_INPUT,
            selected_color=NEON_GREEN,
            selected_hover_color="#00cc6a",
            unselected_color=BG_INPUT,
            unselected_hover_color=BG_HOVER,
            text_color="#000000",
            height=36,
        ).pack()

        self.search_bar = SearchBar(
            sf,
            placeholder="Enter email address or username to check",
            button_text="⚡ Check Breaches",
            on_search=self._start_scan
        )
        self.search_bar.pack(fill="x", expand=True)

        # ── Info cards ────────────────────────────────────────────────────────
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.card_risk   = InfoCard(stats_row, "RISK LEVEL",     "—", accent=True)
        self.card_score  = InfoCard(stats_row, "RISK SCORE",     "—")
        self.card_breach = InfoCard(stats_row, "BREACHES FOUND", "—")
        self.card_paste  = InfoCard(stats_row, "PASTE LEAKS",    "—")
        for c in (self.card_risk, self.card_score, self.card_breach, self.card_paste):
            c.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

        # ── Split layout ──────────────────────────────────────────────────────
        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_MD))
        split.columnconfigure(0, weight=3)
        split.columnconfigure(1, weight=2)
        split.rowconfigure(0, weight=1)

        rf = ctk.CTkFrame(split, fg_color="transparent")
        rf.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))
        SectionLabel(rf, "■ BREACH REPORT").pack(anchor="w", pady=(0, PAD_XS))
        self.results_panel = ResultsPanel(rf)
        self.results_panel.pack(fill="both", expand=True)

        # Known breach reference panel
        bf = ctk.CTkFrame(split, fg_color="transparent")
        bf.grid(row=0, column=1, sticky="nsew")
        SectionLabel(bf, "■ MAJOR BREACH DATABASE").pack(anchor="w", pady=(0, PAD_XS))
        self.breach_ref = ctk.CTkScrollableFrame(
            bf, fg_color=BG_PANEL,
            border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=CORNER_RADIUS,
        )
        self.breach_ref.pack(fill="both", expand=True)
        self._populate_breach_reference()

        # ── Export row ────────────────────────────────────────────────────────
        er = ctk.CTkFrame(self, fg_color="transparent")
        er.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        for text, cmd, w in [
            ("💾 Export JSON",  self._export_json,  130),
            ("📄 Export HTML",  self._export_html,  130),
        ]:
            ctk.CTkButton(
                er, text=text,
                font=ctk.CTkFont("Consolas", 10),
                fg_color="transparent", hover_color=BG_HOVER,
                text_color=NEON_CYAN,
                border_color=BORDER_SUBTLE, border_width=1,
                corner_radius=BUTTON_RADIUS, height=34, width=w,
                command=cmd
            ).pack(side="left", padx=(0, PAD_SM))

    # ── Breach reference panel ─────────────────────────────────────────────────

    def _populate_breach_reference(self):
        ctk.CTkLabel(
            self.breach_ref,
            text="NOTABLE PUBLIC BREACHES",
            font=ctk.CTkFont("Consolas", 9, "bold"),
            text_color=TEXT_DIM
        ).pack(anchor="w", padx=PAD_SM, pady=(PAD_SM, PAD_XS))

        for breach in KNOWN_BREACHES[:22]:
            row = ctk.CTkFrame(self.breach_ref, fg_color=BG_CARD, corner_radius=4)
            row.pack(fill="x", padx=PAD_SM, pady=2)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=PAD_SM, pady=4)
            ctk.CTkLabel(
                inner,
                text=f"{breach['name']} ({breach['year']})",
                font=ctk.CTkFont("Consolas", 10, "bold"),
                text_color=TEXT_PRIMARY, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                inner,
                text=breach["records"],
                font=ctk.CTkFont("Consolas", 9),
                text_color=NEON_PINK
            ).pack(side="right")
            data_str = ", ".join(breach.get("data", [])[:3])
            if data_str:
                ctk.CTkLabel(
                    row, text=f"  {data_str}",
                    font=ctk.CTkFont("Consolas", 8),
                    text_color=TEXT_DIM, anchor="w"
                ).pack(anchor="w", padx=PAD_SM, pady=(0, 3))

    # ── Scan logic ─────────────────────────────────────────────────────────────

    def _start_scan(self):
        target = self.search_bar.get_value()
        if not target:
            self.results_panel.set_text("⚠  Please enter an email or username.")
            return
        self._target = target
        self._last_results = None
        target_type = self._type_var.get()
        self.search_bar.set_state("disabled")
        self.status_bar.set_scanning(target)
        self.results_panel.clear()
        threading.Thread(
            target=self._run, args=(target, target_type), daemon=True
        ).start()

    def _run(self, target: str, target_type: str):
        try:
            results = check_breach(target, target_type)
            self._last_results = results
            self.after(0, self._display_results, results)
        except Exception as e:
            logger.error(f"Breach check error: {e}", exc_info=True)
            self.after(0, self._on_error, str(e))

    def _display_results(self, r: dict):
        bc    = r.get("breach_check", {})
        pc    = r.get("paste_check", {})
        pwc   = r.get("password_check", {})
        risk  = r.get("risk_level", "Unknown")
        score = r.get("risk_score", 0)
        dark  = r.get("dark_web_indicators", [])

        lines = [
            "━" * 62,
            "  ReconX Breach Intelligence Report",
            f"  Target     : {r['target']}",
            f"  Type       : {r['target_type'].upper()}",
            f"  Risk Level : {risk}  (Score: {score}/100)",
            "━" * 62,
            "",
            "  ── HIBP BREACH DATABASE ─────────────────────────────────────",
            f"  Source         : {bc.get('source', 'N/A')}",
            f"  Status         : {bc.get('api_status', 'N/A')}",
            f"  Breaches Found : {bc.get('breach_count', 0)}",
        ]

        if bc.get("breaches"):
            lines.append("  Breach List    :")
            for b in bc["breaches"]:
                lines.append(f"    ⚠ {b}")

        if bc.get("note"):
            lines.append(f"\n  ℹ {bc['note'][:200]}")

        if bc.get("provider_in_breaches"):
            lines += [
                "",
                "  ⚠ EMAIL PROVIDER FOUND IN THESE BREACHES:",
            ]
            for b in bc["provider_in_breaches"]:
                lines.append(f"     • {b}")

        if bc.get("leakcheck"):
            lk = bc["leakcheck"]
            lines += [
                "",
                "  ── LEAKCHECK ─────────────────────────────────────────────",
                f"  Found    : {lk.get('found', 0)} records",
            ]
            for s in lk.get("sources", [])[:5]:
                lines.append(f"    • {s}")

        lines += [
            "",
            "  ── PUBLIC PASTE SEARCH ──────────────────────────────────────",
            f"  Sources Checked : {', '.join(pc.get('sources_checked', []))}",
            f"  Found In Pastes : {'⚠ YES' if pc.get('found_in_pastes') else '✓ No'}",
            f"  Paste Count     : {pc.get('paste_count', 0)}",
        ]
        for p in pc.get("pastes", [])[:3]:
            lines.append(f"    • ID: {p.get('id','')}  |  {p.get('time','')}")
        if pc.get("note"):
            lines.append(f"  Note: {pc['note']}")

        lines += [
            "",
            "  ── PASSWORD BREACH MODEL ────────────────────────────────────",
            f"  Model  : {pwc.get('model', 'N/A')}",
            f"  API    : {pwc.get('api_endpoint', 'N/A')}",
        ]

        if dark:
            lines += ["", "  ── DARK WEB INDICATORS ─────────────────────────────────────"]
            for d in dark:
                lines.append(f"  {d}")

        lines += [
            "",
            "  ── DISCLAIMER ───────────────────────────────────────────────",
            f"  {r.get('disclaimer', '')[:220]}",
            "",
            "━" * 62,
        ]
        self.results_panel.set_text("\n".join(lines))

        self.card_risk.set_value(risk)
        self.card_score.set_value(f"{score}/100")
        self.card_breach.set_value(str(bc.get("breach_count", "—")))
        self.card_paste.set_value("Yes ⚠" if pc.get("found_in_pastes") else "No ✓")

        self.search_bar.set_state("normal")
        self.status_bar.set_ready(f"Breach check complete — Risk: {risk}")

    def _on_error(self, err: str):
        self.results_panel.set_text(f"✗  Check failed:\n\n{err}")
        self.search_bar.set_state("normal")
        self.status_bar.set_error("Check failed")

    def _export_json(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a check first."); return
        path = save_json_report(self._last_results, "breach", self._target)
        self.results_panel.append_text(f"\n\n✓  JSON saved → {path}")

    def _export_html(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run a check first."); return
        path = generate_html_report(self._last_results, "breach", self._target)
        self.results_panel.append_text(f"\n\n✓  HTML report saved → {path}")
