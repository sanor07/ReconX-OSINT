"""
ReconX GUI Components — Premium Hacker Edition
Reusable custom widgets with neon-cyberpunk aesthetic.
"""

import customtkinter as ctk
from tkinter import Canvas
from gui.theme import *


class SectionLabel(ctk.CTkLabel):
    """Styled section header with neon left-bar accent."""
    def __init__(self, parent, text, **kwargs):
        super().__init__(
            parent,
            text=f"  {text}",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            text_color=NEON_GREEN,
            **kwargs
        )


class GlowDivider(ctk.CTkFrame):
    """A 1-px line that glows with the accent color."""
    def __init__(self, parent, color=None, **kwargs):
        super().__init__(
            parent,
            height=1,
            fg_color=color or BORDER_SUBTLE,
            corner_radius=0,
            **kwargs
        )


class NeonBadge(ctk.CTkLabel):
    """Small pill badge with neon color."""
    def __init__(self, parent, text, color=None, **kwargs):
        c = color or NEON_GREEN
        super().__init__(
            parent,
            text=f" {text} ",
            font=ctk.CTkFont("Consolas", 9, "bold"),
            text_color=c,
            fg_color=_alpha_mix(c, BG_DARK, 0.12),
            corner_radius=3,
            **kwargs
        )


class ResultsPanel(ctk.CTkFrame):
    """
    Terminal-style scrollable output panel.
    Dark background with green-on-black monospace text — pure hacker aesthetic.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=BG_OVERLAY,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=CORNER_RADIUS,
            **kwargs
        )
        self._build()

    def _build(self):
        # Terminal toolbar
        toolbar = ctk.CTkFrame(self, fg_color=BG_CARD, height=30, corner_radius=0)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        # Traffic-light dots
        dot_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        dot_frame.pack(side="left", padx=(10, 0), pady=8)
        for dot_color in ("#ff5f56", "#ffbd2e", "#27c93f"):
            ctk.CTkLabel(
                dot_frame, text="●",
                font=ctk.CTkFont("Consolas", 9),
                text_color=dot_color, width=14
            ).pack(side="left", padx=1)

        ctk.CTkLabel(
            toolbar, text="  ▸  RECONX TERMINAL  —  OUTPUT",
            font=ctk.CTkFont("Consolas", 9, "bold"),
            text_color=TEXT_DIM
        ).pack(side="left", padx=4)

        # Copy button
        self._copy_btn = ctk.CTkButton(
            toolbar, text="⎘ COPY", width=70, height=20,
            font=ctk.CTkFont("Consolas", 9, "bold"),
            fg_color="transparent",
            hover_color=BG_HOVER,
            text_color=NEON_GREEN,
            border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=3,
            command=self._copy_text
        )
        self._copy_btn.pack(side="right", padx=8, pady=5)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR, corner_radius=0).pack(fill="x")

        # Text area — monospace terminal look
        self.text_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont("Consolas", 12),
            fg_color=BG_OVERLAY,
            text_color=NEON_GREEN,
            border_width=0,
            wrap="word",
            activate_scrollbars=True,
        )
        self.text_box.pack(fill="both", expand=True, padx=2, pady=2)

        # Cursor blink on the label (purely visual)
        self._blink_state = True

    def _copy_text(self):
        content = self.text_box.get("1.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            self._copy_btn.configure(text="✓ COPIED")
            self.after(1500, lambda: self._copy_btn.configure(text="⎘ COPY"))

    def set_text(self, content: str):
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", content)

    def append_text(self, content: str):
        self.text_box.configure(state="normal")
        self.text_box.insert("end", content)
        self.text_box.see("end")

    def clear(self):
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")


class SearchBar(ctk.CTkFrame):
    """Hacker-style input field with neon scan button."""
    def __init__(self, parent, placeholder: str, button_text: str,
                 on_search, on_secondary=None, secondary_text: str = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_search = on_search
        self._build(placeholder, button_text, on_secondary, secondary_text)

    def _build(self, placeholder, button_text, on_secondary, secondary_text):
        # Entry field
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=f"  ›  {placeholder}",
            font=ctk.CTkFont("Consolas", 12),
            fg_color=BG_INPUT,
            border_color=BORDER_SUBTLE,
            border_width=1,
            text_color=NEON_GREEN,
            placeholder_text_color=TEXT_DIM,
            corner_radius=BUTTON_RADIUS,
            height=42,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))
        self.entry.bind("<Return>", lambda e: self._on_search())
        self.entry.bind("<FocusIn>",  lambda e: self.entry.configure(border_color=NEON_GREEN))
        self.entry.bind("<FocusOut>", lambda e: self.entry.configure(border_color=BORDER_SUBTLE))

        # Primary action button
        self.search_btn = ctk.CTkButton(
            self,
            text=button_text,
            font=ctk.CTkFont("Consolas", 11, "bold"),
            fg_color=NEON_GREEN,
            hover_color="#00cc6a",
            text_color="#000000",
            corner_radius=BUTTON_RADIUS,
            height=42,
            width=150,
            command=self._on_search,
        )
        self.search_btn.pack(side="left")

        if on_secondary and secondary_text:
            ctk.CTkButton(
                self,
                text=secondary_text,
                font=ctk.CTkFont("Consolas", 10),
                fg_color=BG_INPUT,
                hover_color=BG_HOVER,
                text_color=NEON_CYAN,
                border_color=BORDER_SUBTLE, border_width=1,
                corner_radius=BUTTON_RADIUS,
                height=42, width=130,
                command=on_secondary,
            ).pack(side="left", padx=(PAD_SM, 0))

    def get_value(self) -> str:
        return self.entry.get().strip()

    def set_value(self, value: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def set_state(self, state: str):
        self.search_btn.configure(state=state)
        self.entry.configure(state=state)


class StatusBar(ctk.CTkFrame):
    """
    Premium status bar with animated neon pulse, progress bar,
    and 'Developed by Sanowar Hussain' credit on the right.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=BG_SIDEBAR,
            height=34,
            corner_radius=0,
            **kwargs
        )
        self.pack_propagate(False)
        self._build()

    def _build(self):
        # Left side: status indicator
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=PAD_MD, fill="y")

        self._pulse_dot = ctk.CTkLabel(
            left, text="◉",
            font=ctk.CTkFont("Consolas", 11, "bold"),
            text_color=NEON_GREEN
        )
        self._pulse_dot.pack(side="left", padx=(0, 6))

        self._status_label = ctk.CTkLabel(
            left, text="SYSTEM READY",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            text_color=NEON_GREEN
        )
        self._status_label.pack(side="left")

        # Right side: credit + version
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=PAD_MD, fill="y")

        ctk.CTkLabel(
            right,
            text="Developed by ",
            font=ctk.CTkFont("Consolas", 9),
            text_color=TEXT_DIM
        ).pack(side="left")

        ctk.CTkLabel(
            right,
            text="Sanowar Hussain",
            font=ctk.CTkFont("Consolas", 9, "bold"),
            text_color=NEON_GREEN
        ).pack(side="left")

        ctk.CTkLabel(
            right,
            text="  |  ReconX v2.0  |  OSINT Framework",
            font=ctk.CTkFont("Consolas", 9),
            text_color=TEXT_DIM
        ).pack(side="left")

        # Progress bar — center
        self.progress_bar = ctk.CTkProgressBar(
            self, height=3, width=220,
            fg_color=BG_HOVER,
            progress_color=NEON_GREEN,
            corner_radius=0,
        )
        self.progress_bar.pack(side="right", padx=(0, PAD_LG))
        self.progress_bar.set(0)

        # Start pulse animation
        self._pulse_cycle()

    def _pulse_cycle(self):
        """Animate the pulse dot."""
        try:
            current = self._pulse_dot.cget("text_color")
            if current == NEON_GREEN:
                self._pulse_dot.configure(text_color=_alpha_mix(NEON_GREEN, BG_DARK, 0.3))
            else:
                self._pulse_dot.configure(text_color=NEON_GREEN)
            self.after(900, self._pulse_cycle)
        except Exception:
            pass

    def set_scanning(self, target: str = ""):
        txt = f"SCANNING  {target[:30]}" if target else "SCANNING..."
        self._status_label.configure(text=txt, text_color=NEON_ORANGE)
        self._pulse_dot.configure(text_color=NEON_ORANGE)
        self.progress_bar.configure(mode="indeterminate", progress_color=NEON_ORANGE)
        self.progress_bar.start()

    def set_ready(self, message: str = "SYSTEM READY"):
        self._status_label.configure(text=message.upper()[:50], text_color=NEON_GREEN)
        self._pulse_dot.configure(text_color=NEON_GREEN)
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate", progress_color=NEON_GREEN)
        self.progress_bar.set(1)

    def set_error(self, message: str = "ERROR"):
        self._status_label.configure(text=f"[ERR]  {message.upper()[:40]}", text_color=NEON_PINK)
        self._pulse_dot.configure(text_color=NEON_PINK)
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate", progress_color=NEON_PINK)
        self.progress_bar.set(0)

    def set_progress(self, value: float, message: str = ""):
        self.progress_bar.configure(mode="determinate", progress_color=NEON_ORANGE)
        self.progress_bar.set(max(0.0, min(1.0, value)))
        if message:
            self._status_label.configure(
                text=message.upper()[:50], text_color=NEON_ORANGE
            )


