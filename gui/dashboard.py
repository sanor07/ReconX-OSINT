"""
ReconX Dashboard — Premium Hacker Edition
Ultra-dark neon cyberpunk interface with animated elements.
"""

import time
import threading
import customtkinter as ctk
from tkinter import Canvas
from gui.theme import *
from gui.components import StatusBar, GlowDivider
from gui.username_tab  import UsernameTab
from gui.email_tab     import EmailTab
from gui.domain_tab    import DomainTab
from gui.ip_tab        import IPTab
from gui.metadata_tab  import MetadataTab
from gui.subdomain_tab import SubdomainTab
from gui.tech_tab      import TechTab
from gui.phone_tab     import PhoneTab
from gui.breach_tab    import BreachTab
from gui.graph_tab     import GraphTab
from utils.logger      import get_logger

logger = get_logger("dashboard")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Navigation manifest ────────────────────────────────────────────────────────
# (icon, label, TabClass, kind)   kind = "header" | "item"
NAV_ITEMS = [
    (None,  "── RECON ──",     None,          "header"),
    ("󰀄",  "Username",        UsernameTab,   "item"),
    ("",   "Email",           EmailTab,      "item"),
    ("󰖟",  "Domain",          DomainTab,     "item"),
    ("󰩟",  "IP Lookup",       IPTab,         "item"),
    (None,  "── ADVANCED ──",  None,          "header"),
    ("󰍉",  "Subdomains",      SubdomainTab,  "item"),
    ("󰒓",  "Tech Detect",     TechTab,       "item"),
    (None,  "── IDENTITY ──",  None,          "header"),
    ("",   "Phone",           PhoneTab,      "item"),
    ("󰋞",  "Breach Check",    BreachTab,     "item"),
    (None,  "── ANALYZE ──",   None,          "header"),
    ("󰋩",  "Metadata",        MetadataTab,   "item"),
    ("󰕮",  "Graph View",      GraphTab,      "item"),
]

# Flat list of (icon, label, cls) for tab indexing
TAB_ITEMS = [(ic, lb, cls)
             for ic, lb, cls, kind in NAV_ITEMS if kind == "item"]

# ASCII icon fallbacks (used when nerd-font glyphs are unavailable)
ASCII_ICONS = {
    "Username":     "[ @ ]",
    "Email":        "[ ✉ ]",
    "Domain":       "[ 🌐 ]",
    "IP Lookup":    "[ 🔍 ]",
    "Subdomains":   "[ 🔎 ]",
    "Tech Detect":  "[ ⚙ ]",
    "Phone":        "[ 📞 ]",
    "Breach Check": "[ 🕵 ]",
    "Metadata":     "[ 🖼 ]",
    "Graph View":   "[ 🕸 ]",
}


