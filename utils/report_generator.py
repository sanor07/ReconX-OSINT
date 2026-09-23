"""
ReconX Report Generator
Generates professional OSINT reports in HTML, JSON, and PDF formats.
PDF generation uses ReportLab (pip install reportlab).
"""

import os
import json
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("report_generator")

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


def save_json_report(data: dict, scan_type: str, target: str) -> str:
    """Save scan results as a JSON file and return the file path."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = "".join(c if c.isalnum() or c in "._-" else "_" for c in target)
    filename = f"reconx_{scan_type}_{safe_target}_{timestamp}.json"
    filepath = os.path.join(REPORT_DIR, filename)
    report = {
        "tool": "ReconX OSINT Intelligence Framework",
        "version": "1.0.0",
        "scan_type": scan_type,
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "results": data,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False, default=str)
    logger.info(f"JSON report saved: {filepath}")
    return filepath


def generate_html_report(data: dict, scan_type: str, target: str) -> str:
    """Generate a professional HTML OSINT report and return file path."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = "".join(c if c.isalnum() or c in "._-" else "_" for c in target)
    filename = f"reconx_{scan_type}_{safe_target}_{timestamp}.html"
    filepath = os.path.join(REPORT_DIR, filename)

    dt = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    rows_html = _build_rows(data)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ReconX Report – {target}</title>
