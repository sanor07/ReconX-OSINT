"""
ReconX GUI Theme — Premium Hacker Edition
Ultra-dark, neon-accented cyberpunk aesthetic.
"""

# ── Core Background Palette ────────────────────────────────────────────────────
BG_DARK       = "#04080f"       # Void black — main window
BG_PANEL      = "#080d16"       # Panel surface
BG_SIDEBAR    = "#020509"       # Sidebar — near-black
BG_INPUT      = "#0c1220"       # Input fields
BG_HOVER      = "#101828"       # Hover state
BG_SELECTED   = "#0a1f35"       # Active nav item
BG_CARD       = "#0b1422"       # Card backgrounds
BG_OVERLAY    = "#060b14"       # Overlay / modal

# ── Neon Accent Palette ────────────────────────────────────────────────────────
NEON_GREEN    = "#00ff88"       # Primary neon — electric green
NEON_CYAN     = "#00e5ff"       # Secondary neon — ice cyan
NEON_PURPLE   = "#b44fff"       # Tertiary — vivid purple
NEON_PINK     = "#ff2d78"       # Alert pink
NEON_BLUE     = "#0ea5e9"       # Info blue
NEON_ORANGE   = "#ff6b35"       # Warning orange
NEON_YELLOW   = "#ffd700"       # Gold accent

# ── Legacy alias names (keeps existing tabs working without changes) ───────────
ACCENT_CYAN   = NEON_GREEN      # map old cyan → new primary neon green
ACCENT_PURPLE = NEON_PURPLE
ACCENT_BLUE   = NEON_CYAN
ACCENT_ORANGE = NEON_ORANGE

# ── Text Palette ───────────────────────────────────────────────────────────────
TEXT_PRIMARY  = "#ccd6f6"       # Soft blue-white
TEXT_SECONDARY= "#64748b"       # Muted slate
TEXT_ACCENT   = NEON_GREEN      # Green accent text
TEXT_DIM      = "#2d3a4a"       # Very muted
TEXT_BRIGHT   = "#ffffff"       # Pure white for emphasis

# ── Border Palette ─────────────────────────────────────────────────────────────
BORDER_COLOR  = "#0f1f33"       # Default border — almost invisible
BORDER_GLOW   = NEON_GREEN      # Glow border accent
BORDER_SUBTLE = "#1a2740"       # Slightly visible border

# ── Semantic Colors ────────────────────────────────────────────────────────────
SUCCESS       = "#00ff88"       # Neon green
DANGER        = "#ff2d78"       # Neon pink-red
WARNING       = "#ff6b35"       # Neon orange
INFO          = "#00e5ff"       # Neon cyan

# ── Typography ─────────────────────────────────────────────────────────────────
FONT_MONO_XS  = ("Consolas", 9)
FONT_MONO_SM  = ("Consolas", 10)
FONT_MONO     = ("Consolas", 11)
FONT_MONO_MD  = ("Consolas", 12)
FONT_MONO_LG  = ("Consolas", 14, "bold")
FONT_MONO_XL  = ("Consolas", 18, "bold")
FONT_LOGO     = ("Consolas", 24, "bold")

FONT_UI_XS    = ("Segoe UI", 10)
FONT_UI_SM    = ("Segoe UI", 11)
FONT_UI_BASE  = ("Segoe UI", 12)
FONT_UI_MD    = ("Segoe UI", 13)
FONT_UI_LG    = ("Segoe UI", 15, "bold")
FONT_UI_XL    = ("Segoe UI", 20, "bold")

# ── Spacing ────────────────────────────────────────────────────────────────────
PAD_XS  = 4
PAD_SM  = 8
PAD_MD  = 14
PAD_LG  = 20
PAD_XL  = 28

# ── Geometry ───────────────────────────────────────────────────────────────────
WINDOW_SIZE    = "1400x880"
SIDEBAR_WIDTH  = 252
CORNER_RADIUS  = 6
BUTTON_RADIUS  = 5