class ReconXDashboard(ctk.CTk):
    """Main application window — Premium Hacker Edition."""

    def __init__(self):
        super().__init__()
        self.title("ReconX v2.0  ─  OSINT Intelligence Framework")
        self.geometry(WINDOW_SIZE)
        self.minsize(1100, 700)
        self.configure(fg_color=BG_DARK)

        self._active_tab_index = 0
        self._tab_frames: list[ctk.CTkFrame] = []
        self._nav_buttons: list[ctk.CTkButton] = []
        self._matrix_chars = []  # for animated canvas

        self._build_layout()
        self._select_tab(0)
        logger.info("ReconX Premium Dashboard initialized.")

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, fg_color=BG_SIDEBAR, corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self._build_sidebar()

        # Content pane
        self.content_area = ctk.CTkFrame(
            self, fg_color=BG_DARK, corner_radius=0
        )
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self._draw_content_grid_lines()

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Build all tabs
        for _, _, TabClass in TAB_ITEMS:
            tab = TabClass(self.content_area, self.status_bar)
            tab.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._tab_frames.append(tab)

    def _draw_content_grid_lines(self):
        """Draw subtle dot-grid background on the content area."""
        try:
            bg = Canvas(
                self.content_area,
                bg=BG_DARK, highlightthickness=0
            )
            bg.place(x=0, y=0, relwidth=1, relheight=1)
            bg.lower()

            def _redraw(event=None):
                bg.delete("grid")
                w = bg.winfo_width()
                h = bg.winfo_height()
                step = 28
                for x in range(0, w + step, step):
                    for y in range(0, h + step, step):
                        bg.create_oval(
                            x - 1, y - 1, x + 1, y + 1,
                            fill="#0d1828", outline="", tags="grid"
                        )
            bg.bind("<Configure>", _redraw)
        except Exception:
            pass

    # ── Sidebar ────────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = self.sidebar

        # Neon top bar (3-layer glow effect)
        ctk.CTkFrame(sb, height=1, fg_color=NEON_GREEN,    corner_radius=0).pack(fill="x")
        ctk.CTkFrame(sb, height=2, fg_color="#004422",     corner_radius=0).pack(fill="x")
        ctk.CTkFrame(sb, height=1, fg_color=BORDER_SUBTLE, corner_radius=0).pack(fill="x")

        # ── Logo block ─────────────────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(sb, fg_color="transparent", height=100)
        logo_frame.pack(fill="x", padx=0, pady=0)
        logo_frame.pack_propagate(False)

        logo_canvas = Canvas(logo_frame, bg=BG_SIDEBAR,
                             highlightthickness=0, height=100)
        logo_canvas.pack(fill="both", expand=True)

        def _draw_logo(event=None):
            logo_canvas.delete("all")
            w = logo_canvas.winfo_width() or SIDEBAR_WIDTH
            cx = w // 2

            # Hex circuit decorations
            for ox, oy, size, alpha in [(-60, 50, 30, 0.15), (60, 50, 22, 0.10)]:
                c = _hex_mix(NEON_GREEN, BG_SIDEBAR, alpha)
                logo_canvas.create_polygon(
                    _hex_points(cx + ox, oy, size),
                    outline=c, fill="", width=1
                )

            # RECON text
            logo_canvas.create_text(
                cx - 18, 42, text="RECON",
                font=("Consolas", 22, "bold"),
                fill=TEXT_PRIMARY, anchor="e"
            )
            # X in neon
            logo_canvas.create_text(
                cx - 18, 42, text="     X",
                font=("Consolas", 22, "bold"),
                fill=NEON_GREEN, anchor="e"
            )
            # v2 badge
            logo_canvas.create_rectangle(
                cx + 6, 30, cx + 36, 48,
                fill="#001a0d", outline=NEON_GREEN, width=1
            )
            logo_canvas.create_text(
                cx + 21, 39, text="v2.0",
                font=("Consolas", 8, "bold"),
                fill=NEON_GREEN, anchor="center"
            )
            # Subtitle
            logo_canvas.create_text(
                cx, 68, text="OSINT INTELLIGENCE FRAMEWORK",
                font=("Consolas", 7, "bold"),
                fill=TEXT_DIM, anchor="center", spacing=4
            )
            # Scan line effect
            logo_canvas.create_line(
                0, 85, w, 85,
                fill=BORDER_SUBTLE, dash=(4, 6)
            )

        logo_canvas.bind("<Configure>", _draw_logo)
        self.after(50, _draw_logo)

        # ── System info strip ──────────────────────────────────────────────────
        sys_strip = ctk.CTkFrame(sb, fg_color=BG_OVERLAY, height=22, corner_radius=0)
        sys_strip.pack(fill="x")
        sys_strip.pack_propagate(False)
        ctk.CTkLabel(
            sys_strip,
            text="  ◈  MODULES  ONLINE  ◈  10 / 10  ◈",
            font=ctk.CTkFont("Consolas", 8),
            text_color=NEON_GREEN
        ).pack(side="left", padx=PAD_SM)

        GlowDivider(sb, color=BORDER_SUBTLE).pack(fill="x")

        # ── Scrollable nav ─────────────────────────────────────────────────────
        nav_scroll = ctk.CTkScrollableFrame(
            sb, fg_color="transparent",
            scrollbar_button_color=BG_HOVER,
            scrollbar_button_hover_color=BORDER_SUBTLE,
        )
        nav_scroll.pack(fill="both", expand=True, padx=0, pady=(PAD_XS, 0))

        btn_idx = 0
        for icon, label, cls, kind in NAV_ITEMS:
            if kind == "header":
                # Section header with decorative line
                hdr = ctk.CTkFrame(nav_scroll, fg_color="transparent")
                hdr.pack(fill="x", padx=PAD_SM, pady=(PAD_MD, 2))
                ctk.CTkLabel(
                    hdr, text=label,
                    font=ctk.CTkFont("Consolas", 8, "bold"),
                    text_color=TEXT_DIM
                ).pack(side="left", padx=(PAD_SM, PAD_XS))
                ctk.CTkFrame(
                    hdr, height=1, fg_color=BORDER_SUBTLE
                ).pack(side="left", fill="x", expand=True, pady=4)
            else:
                ascii_icon = ASCII_ICONS.get(label, "[ · ]")
                btn = ctk.CTkButton(
                    nav_scroll,
                    text=f"  {ascii_icon}  {label}",
                    font=ctk.CTkFont("Consolas", 11),
                    anchor="w",
                    height=38,
                    corner_radius=BUTTON_RADIUS,
                    fg_color="transparent",
                    hover_color=BG_HOVER,
                    text_color=TEXT_SECONDARY,
                    border_width=0,
                    command=lambda i=btn_idx: self._select_tab(i),
                )
                btn.pack(fill="x", padx=PAD_XS, pady=1)
                self._nav_buttons.append(btn)
                btn_idx += 1

        # ── Footer ─────────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(sb, fg_color=BG_OVERLAY, corner_radius=0)
        footer.pack(fill="x", side="bottom")

        GlowDivider(footer, color=BORDER_SUBTLE).pack(fill="x")

        # Warning row
        warn_row = ctk.CTkFrame(footer, fg_color="transparent")
        warn_row.pack(fill="x", padx=PAD_SM, pady=(PAD_XS, 0))
        ctk.CTkLabel(
            warn_row, text="⚠",
            font=ctk.CTkFont("Consolas", 9),
            text_color=NEON_ORANGE
        ).pack(side="left")
        ctk.CTkLabel(
            warn_row, text="  AUTHORIZED USE ONLY",
            font=ctk.CTkFont("Consolas", 8, "bold"),
            text_color=NEON_ORANGE
        ).pack(side="left")

        # Developer credit
        dev_row = ctk.CTkFrame(footer, fg_color="transparent")
        dev_row.pack(fill="x", padx=PAD_SM, pady=(2, PAD_SM))
        ctk.CTkLabel(
            dev_row, text="dev://",
            font=ctk.CTkFont("Consolas", 8),
            text_color=TEXT_DIM
        ).pack(side="left")
        ctk.CTkLabel(
            dev_row, text=" Sanowar Hussain",
            font=ctk.CTkFont("Consolas", 8, "bold"),
            text_color=NEON_GREEN
        ).pack(side="left")

    # ── Tab switching ──────────────────────────────────────────────────────────

    def _select_tab(self, index: int):
        self._active_tab_index = index

        for i, frame in enumerate(self._tab_frames):
            frame.lift() if i == index else frame.lower()

        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.configure(
                    fg_color=BG_SELECTED,
                    text_color=NEON_GREEN,
                    border_width=1,
                    border_color=NEON_GREEN,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY,
                    border_width=0,
                )
        logger.debug(f"Tab → {TAB_ITEMS[index][1]}")


# ── Canvas helpers ─────────────────────────────────────────────────────────────

def _hex_points(cx: float, cy: float, r: float) -> list:
    """Return flat list of (x, y) for a regular hexagon."""
    import math
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts += [cx + r * math.cos(angle), cy + r * math.sin(angle)]
    return pts


def _hex_mix(fg: str, bg: str, alpha: float) -> str:
    """Mix two hex colours at alpha (0–1)."""
    def p(h): h = h.lstrip("#"); return int(h[:2],16), int(h[2:4],16), int(h[4:6],16)
    fr, fg2, fb = p(fg)
    br, bg2, bb = p(bg)
    r = int(fr * alpha + br * (1 - alpha))
    g = int(fg2 * alpha + bg2 * (1 - alpha))
    b = int(fb * alpha + bb * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"
