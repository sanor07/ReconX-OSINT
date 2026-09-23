"""
ReconX – Interactive Graph Visualization Tab
Renders an interactive force-directed node-link graph of OSINT connections
using Python's tkinter Canvas — no external graph library needed.

Features:
  • Drag nodes to reposition
  • Zoom in/out with scroll wheel
  • Click nodes to inspect details
  • Auto-layout via force-directed simulation
  • Color-coded node types
  • Animated layout settling
  • Add entities from any module result
"""

import math
import random
import threading
import time
import customtkinter as ctk
from tkinter import Canvas, StringVar
from gui.theme import *
from gui.components import SectionLabel
from utils.logger import get_logger

logger = get_logger("graph_tab")

# ── Node type definitions ──────────────────────────────────────────────────────
NODE_TYPES = {
    "target":    {"color": "#00ff88", "radius": 22, "label": "TARGET"},
    "domain":    {"color": "#00e5ff", "radius": 18, "label": "DOMAIN"},
    "ip":        {"color": "#ff6b35", "radius": 16, "label": "IP"},
    "email":     {"color": "#b44fff", "radius": 16, "label": "EMAIL"},
    "phone":     {"color": "#10b981", "radius": 16, "label": "PHONE"},
    "username":  {"color": "#ff2d78", "radius": 16, "label": "USERNAME"},
    "subdomain": {"color": "#00e5ff", "radius": 12, "label": "SUBDOMAIN"},
    "tech":      {"color": "#ffd700", "radius": 12, "label": "TECH"},
    "breach":    {"color": "#ff2d78", "radius": 14, "label": "BREACH"},
    "platform":  {"color": "#8b5cf6", "radius": 12, "label": "PLATFORM"},
    "isp":       {"color": "#f97316", "radius": 14, "label": "ISP"},
    "location":  {"color": "#14b8a6", "radius": 14, "label": "LOCATION"},
    "ns":        {"color": "#64748b", "radius": 12, "label": "NS"},
    "generic":   {"color": "#94a3b8", "radius": 12, "label": "NODE"},
}

EDGE_COLORS = {
    "resolves_to":   "#3b82f6",
    "hosts":         "#f59e0b",
    "subdomain_of":  "#06b6d4",
    "uses_tech":     "#84cc16",
    "breach_of":     "#dc2626",
    "belongs_to":    "#7c3aed",
    "found_on":      "#8b5cf6",
    "located_in":    "#14b8a6",
    "registered_by": "#94a3b8",
    "default":       "#334155",
}

# Physics constants
REPULSION    = 8000.0
ATTRACTION   = 0.035
DAMPING      = 0.82
CENTER_PULL  = 0.008
MIN_DIST     = 60.0
MAX_VELOCITY = 12.0


class GraphNode:
    """A single node in the graph."""
    __slots__ = ("id", "label", "node_type", "x", "y", "vx", "vy",
                 "metadata", "canvas_ids", "pinned")

    def __init__(self, node_id: str, label: str, node_type: str = "generic",
                 x: float = 0, y: float = 0, metadata: dict = None):
        self.id          = node_id
        self.label       = label[:24]
        self.node_type   = node_type
        self.x           = x
        self.y           = y
        self.vx          = random.uniform(-1, 1)
        self.vy          = random.uniform(-1, 1)
        self.metadata    = metadata or {}
        self.canvas_ids  = {}
        self.pinned      = False


class GraphEdge:
    """A directed edge between two nodes."""
    __slots__ = ("source", "target", "label", "edge_type", "canvas_id")

    def __init__(self, source: str, target: str,
                 label: str = "", edge_type: str = "default"):
        self.source    = source
        self.target    = target
        self.label     = label
        self.edge_type = edge_type
        self.canvas_id = None


