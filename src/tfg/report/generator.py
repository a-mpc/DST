# src/tfg/reporting/generator.py
from datetime import datetime
from io import StringIO
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pathlib import Path
from tfg.models import Event
from weasyprint import HTML
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as pyplot
import networkx
import textwrap

TEMPLATE_DIR = Path(__file__).parent / "template"

def generate_report(context: dict, output_path: str | Path, template_name: str = "report.html.j2"):
  output_path = Path(output_path)
  output_path.parent.mkdir(parents=True, exist_ok=True)

  context = {**context}
  context.setdefault("report", {}).setdefault(
    "generated_at",
    datetime.now().strftime("%Y-%m-%d %H:%M")
  )

  env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    undefined=StrictUndefined,
    autoescape=True
  )
  html = env.get_template(template_name).render(**context)

  HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(output_path)
  return output_path

def generate_mission_graph(graph: networkx.DiGraph, event: Event):
  mission = next((n for n, d in graph.nodes(data=True) if d.get("type") == "Mission"), None)
  edges_by_kind = {"hierarchy": [], "dependency": []}
  for u, v, d in graph.edges(data=True):
    edges_by_kind[d.get("kind", "hierarchy")].append((u, v))

  levels = {mission: 0} if mission else {}
  for parent, child in networkx.bfs_edges(graph.edge_subgraph(edges_by_kind["hierarchy"]), mission):
    levels[child] = levels[parent] + 1

  by_level: dict[int, list[str]] = {}
  for node, level in levels.items():
    by_level.setdefault(level, []).append(node)

  hierarchy_graph = graph.edge_subgraph(edges_by_kind["hierarchy"])
  children: dict[str, list[str]] = {}
  for parent, child in networkx.bfs_edges(hierarchy_graph, mission):
      children.setdefault(parent, []).append(child)

  bfs_order = [mission] + [c for _, c in networkx.bfs_edges(hierarchy_graph, mission)]

  widths: dict[str, int] = {}
  for node in reversed(bfs_order):
      kids = children.get(node, [])
      widths[node] = sum(widths[k] for k in kids) if kids else 1

  pos = {mission: (0, 0.0)}
  for node in bfs_order:
      kids = children.get(node, [])
      if not kids:
          continue
      level_x, y_center = pos[node]
      total = widths[node]
      cursor = y_center + (total - 1) / 2 * 0.6
      for k in kids:
          w = widths[k]
          pos[k] = (level_x + 1, cursor - (w - 1) / 2 * 0.6)
          cursor -= w * 0.6

  target_asset = event.targets_asset
  event_edges = []
  x, y = pos[target_asset]
  pos[event.id] = (x + 0.55, y + 0.15)
  event_edges.append((event.id, event.targets_asset))
  event_nodes = [u for u, _ in event_edges]

  ys = [y for _, y in pos.values()]
  y_min, y_max = min(ys), max(ys)
  y_range = y_max - y_min + 2.0
  height = max(y_range * 1.4, 4.0)

  fig, ax = pyplot.subplots(figsize=(13, height))
  ax.set_axis_off()
  ax.set_ylim(y_min - 1.0, y_max + 1.0)
  ax.margins(x=0.1, y=0.2)

  for edges, color in [(edges_by_kind["hierarchy"], "#bdc3c7"), (edges_by_kind["dependency"], "#3498db"), (event_edges, "#c0392b")]:
    if edges:
      networkx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color=color, style="solid", width=1.1, arrows=True, arrowsize=8, ax=ax)

  colors = ["#c0392b" if n in event_nodes else "#34495e" if n in target_asset else "#ecf0f1" for n in pos]
  borders = ["#c0392b" if n in event_nodes else "#34495e" if n in target_asset else "#95a5a6" for n in pos]
  networkx.draw_networkx_nodes(graph, pos, nodelist=list(pos), node_color=colors, edgecolors=borders, linewidths=1.0, node_size=220, ax=ax)

  max_chars = 18
  raw_labels = {n: graph.nodes[n].get("name", n) if n in graph.nodes else n for n in pos}
  labels = {n: textwrap.fill(str(text), width=max_chars) for n, text in raw_labels.items()}
  label_pos = {n: (x, y + 0.2) for n, (x, y) in pos.items()}
  networkx.draw_networkx_labels(graph, label_pos, labels=labels, font_size=8, font_family="Times New Roman", ax=ax)

  buf = StringIO()
  pyplot.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
  pyplot.close(fig)
  return buf.getvalue()
