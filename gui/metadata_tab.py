"""
ReconX – Image Metadata Extractor Tab
"""

import threading
import os
import customtkinter as ctk
from tkinter import filedialog
from gui.theme import *
from gui.components import ResultsPanel, SectionLabel, InfoCard
from modules.metadata_extractor import extract_metadata
from utils.report_generator import save_json_report, generate_html_report
from utils.logger import get_logger

logger = get_logger("metadata_tab")

SUPPORTED_FORMATS = ("*.jpg", "*.jpeg", "*.png", "*.tiff", "*.tif", "*.bmp", "*.webp", "*.heic")


class MetadataTab(ctk.CTkFrame):
    def __init__(self, parent, status_bar, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.status_bar = status_bar
        self._last_results = None
        self._filepath = ""
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_XL, pady=(PAD_XL, PAD_MD))
        ctk.CTkLabel(
            header, text="🖼  IMAGE METADATA EXTRACTOR",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        # File picker row
        file_row = ctk.CTkFrame(self, fg_color="transparent")
        file_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))

        self.file_entry = ctk.CTkEntry(
            file_row,
            placeholder_text="No file selected — click Browse to choose an image",
            font=ctk.CTkFont("Consolas", 12),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_DIM,
            corner_radius=BUTTON_RADIUS, height=40,
            state="readonly",
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))

        ctk.CTkButton(
            file_row, text="📁 Browse",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="transparent", hover_color=BG_HOVER, text_color=NEON_CYAN, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=BUTTON_RADIUS, height=40, width=100,
            command=self._browse_file
        ).pack(side="left", padx=(0, PAD_SM))

        self._analyze_btn = ctk.CTkButton(
            file_row, text="⚡ Extract Metadata",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=ACCENT_CYAN, hover_color="#00b894", text_color="#0a0e1a",
            corner_radius=BUTTON_RADIUS, height=40, width=160,
            command=self._start_scan, state="disabled"
        )
        self._analyze_btn.pack(side="left")

        # Info cards
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        self.card_format = InfoCard(stats_row, "FORMAT",       "—")
        self.card_size   = InfoCard(stats_row, "DIMENSIONS",   "—", accent=True)
        self.card_gps    = InfoCard(stats_row, "GPS DATA",     "—")
        self.card_camera = InfoCard(stats_row, "CAMERA",       "—")
        for c in (self.card_format, self.card_size, self.card_gps, self.card_camera):
            c.pack(side="left", expand=True, fill="x", padx=(0, PAD_SM))

        # Drop zone hint
        drop_hint = ctk.CTkFrame(
            self, fg_color=BG_PANEL,
            border_color=BORDER_COLOR, border_width=1,
            corner_radius=CORNER_RADIUS, height=60
        )
        drop_hint.pack(fill="x", padx=PAD_XL, pady=(0, PAD_MD))
        drop_hint.pack_propagate(False)
        ctk.CTkLabel(
            drop_hint,
            text="Supported formats: JPG · JPEG · PNG · TIFF · BMP · WEBP",
            font=ctk.CTkFont("Consolas", 11),
            text_color=TEXT_DIM
        ).pack(expand=True)

        # Results panel
        res_frame = ctk.CTkFrame(self, fg_color="transparent")
        res_frame.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_MD))
        SectionLabel(res_frame, "■ METADATA RESULTS").pack(anchor="w", pady=(0, PAD_XS))
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

        # GPS map button
        self._map_btn = ctk.CTkButton(
            export_row, text="🗺 View GPS on Map",
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color="transparent", hover_color=BG_HOVER, text_color=NEON_CYAN, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=BUTTON_RADIUS, height=34, width=150,
            command=self._open_map, state="disabled"
        )
        self._map_btn.pack(side="left", padx=(PAD_SM, 0))

    def _browse_file(self):
        filetypes = [("Image files", " ".join(SUPPORTED_FORMATS)), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Select Image File", filetypes=filetypes)
        if path:
            self._filepath = path
            self.file_entry.configure(state="normal")
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, path)
            self.file_entry.configure(state="readonly")
            self._analyze_btn.configure(state="normal")
            self._map_btn.configure(state="disabled")

    def _start_scan(self):
        if not self._filepath:
            return
        self._last_results = None
        self._analyze_btn.configure(state="disabled")
        self.status_bar.set_scanning(os.path.basename(self._filepath))
        self.results_panel.clear()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            results = extract_metadata(self._filepath)
            self._last_results = results
            self.after(0, self._display_results, results)
        except Exception as e:
            logger.error(f"Metadata extraction error: {e}", exc_info=True)
            self.after(0, self._on_error, str(e))

    def _display_results(self, r: dict):
        fi   = r.get("file_info", {})
        exif = r.get("exif_data", {})
        gps  = r.get("gps_data", {})

        lines = [
            "━" * 60,
            "  ReconX Image Metadata Analysis",
            f"  File      : {fi.get('filename', 'N/A')}",
            "━" * 60,
            "",
            "  ── FILE INFORMATION ─────────────────────────────────────",
            f"  Filename      : {fi.get('filename', 'N/A')}",
            f"  Format        : {fi.get('format', 'N/A')} ({fi.get('extension', '')})",
            f"  Dimensions    : {fi.get('width_px', 'N/A')} × {fi.get('height_px', 'N/A')} px",
            f"  File Size     : {fi.get('size_kb', 'N/A')} KB ({fi.get('size_bytes', 'N/A')} bytes)",
            f"  Color Mode    : {fi.get('mode', 'N/A')}",
            f"  Last Modified : {fi.get('last_modified', 'N/A')}",
            "",
            "  ── EXIF METADATA ────────────────────────────────────────",
        ]

        if exif:
            for key, val in exif.items():
                if key == "note":
                    lines.append(f"  ℹ {val}")
                else:
                    lines.append(f"  {key:<26}: {str(val)[:80]}")
        else:
            lines.append("  No EXIF data available.")

        if gps:
            lines += [
                "",
                "  ── GPS / LOCATION DATA ──────────────────────────────────",
                f"  Latitude      : {gps.get('latitude', 'N/A')}",
                f"  Longitude     : {gps.get('longitude', 'N/A')}",
                f"  Altitude (m)  : {gps.get('altitude_m', 'N/A')}",
                f"  Lat Ref       : {gps.get('lat_ref', 'N/A')}",
                f"  Lon Ref       : {gps.get('lon_ref', 'N/A')}",
            ]
            if gps.get("google_maps_url"):
                lines.append(f"  Google Maps   : {gps['google_maps_url']}")
                self._gps_url = gps["google_maps_url"]
                self._map_btn.configure(state="normal")

        lines += [
            "",
            "  ── RISK INDICATORS ──────────────────────────────────────",
        ]
        for note in r.get("risk_notes", []):
            lines.append(f"  {note}")

        lines.append("\n" + "━" * 60)
        self.results_panel.set_text("\n".join(lines))

        # Update cards
        self.card_format.set_value(fi.get("format", "—"))
        self.card_size.set_value(f"{fi.get('width_px', '?')}×{fi.get('height_px', '?')}")
        has_gps = bool(gps.get("latitude"))
        self.card_gps.set_value("⚠ Embedded!" if has_gps else "✓ None")
        cam = exif.get("Camera Make", "—")
        model = exif.get("Camera Model", "")
        self.card_camera.set_value(f"{cam} {model}"[:22])

        self._analyze_btn.configure(state="normal")
        self.status_bar.set_ready("Metadata extraction complete")

    def _open_map(self):
        if hasattr(self, "_gps_url") and self._gps_url:
            import webbrowser
            webbrowser.open(self._gps_url)

    def _on_error(self, err: str):
        self.results_panel.set_text(f"✗  Extraction failed:\n\n{err}")
        self._analyze_btn.configure(state="normal")
        self.status_bar.set_error("Extraction failed")

    def _export_json(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run extraction first.")
            return
        path = save_json_report(self._last_results, "metadata", self._filepath)
        self.results_panel.append_text(f"\n\n✓  JSON saved → {path}")

    def _export_html(self):
        if not self._last_results:
            self.results_panel.append_text("\n\n⚠  Run extraction first.")
            return
        path = generate_html_report(self._last_results, "metadata", self._filepath)
        self.results_panel.append_text(f"\n\n✓  HTML report saved → {path}")