class GraphTab(ctk.CTkFrame):
    """Interactive force-directed graph visualization tab."""

    def __init__(self, parent, status_bar, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.status_bar = status_bar

        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge]      = []
        self._selected_node: GraphNode | None = None
        self._drag_node: GraphNode | None = None
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._scale   = 1.0
        self._pan_x   = 0.0
        self._pan_y   = 0.0
        self._running = False
        self._sim_thread: threading.Thread | None = None

        self._build()
        self._seed_demo_graph()

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build(self):
        # Title bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_XL, pady=(PAD_XL, 0))
        ctk.CTkLabel(
            header, text="🕸  OSINT GRAPH VISUALIZER",
            font=ctk.CTkFont("Segoe UI", 18, "bold"), text_color=TEXT_PRIMARY
        ).pack(side="left")

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=BG_PANEL,
                               border_color=BORDER_COLOR, border_width=1,
                               corner_radius=CORNER_RADIUS, height=46)
        toolbar.pack(fill="x", padx=PAD_XL, pady=PAD_SM)
        toolbar.pack_propagate(False)

        # Add node controls
        ctk.CTkLabel(
            toolbar, text="Node:", font=ctk.CTkFont("Segoe UI", 11),
            text_color=TEXT_DIM
        ).pack(side="left", padx=(PAD_MD, PAD_XS), pady=PAD_SM)

        self._add_label_var = ctk.StringVar()
        add_entry = ctk.CTkEntry(
            toolbar, textvariable=self._add_label_var,
            placeholder_text="Label (e.g. example.com)",
            font=ctk.CTkFont("Consolas", 11),
            fg_color=BG_INPUT, border_color=BORDER_COLOR, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_DIM,
            corner_radius=4, height=30, width=180,
        )
        add_entry.pack(side="left", pady=PAD_SM, padx=(0, PAD_XS))

        self._add_type_var = ctk.StringVar(value="domain")
        type_menu = ctk.CTkOptionMenu(
            toolbar,
            values=list(NODE_TYPES.keys()),
            variable=self._add_type_var,
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color=BG_INPUT, button_color=BG_HOVER,
            button_hover_color=BG_SELECTED,
            dropdown_fg_color=BG_PANEL,
            text_color=TEXT_PRIMARY,
            height=30, width=110,
        )
        type_menu.pack(side="left", pady=PAD_SM, padx=(0, PAD_SM))

        ctk.CTkButton(
            toolbar, text="＋ Add Node",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color=ACCENT_CYAN, hover_color="#00b894",
            text_color="#0a0e1a", corner_radius=4,
            height=30, width=100,
            command=self._add_node_from_ui
        ).pack(side="left", pady=PAD_SM)

        # Separator
        ctk.CTkFrame(toolbar, width=1, fg_color=BORDER_COLOR).pack(
            side="left", fill="y", padx=PAD_MD, pady=PAD_SM)

        # Controls
        for text, cmd in [
            ("⟳ Re-layout", self._restart_layout),
            ("🗑 Clear",     self._clear_graph),
            ("◉ Demo",      self._seed_demo_graph),
        ]:
            ctk.CTkButton(
                toolbar, text=text,
                font=ctk.CTkFont("Segoe UI", 11),
                fg_color=BG_INPUT, hover_color=BG_HOVER,
                text_color=TEXT_SECONDARY, corner_radius=4,
                height=30, width=100, command=cmd
            ).pack(side="left", padx=(0, PAD_XS), pady=PAD_SM)

        # Zoom
        ctk.CTkFrame(toolbar, width=1, fg_color=BORDER_COLOR).pack(
            side="left", fill="y", padx=PAD_MD, pady=PAD_SM)
        ctk.CTkLabel(
            toolbar, text="Zoom:",
            font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_DIM
        ).pack(side="left", padx=(0, PAD_XS))
        for text, val in [("−", -0.2), ("+", 0.2)]:
            ctk.CTkButton(
                toolbar, text=text,
                font=ctk.CTkFont("Segoe UI", 13, "bold"),
                fg_color=BG_INPUT, hover_color=BG_HOVER,
                text_color=TEXT_SECONDARY, corner_radius=4,
                height=30, width=34,
                command=lambda v=val: self._zoom(v)
            ).pack(side="left", padx=1, pady=PAD_SM)

        # Main split: canvas + detail panel
        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=PAD_XL, pady=(0, PAD_SM))
        split.columnconfigure(0, weight=1)
        split.columnconfigure(1, weight=0)
        split.rowconfigure(0, weight=1)

        # Canvas
        canvas_frame = ctk.CTkFrame(
            split, fg_color=BG_PANEL,
            border_color=BORDER_COLOR, border_width=1,
            corner_radius=CORNER_RADIUS
        )
        canvas_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))

        self.canvas = Canvas(
            canvas_frame,
            bg="#04080f",
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)

        # Bind canvas events
        self.canvas.bind("<ButtonPress-1>",   self._on_mouse_down)
        self.canvas.bind("<B1-Motion>",        self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>",  self._on_mouse_up)
        self.canvas.bind("<MouseWheel>",       self._on_scroll)
        self.canvas.bind("<Button-4>",         self._on_scroll)
        self.canvas.bind("<Button-5>",         self._on_scroll)
        self.canvas.bind("<Configure>",        self._on_resize)

        # Detail panel
        detail_frame = ctk.CTkFrame(
            split, fg_color="transparent", width=220
        )
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.grid_propagate(False)

        SectionLabel(detail_frame, "■ NODE DETAILS").pack(anchor="w", pady=(0, PAD_XS))

        self._detail_panel = ctk.CTkScrollableFrame(
            detail_frame, fg_color=BG_PANEL,
            border_color=BORDER_COLOR, border_width=1,
            corner_radius=CORNER_RADIUS,
        )
        self._detail_panel.pack(fill="both", expand=True)
        self._detail_placeholder = ctk.CTkLabel(
            self._detail_panel,
            text="Click a node to\nsee its details.",
            font=ctk.CTkFont("Consolas", 11), text_color=TEXT_DIM
        )
        self._detail_placeholder.pack(pady=PAD_XL)

        # Legend
        legend_frame = ctk.CTkFrame(
            detail_frame, fg_color=BG_PANEL,
            border_color=BORDER_COLOR, border_width=1,
            corner_radius=CORNER_RADIUS
        )
        legend_frame.pack(fill="x", pady=(PAD_SM, 0))
        ctk.CTkLabel(
            legend_frame, text="LEGEND",
            font=ctk.CTkFont("Consolas", 9, "bold"), text_color=TEXT_DIM
        ).pack(anchor="w", padx=PAD_SM, pady=(PAD_SM, PAD_XS))
        shown = ["target", "domain", "ip", "email", "username",
                 "subdomain", "tech", "breach", "platform", "isp"]
        for ntype in shown:
            info = NODE_TYPES[ntype]
            row = ctk.CTkFrame(legend_frame, fg_color="transparent")
            row.pack(fill="x", padx=PAD_SM, pady=1)
            ctk.CTkLabel(
                row, text="●",
                font=ctk.CTkFont("Consolas", 10),
                text_color=info["color"], width=14
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=info["label"],
                font=ctk.CTkFont("Consolas", 9),
                text_color=TEXT_SECONDARY, anchor="w"
            ).pack(side="left")

        # Stats row
        stats_row = ctk.CTkFrame(self, fg_color="transparent", height=30)
        stats_row.pack(fill="x", padx=PAD_XL, pady=(0, PAD_SM))
        self._stats_label = ctk.CTkLabel(
            stats_row,
            text="Nodes: 0  |  Edges: 0  |  Scroll to zoom  |  Drag to move nodes",
            font=ctk.CTkFont("Consolas", 10),
            text_color=TEXT_DIM
        )
        self._stats_label.pack(side="left")

    # ── Graph data management ──────────────────────────────────────────────────

    def add_node(self, node_id: str, label: str, node_type: str = "generic",
                 metadata: dict = None) -> GraphNode:
        """Add or update a node in the graph. Thread-safe via after()."""
        if node_id in self._nodes:
            return self._nodes[node_id]
        cx = self.canvas.winfo_width() / 2 or 400
        cy = self.canvas.winfo_height() / 2 or 300
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(40, 180)
        node = GraphNode(
            node_id, label, node_type,
            x=cx + r * math.cos(angle),
            y=cy + r * math.sin(angle),
            metadata=metadata,
        )
        self._nodes[node_id] = node
        self._update_stats()
        return node

    def add_edge(self, source_id: str, target_id: str,
                 label: str = "", edge_type: str = "default"):
        """Add a directed edge. Nodes must already exist."""
        if source_id not in self._nodes or target_id not in self._nodes:
            return
        # Avoid duplicate edges
        for e in self._edges:
            if e.source == source_id and e.target == target_id:
                return
        self._edges.append(GraphEdge(source_id, target_id, label, edge_type))
        self._update_stats()

    def add_osint_result(self, result_type: str, data: dict):
        """
        High-level method to add a full OSINT scan result as a subgraph.
        Called by other tabs after a scan completes.
        """
        try:
            if result_type == "domain":
                self._ingest_domain(data)
            elif result_type == "ip":
                self._ingest_ip(data)
            elif result_type == "username":
                self._ingest_username(data)
            elif result_type == "email":
                self._ingest_email(data)
            elif result_type == "subdomains":
                self._ingest_subdomains(data)
            elif result_type == "tech":
                self._ingest_tech(data)
            self._restart_layout()
        except Exception as e:
            logger.error(f"Graph ingest error: {e}", exc_info=True)

    # ── OSINT ingestion helpers ────────────────────────────────────────────────

    def _ingest_domain(self, data: dict):
        domain = data.get("domain", "unknown")
        self.add_node(domain, domain, "target", {"source": "domain_scan"})
        ip = data.get("hosting", {}).get("primary_ip", "")
        if ip and ip != "Could not resolve":
            self.add_node(ip, ip, "ip")
            self.add_edge(domain, ip, "resolves_to", "resolves_to")
        geo = data.get("hosting", {}).get("geolocation", {})
        isp = geo.get("isp", "")
        if isp:
            self.add_node(f"isp_{isp}", isp[:30], "isp", {"full": isp})
            self.add_edge(ip or domain, f"isp_{isp}", "hosted_by", "hosts")
        city = geo.get("city", "")
        country = geo.get("country", "")
        if city and country:
            loc_id = f"loc_{city}_{country}"
            self.add_node(loc_id, f"{city}, {country}", "location")
            self.add_edge(ip or domain, loc_id, "located_in", "located_in")
        ns_list = str(data.get("whois", {}).get("name_servers", "")).replace("{", "").replace("}", "").split(",")
        for ns in ns_list[:3]:
            ns = ns.strip().strip("'\"")
            if ns and len(ns) > 3:
                self.add_node(f"ns_{ns}", ns[:28], "ns")
                self.add_edge(domain, f"ns_{ns}", "ns", "registered_by")

    def _ingest_ip(self, data: dict):
        ip = data.get("ip", "unknown")
        self.add_node(ip, ip, "target", {"source": "ip_scan"})
        geo = data.get("geolocation", {})
        city, country = geo.get("city", ""), geo.get("country", "")
        if city:
            loc_id = f"loc_{city}"
            self.add_node(loc_id, f"{city}, {country}", "location")
            self.add_edge(ip, loc_id, "located_in", "located_in")
        isp = data.get("network", {}).get("isp", "")
        if isp:
            isp_id = f"isp_{isp[:20]}"
            self.add_node(isp_id, isp[:24], "isp")
            self.add_edge(ip, isp_id, "ISP", "hosts")

    def _ingest_username(self, data: dict):
        username = data.get("username", "unknown")
        self.add_node(f"@{username}", f"@{username}", "target", {"source": "username_scan"})
        for platform, url in list(data.get("found", {}).items())[:15]:
            plat_id = f"plat_{platform}"
            self.add_node(plat_id, platform, "platform", {"url": url})
            self.add_edge(f"@{username}", plat_id, "found_on", "found_on")

    def _ingest_email(self, data: dict):
        email = data.get("email", "unknown")
        self.add_node(email, email, "target", {"source": "email_scan"})
        domain = data.get("validation", {}).get("domain", "")
        if domain:
            self.add_node(domain, domain, "domain")
            self.add_edge(email, domain, "domain", "belongs_to")
        provider = data.get("provider_guess", "")
        if provider:
            self.add_node(f"prov_{provider}", provider[:24], "isp", {"type": "mail_provider"})
            self.add_edge(domain or email, f"prov_{provider}", "uses", "hosts")

    def _ingest_subdomains(self, data: dict):
        domain = data.get("domain", "unknown")
        self.add_node(domain, domain, "target", {"source": "subdomain_scan"})
        for sub, info in list(data.get("found", {}).items())[:30]:
            self.add_node(sub, sub[:28], "subdomain", {"ip": info.get("ip", "")})
            self.add_edge(domain, sub, "", "subdomain_of")
            ip = info.get("ip", "")
            if ip and ip != "unresolved":
                ip_id = f"ip_{ip}"
                self.add_node(ip_id, ip, "ip")
                self.add_edge(sub, ip_id, "→", "resolves_to")

    def _ingest_tech(self, data: dict):
        domain = data.get("domain", "unknown")
        self.add_node(domain, domain, "target", {"source": "tech_scan"})
        for category, techs in data.get("detected", {}).items():
            for tech in techs[:6]:
                tech_id = f"tech_{tech}"
                self.add_node(tech_id, tech[:22], "tech", {"category": category})
                self.add_edge(domain, tech_id, category[:12], "uses_tech")

    # ── Physics simulation ─────────────────────────────────────────────────────

    def _start_simulation(self):
        if self._sim_thread and self._sim_thread.is_alive():
            return
        self._running = True
        self._sim_thread = threading.Thread(
            target=self._simulation_loop, daemon=True
        )
        self._sim_thread.start()

    def _stop_simulation(self):
        self._running = False

    def _simulation_loop(self):
        """Force-directed layout engine running in a background thread."""
        iterations = 0
        max_iter   = 300
        while self._running and iterations < max_iter:
            nodes = list(self._nodes.values())
            n = len(nodes)
            if n == 0:
                time.sleep(0.05)
                iterations += 1
                continue

            cx = self.canvas.winfo_width() / 2 or 400
            cy = self.canvas.winfo_height() / 2 or 300

            # Compute forces
            forces = {node.id: [0.0, 0.0] for node in nodes}

            # Repulsion (Barnes-Hut approximation: O(n²) simplified)
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = nodes[i], nodes[j]
                    dx = a.x - b.x
                    dy = a.y - b.y
                    dist = max(math.hypot(dx, dy), MIN_DIST)
                    f = REPULSION / (dist * dist)
                    fx = f * dx / dist
                    fy = f * dy / dist
                    forces[a.id][0] += fx
                    forces[a.id][1] += fy
                    forces[b.id][0] -= fx
                    forces[b.id][1] -= fy

            # Attraction (spring forces along edges)
            for edge in self._edges:
                a = self._nodes.get(edge.source)
                b = self._nodes.get(edge.target)
                if not a or not b:
                    continue
                dx = b.x - a.x
                dy = b.y - a.y
                dist = max(math.hypot(dx, dy), 1.0)
                f = ATTRACTION * dist
                fx = f * dx / dist
                fy = f * dy / dist
                forces[a.id][0] += fx
                forces[a.id][1] += fy
                forces[b.id][0] -= fx
                forces[b.id][1] -= fy

            # Center gravity
            for node in nodes:
                forces[node.id][0] += CENTER_PULL * (cx - node.x)
                forces[node.id][1] += CENTER_PULL * (cy - node.y)

            # Integrate velocities
            for node in nodes:
                if node.pinned:
                    continue
                fx, fy = forces[node.id]
                node.vx = max(-MAX_VELOCITY, min(MAX_VELOCITY, (node.vx + fx) * DAMPING))
                node.vy = max(-MAX_VELOCITY, min(MAX_VELOCITY, (node.vy + fy) * DAMPING))
                node.x += node.vx
                node.y += node.vy

            # Schedule canvas redraw on main thread
            self.after(0, self._redraw)
            time.sleep(0.033)  # ~30 FPS
            iterations += 1

        self._running = False

    # ── Canvas rendering ───────────────────────────────────────────────────────

    def _redraw(self):
        """Full canvas repaint."""
        self.canvas.delete("all")
        if not self._nodes:
            self._draw_empty_state()
            return

        # Draw edges first (below nodes)
        for edge in self._edges:
            self._draw_edge(edge)

        # Draw nodes
        for node in self._nodes.values():
            self._draw_node(node)

    def _draw_edge(self, edge: GraphEdge):
        src = self._nodes.get(edge.source)
        tgt = self._nodes.get(edge.target)
        if not src or not tgt:
            return

        sx, sy = self._world_to_canvas(src.x, src.y)
        tx, ty = self._world_to_canvas(tgt.x, tgt.y)
        color  = EDGE_COLORS.get(edge.edge_type, EDGE_COLORS["default"])

        # Draw line
        self.canvas.create_line(
            sx, sy, tx, ty,
            fill=color, width=1.5, smooth=True,
            arrow="last", arrowshape=(8, 10, 4),
            tags="edge"
        )

        # Draw edge label at midpoint
        if edge.label:
            mx = (sx + tx) / 2
            my = (sy + ty) / 2
            self.canvas.create_text(
                mx, my, text=edge.label[:14],
                font=("Consolas", 8), fill=color,
                tags="edge_label"
            )

    def _draw_node(self, node: GraphNode):
        info   = NODE_TYPES.get(node.node_type, NODE_TYPES["generic"])
        radius = int(info["radius"] * self._scale)
        color  = info["color"]
        cx, cy = self._world_to_canvas(node.x, node.y)
        is_sel = (node is self._selected_node)

        # Outer glow for selected / target nodes
        if is_sel or node.node_type == "target":
            glow_r = radius + (6 if is_sel else 4)
            self.canvas.create_oval(
                cx - glow_r, cy - glow_r,
                cx + glow_r, cy + glow_r,
                outline=color, fill="", width=2,
                tags="node_glow"
            )

        # Node circle
        self.canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            fill=color if is_sel else _hex_darken(color, 0.6),
            outline=color,
            width=2 if is_sel else 1.5,
            tags=("node", node.id)
        )

        # Type abbreviation inside
        abbr = node.node_type[:2].upper()
        self.canvas.create_text(
            cx, cy,
            text=abbr,
            font=("Consolas", max(7, int(8 * self._scale)), "bold"),
            fill=TEXT_PRIMARY if is_sel else color,
            tags=("node_text", node.id)
        )

        # Label below
        self.canvas.create_text(
            cx, cy + radius + 10,
            text=node.label[:20],
            font=("Consolas", max(7, int(9 * self._scale))),
            fill=TEXT_PRIMARY if is_sel else TEXT_SECONDARY,
            tags=("node_label", node.id)
        )

        # Pin indicator
        if node.pinned:
            self.canvas.create_text(
                cx + radius - 4, cy - radius + 4,
                text="📍", font=("Segoe UI Emoji", 8),
                tags="node_pin"
            )

    def _draw_empty_state(self):
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        self.canvas.create_text(
            cx, cy - 20,
            text="OSINT GRAPH VISUALIZER",
            font=("Consolas", 16, "bold"),
            fill=ACCENT_CYAN
        )
        self.canvas.create_text(
            cx, cy + 14,
            text="Run a scan in any module, then click  'Send to Graph'\n"
                 "Or use  ＋ Add Node  to build manually.",
            font=("Consolas", 11),
            fill=TEXT_DIM, justify="center"
        )

    # ── Coordinate transforms ──────────────────────────────────────────────────

    def _world_to_canvas(self, wx: float, wy: float) -> tuple[float, float]:
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        sx = (wx - cx) * self._scale + cx + self._pan_x
        sy = (wy - cy) * self._scale + cy + self._pan_y
        return sx, sy

    def _canvas_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        wx = (sx - cx - self._pan_x) / self._scale + cx
        wy = (sy - cy - self._pan_y) / self._scale + cy
        return wx, wy

    def _hit_test(self, sx: float, sy: float) -> GraphNode | None:
        """Return the node under canvas coordinates (sx, sy), or None."""
        for node in self._nodes.values():
            nx, ny = self._world_to_canvas(node.x, node.y)
            r = NODE_TYPES.get(node.node_type, NODE_TYPES["generic"])["radius"] * self._scale
            if math.hypot(sx - nx, sy - ny) <= r + 6:
                return node
        return None

    # ── Mouse / scroll events ──────────────────────────────────────────────────

    def _on_mouse_down(self, event):
        node = self._hit_test(event.x, event.y)
        if node:
            self._drag_node = node
            nx, ny = self._world_to_canvas(node.x, node.y)
            self._drag_offset_x = event.x - nx
            self._drag_offset_y = event.y - ny
            node.pinned = True
            self._select_node(node)
        else:
            self._drag_node = None
            self._selected_node = None
            self._update_detail_panel(None)
            self._redraw()

    def _on_mouse_drag(self, event):
        if self._drag_node:
            wx, wy = self._canvas_to_world(
                event.x - self._drag_offset_x,
                event.y - self._drag_offset_y
            )
            self._drag_node.x = wx
            self._drag_node.y = wy
            self._drag_node.vx = 0
            self._drag_node.vy = 0
            self._redraw()

    def _on_mouse_up(self, event):
        self._drag_node = None

    def _on_scroll(self, event):
        if hasattr(event, "delta") and event.delta:
            factor = 1.1 if event.delta > 0 else 0.9
        elif event.num == 4:
            factor = 1.1
        else:
            factor = 0.9
        self._zoom_at(factor, event.x, event.y)

    def _zoom_at(self, factor: float, sx: float, sy: float):
        self._scale = max(0.2, min(4.0, self._scale * factor))
        self._redraw()

    def _zoom(self, delta: float):
        self._scale = max(0.2, min(4.0, self._scale + delta))
        self._redraw()

    def _on_resize(self, event):
        self._redraw()

    # ── Node selection & details ───────────────────────────────────────────────

    def _select_node(self, node: GraphNode):
        self._selected_node = node
        self._update_detail_panel(node)
        self._redraw()

    def _update_detail_panel(self, node: GraphNode | None):
        for w in self._detail_panel.winfo_children():
            w.destroy()

        if node is None:
            ctk.CTkLabel(
                self._detail_panel, text="Click a node to\nsee its details.",
                font=ctk.CTkFont("Consolas", 11), text_color=TEXT_DIM
            ).pack(pady=PAD_XL)
            return

        info  = NODE_TYPES.get(node.node_type, NODE_TYPES["generic"])
        color = info["color"]

        ctk.CTkLabel(
            self._detail_panel,
            text=f"● {node.node_type.upper()}",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            text_color=color
        ).pack(anchor="w", padx=PAD_SM, pady=(PAD_SM, 0))

        ctk.CTkLabel(
            self._detail_panel,
            text=node.label,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=TEXT_PRIMARY,
            wraplength=190, anchor="w"
        ).pack(anchor="w", padx=PAD_SM, pady=(2, PAD_SM))

        ctk.CTkFrame(
            self._detail_panel, height=1, fg_color=BORDER_COLOR
        ).pack(fill="x", padx=PAD_SM)

        # Connections
        connected = [
            e for e in self._edges
            if e.source == node.id or e.target == node.id
        ]
        ctk.CTkLabel(
            self._detail_panel,
            text=f"Connections: {len(connected)}",
            font=ctk.CTkFont("Consolas", 10),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", padx=PAD_SM, pady=(PAD_XS, 0))

        for e in connected[:6]:
            other_id = e.target if e.source == node.id else e.source
            other    = self._nodes.get(other_id)
            if other:
                arrow = "→" if e.source == node.id else "←"
                ctk.CTkLabel(
                    self._detail_panel,
                    text=f"  {arrow} {other.label[:18]}",
                    font=ctk.CTkFont("Consolas", 9),
                    text_color=EDGE_COLORS.get(e.edge_type, TEXT_DIM)
                ).pack(anchor="w", padx=PAD_SM)

        # Metadata
        if node.metadata:
            ctk.CTkFrame(
                self._detail_panel, height=1, fg_color=BORDER_COLOR
            ).pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 0))
            ctk.CTkLabel(
                self._detail_panel, text="Metadata:",
                font=ctk.CTkFont("Consolas", 9, "bold"), text_color=TEXT_DIM
            ).pack(anchor="w", padx=PAD_SM, pady=(PAD_XS, 0))
            for k, v in node.metadata.items():
                ctk.CTkLabel(
                    self._detail_panel,
                    text=f"  {k}: {str(v)[:30]}",
                    font=ctk.CTkFont("Consolas", 9),
                    text_color=TEXT_SECONDARY,
                    anchor="w", wraplength=190
                ).pack(anchor="w", padx=PAD_SM)

        # Unpin button
        ctk.CTkButton(
            self._detail_panel,
            text="📌 Unpin" if node.pinned else "📌 Pin",
            font=ctk.CTkFont("Segoe UI", 10),
            fg_color=BG_INPUT, hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            corner_radius=4, height=26,
            command=lambda n=node: self._toggle_pin(n)
        ).pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 0))

        ctk.CTkButton(
            self._detail_panel,
            text="🗑 Remove Node",
            font=ctk.CTkFont("Segoe UI", 10),
            fg_color=BG_INPUT, hover_color="#3b0f0f",
            text_color=DANGER,
            corner_radius=4, height=26,
            command=lambda n=node: self._remove_node(n)
        ).pack(fill="x", padx=PAD_SM, pady=(PAD_XS, 0))

    def _toggle_pin(self, node: GraphNode):
        node.pinned = not node.pinned
        self._update_detail_panel(node)
        self._redraw()

    def _remove_node(self, node: GraphNode):
        self._edges = [e for e in self._edges
                       if e.source != node.id and e.target != node.id]
        del self._nodes[node.id]
        self._selected_node = None
        self._update_detail_panel(None)
        self._update_stats()
        self._redraw()

    # ── UI actions ─────────────────────────────────────────────────────────────

    def _add_node_from_ui(self):
        label = self._add_label_var.get().strip()
        if not label:
            return
        node_type = self._add_type_var.get()
        node_id   = f"{node_type}_{label}"
        self.add_node(node_id, label, node_type)
        self._add_label_var.set("")
        self._restart_layout()

    def _restart_layout(self):
        self._stop_simulation()
        # Give velocities a nudge to avoid local minima
        for node in self._nodes.values():
            if not node.pinned:
                node.vx = random.uniform(-2, 2)
                node.vy = random.uniform(-2, 2)
        self._start_simulation()

    def _clear_graph(self):
        self._stop_simulation()
        self._nodes.clear()
        self._edges.clear()
        self._selected_node = None
        self._update_detail_panel(None)
        self._update_stats()
        self._redraw()

    def _seed_demo_graph(self):
        """Load a pre-built demo graph showing ReconX capabilities."""
        self._clear_graph()

        # Core target
        self.add_node("acme.com",      "acme.com",          "target",   {"type": "demo"})
        self.add_node("93.184.216.34", "93.184.216.34",     "ip",       {"isp": "Edgecast"})
        self.add_node("mail.acme.com", "mail.acme.com",     "subdomain")
        self.add_node("dev.acme.com",  "dev.acme.com",      "subdomain")
        self.add_node("api.acme.com",  "api.acme.com",      "subdomain")
        self.add_node("Edgecast",      "Verizon Edgecast",  "isp")
        self.add_node("Cloudflare",    "Cloudflare CDN",    "tech",     {"category": "CDN"})
        self.add_node("WordPress",     "WordPress CMS",     "tech",     {"category": "CMS"})
        self.add_node("GA",            "Google Analytics",  "tech",     {"category": "Analytics"})
        self.add_node("React",         "React.js",          "tech",     {"category": "JS Framework"})
        self.add_node("US",            "Ashburn, VA, US",   "location")
        self.add_node("john@acme.com", "john@acme.com",     "email")
        self.add_node("@john_acme",    "@john_acme",        "username")
        self.add_node("GitHub",        "GitHub",            "platform")
        self.add_node("LinkedIn",      "LinkedIn",          "platform")
        self.add_node("BREACH_2021",   "LinkedIn 2021 Breach","breach", {"records": "700M"})

        # Edges
        self.add_edge("acme.com",      "93.184.216.34", "resolves",    "resolves_to")
        self.add_edge("93.184.216.34", "Edgecast",      "hosted by",   "hosts")
        self.add_edge("93.184.216.34", "US",            "located in",  "located_in")
        self.add_edge("acme.com",      "mail.acme.com", "",            "subdomain_of")
        self.add_edge("acme.com",      "dev.acme.com",  "",            "subdomain_of")
        self.add_edge("acme.com",      "api.acme.com",  "",            "subdomain_of")
        self.add_edge("acme.com",      "Cloudflare",    "CDN",         "uses_tech")
        self.add_edge("acme.com",      "WordPress",     "CMS",         "uses_tech")
        self.add_edge("acme.com",      "GA",            "analytics",   "uses_tech")
        self.add_edge("acme.com",      "React",         "frontend",    "uses_tech")
        self.add_edge("john@acme.com", "acme.com",      "belongs to",  "belongs_to")
        self.add_edge("@john_acme",    "john@acme.com", "same person", "belongs_to")
        self.add_edge("@john_acme",    "GitHub",        "found on",    "found_on")
        self.add_edge("@john_acme",    "LinkedIn",      "found on",    "found_on")
        self.add_edge("john@acme.com", "BREACH_2021",   "in breach",   "breach_of")

        self._restart_layout()

    def _update_stats(self):
        self._stats_label.configure(
            text=(f"Nodes: {len(self._nodes)}  |  "
                  f"Edges: {len(self._edges)}  |  "
                  f"Scroll to zoom  |  Drag nodes  |  Click to inspect")
        )


# ── Utility ────────────────────────────────────────────────────────────────────

def _hex_darken(hex_color: str, factor: float) -> str:
    """Darken a hex color by mixing it with black at `factor` (0–1)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"