<style>
  :root {{
    --bg: #0d1117;
    --surface: #161b22;
    --border: #30363d;
    --accent: #00ff88;
    --accent2: #b44fff;
    --text: #e6edf3;
    --muted: #8b949e;
    --success: #3fb950;
    --danger: #f85149;
    --warning: #d29922;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; padding: 40px 20px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  .header {{ border-bottom: 1px solid var(--border); padding-bottom: 24px; margin-bottom: 32px; }}
  .logo {{ font-size: 28px; font-weight: 800; letter-spacing: 2px; color: var(--accent); }}
  .logo span {{ color: var(--accent2); }}
  .subtitle {{ color: var(--muted); margin-top: 4px; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; }}
  .meta {{ margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }}
  .meta-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; }}
  .meta-label {{ font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: 1px; }}
  .meta-value {{ font-size: 14px; font-weight: 600; margin-top: 4px; color: var(--accent); word-break: break-all; }}
  .section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
  .section-header {{ background: rgba(0,255,136,0.06); padding: 12px 20px; font-size: 12px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--accent); border-bottom: 1px solid var(--border); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  tr:not(:last-child) td {{ border-bottom: 1px solid var(--border); }}
  td {{ padding: 10px 20px; vertical-align: top; }}
  td:first-child {{ color: var(--muted); width: 35%; font-weight: 500; }}
  td:last-child {{ color: var(--text); word-break: break-all; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
  .badge-green {{ background: rgba(63,185,80,0.15); color: var(--success); }}
  .badge-red {{ background: rgba(248,81,73,0.15); color: var(--danger); }}
  .footer {{ text-align: center; color: var(--muted); font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="logo">RECON<span>X</span></div>
    <div class="subtitle">OSINT Intelligence Framework — Scan Report</div>
    <div class="meta">
      <div class="meta-card"><div class="meta-label">Target</div><div class="meta-value">{target}</div></div>
      <div class="meta-card"><div class="meta-label">Scan Type</div><div class="meta-value">{scan_type.upper()}</div></div>
      <div class="meta-card"><div class="meta-label">Generated</div><div class="meta-value">{dt}</div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-header">⚡ Intelligence Results</div>
    <table>
      {rows_html}
    </table>
  </div>

  <div class="footer">
    Generated by ReconX v2.0 • Developed by Sanowar Hussain • For educational and authorized use only •
    {datetime.now().year} ReconX OSINT Framework
  </div>
</div>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"HTML report saved: {filepath}")
    return filepath


def _build_rows(data: dict, prefix: str = "") -> str:
    """Recursively build HTML table rows from a dict."""
    rows = ""
    for key, value in data.items():
        label = (prefix + key).replace("_", " ").title()
        if isinstance(value, dict):
            rows += _build_rows(value, prefix=f"{key}.")
        elif isinstance(value, list):
            display = "<br>".join(str(v) for v in value) if value else "<em>None</em>"
            rows += f"<tr><td>{label}</td><td>{display}</td></tr>\n"
        elif isinstance(value, bool):
            badge_class = "badge-green" if value else "badge-red"
            rows += f'<tr><td>{label}</td><td><span class="badge {badge_class}">{"Yes" if value else "No"}</span></td></tr>\n'
        else:
            display = str(value) if value else "<em>N/A</em>"
            rows += f"<tr><td>{label}</td><td>{display}</td></tr>\n"
    return rows


def generate_pdf_report(data: dict, scan_type: str, target: str) -> str:
    """
    Generate a professional dark-themed PDF OSINT report using ReportLab.
    Returns the file path of the saved PDF.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    except ImportError:
        raise ImportError(
            "ReportLab is not installed. Run: pip install reportlab"
        )

    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_tgt   = "".join(c if c.isalnum() or c in "._-" else "_" for c in target)
    filename   = f"reconx_{scan_type}_{safe_tgt}_{timestamp}.pdf"
    filepath   = os.path.join(REPORT_DIR, filename)
    dt_str     = datetime.now().strftime("%B %d, %Y  %H:%M:%S UTC")

    # ── Colour palette ────────────────────────────────────────────────────────
    C_BG        = colors.HexColor("#0d1117")
    C_SURFACE   = colors.HexColor("#161b22")
    C_ACCENT    = colors.HexColor("#00d4aa")
    C_ACCENT2   = colors.HexColor("#7c3aed")
    C_TEXT      = colors.HexColor("#e6edf3")
    C_MUTED     = colors.HexColor("#8b949e")
    C_BORDER    = colors.HexColor("#30363d")
    C_SUCCESS   = colors.HexColor("#3fb950")
    C_DANGER    = colors.HexColor("#f85149")
    C_WARNING   = colors.HexColor("#d29922")
    C_WHITE     = colors.white
    C_BLACK     = colors.black

    # ── Styles ────────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    def make_style(name, parent="Normal", **kwargs):
        return ParagraphStyle(name, parent=styles[parent], **kwargs)

    s_title   = make_style("RXTitle",   fontSize=22, textColor=C_ACCENT,
                           fontName="Helvetica-Bold", spaceAfter=2, leading=26)
    s_sub     = make_style("RXSub",     fontSize=9,  textColor=C_MUTED,
                           fontName="Helvetica", spaceAfter=8, leading=12)
    s_section = make_style("RXSection", fontSize=10, textColor=C_ACCENT,
                           fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4,
                           leading=14)
    s_key     = make_style("RXKey",     fontSize=9,  textColor=C_MUTED,
                           fontName="Helvetica", leading=13)
    s_val     = make_style("RXVal",     fontSize=9,  textColor=C_TEXT,
                           fontName="Courier", leading=13)
    s_foot    = make_style("RXFoot",    fontSize=8,  textColor=C_MUTED,
                           fontName="Helvetica", alignment=TA_CENTER)
    s_warn    = make_style("RXWarn",    fontSize=8,  textColor=C_WARNING,
                           fontName="Helvetica-Bold", leading=12)

    # ── Document setup ────────────────────────────────────────────────────────
    margin = 18 * mm
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=margin,
        title=f"ReconX Report — {target}",
        author="ReconX OSINT Framework",
    )

    story = []

    # ── Header block ──────────────────────────────────────────────────────────
    story.append(Paragraph("RECONX", s_title))
    story.append(Paragraph("OSINT Intelligence Framework — Confidential Scan Report", s_sub))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT, spaceAfter=8))

    # Meta table
    meta_data = [
        [Paragraph("<b>Target</b>", s_key),    Paragraph(str(target), s_val)],
        [Paragraph("<b>Scan Type</b>", s_key),  Paragraph(scan_type.upper(), s_val)],
        [Paragraph("<b>Generated</b>", s_key),  Paragraph(dt_str, s_val)],
        [Paragraph("<b>Tool</b>", s_key),        Paragraph("ReconX v2.0 OSINT Framework", s_val)],
    ]
    meta_tbl = Table(meta_data, colWidths=["28%", "72%"])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_SURFACE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_SURFACE, C_BG]),
        ("TEXTCOLOR",   (0, 0), (-1, -1), C_TEXT),
        ("BOX",         (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID",   (0, 0), (-1, -1), 0.3, C_BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 10))

    # ── Legal notice ──────────────────────────────────────────────────────────
    story.append(Paragraph(
        "WARNING: This report contains sensitive intelligence data. "
        "For authorized and educational use only. "
        "Do not distribute without proper authorization.",
        s_warn
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=8, spaceAfter=10))

    # ── Results section ───────────────────────────────────────────────────────
    story.append(Paragraph("INTELLIGENCE RESULTS", s_section))
    story.extend(_build_pdf_content(data, s_key, s_val, s_section, C_SURFACE, C_BG, C_BORDER, C_TEXT, C_MUTED))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Paragraph(
        f"Generated by ReconX v2.0 OSINT Framework  •  {datetime.now().year}  "
        "•  For educational and authorized use only",
        s_foot
    ))

    # ── Page background painter ───────────────────────────────────────────────
    def _paint_page(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFillColor(C_BG)
        canvas_obj.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        # Accent stripe at top
        canvas_obj.setFillColor(C_ACCENT)
        canvas_obj.rect(0, A4[1] - 4, A4[0], 4, fill=1, stroke=0)
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=_paint_page, onLaterPages=_paint_page)
    logger.info(f"PDF report saved: {filepath}")
    return filepath


def _build_pdf_content(data: dict, s_key, s_val, s_section,
                       C_SURFACE, C_BG, C_BORDER, C_TEXT, C_MUTED):
    """Recursively convert data dict into ReportLab flowables."""
    from reportlab.platypus import Table, TableStyle, Spacer, Paragraph
    from reportlab.lib import colors
    flowables = []
    rows = _flatten_dict(data)

    # Split into chunks of 30 rows per table to avoid overflow
    chunk_size = 30
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        tdata = [
            [Paragraph(k, s_key), Paragraph(str(v)[:300], s_val)]
            for k, v in chunk
        ]
        tbl = Table(tdata, colWidths=["35%", "65%"])
        tbl.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_SURFACE, C_BG]),
            ("BOX",            (0, 0), (-1, -1), 0.4, C_BORDER),
            ("INNERGRID",      (0, 0), (-1, -1), 0.2, C_BORDER),
            ("LEFTPADDING",    (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
            ("TOPPADDING",     (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
            ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ]))
        flowables.append(tbl)
        if i + chunk_size < len(rows):
            flowables.append(Spacer(1, 6))
    return flowables


def _flatten_dict(data: dict, prefix: str = "", max_depth: int = 6) -> list:
    """Flatten nested dict into (key, value) pairs for table rows."""
    rows = []
    if max_depth <= 0:
        return rows
    for k, v in data.items():
        label = (prefix + str(k)).replace("_", " ").title()
        if isinstance(v, dict):
            rows.extend(_flatten_dict(v, prefix=f"{k}.", max_depth=max_depth - 1))
        elif isinstance(v, list):
            display = "; ".join(str(i) for i in v[:10]) if v else "None"
            rows.append((label, display[:300]))
        elif isinstance(v, bool):
            rows.append((label, "Yes" if v else "No"))
        else:
            rows.append((label, str(v)[:300] if v else "N/A"))
    return rows