class InfoCard(ctk.CTkFrame):
    """
    Neon-accented stat card with glowing border on accent cards.
    """
    def __init__(self, parent, label: str, value: str = "—",
                 accent: bool = False, **kwargs):
        border_c = NEON_GREEN if accent else BORDER_SUBTLE
        super().__init__(
            parent,
            fg_color=BG_CARD,
            border_color=border_c,
            border_width=1,
            corner_radius=CORNER_RADIUS,
            **kwargs
        )
        self._accent = accent

        ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont("Consolas", 9, "bold"),
            text_color=NEON_GREEN if accent else TEXT_DIM
        ).pack(anchor="w", padx=PAD_SM, pady=(PAD_SM, 0))

        self._val_label = ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont("Consolas", 14, "bold"),
            text_color=NEON_GREEN if accent else TEXT_PRIMARY,
            wraplength=200
        )
        self._val_label.pack(anchor="w", padx=PAD_SM, pady=(1, PAD_SM))

    def set_value(self, value: str):
        self._val_label.configure(text=value)


# ── Internal helper ────────────────────────────────────────────────────────────

def _alpha_mix(hex_fg: str, hex_bg: str, alpha: float) -> str:
    """Blend hex_fg over hex_bg at `alpha` opacity (0–1)."""
    def parse(h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    fr, fg_c, fb = parse(hex_fg)
    br, bg_c, bb = parse(hex_bg)
    r = int(fr * alpha + br * (1 - alpha))
    g = int(fg_c * alpha + bg_c * (1 - alpha))
    b = int(fb * alpha + bb * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"
