# src/tfg/catalog/loader.py
from datetime import datetime, timezone
from pathlib import Path
from tfg.models import CIA, Countermeasure, Event
import json
import networkx

def load_catalog(path: str | Path) -> list[Countermeasure]:
  path = Path(path)
  with path.open(encoding="utf-8") as file:
    data = json.load(file)
  return [_parse(item) for item in data]

def filter_applicable(catalog: list[Countermeasure], asset_id: str, phase: str | None = None) -> list[Countermeasure]:
  result = []
  for cm in catalog:
    if cm.applicable_to and asset_id not in cm.applicable_to:
      continue
    if phase and cm.applicable_in_phases and phase not in cm.applicable_in_phases:
      continue
    result.append(cm)
  return result

def filter_in_time(graph: networkx.DiGraph, event: Event, candidates: list[Countermeasure]) -> list[Countermeasure]:
  hierarchy_edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get("kind", "hierarchy") == "hierarchy"]
  hierarchy = graph.edge_subgraph(hierarchy_edges)

  deadlines = []
  ancestors = networkx.ancestors(hierarchy, event.targets_asset)
  tasks = [a for a in ancestors if graph.nodes[a].get("type") == "Task"]
  tasks_with_end = [t for t in tasks if graph.nodes[t].get("end_date") is not None]
  if tasks_with_end:
    deadlines.append(min(graph.nodes[t]["end_date"] for t in tasks_with_end))

  if not deadlines:
    return candidates

  deadline = min(deadlines)
  if deadline.tzinfo is None:
    deadline = deadline.replace(tzinfo=timezone.utc)

  now = datetime.now(timezone.utc)
  available_hours = (deadline - now).total_seconds() / 3600

  return [cm for cm in candidates if cm.deployment_time <= available_hours]

def filter_by_tactic(event: Event, candidates: list[Countermeasure]) -> list[Countermeasure]:
  return [cm for cm in candidates if any(technique in cm.counters_attack_techniques for technique in event.attack_techniques)]

def _parse(item: dict) -> Countermeasure:
  cia = item.get("cia_mitigation", {})
  return Countermeasure(
    id=item["id"],
    name=item["name"],
    description=item.get("description", ""),
    cost=float(item["cost"]),
    deployment_time=float(item.get("deployment_time", 0.0)),
    cia_mitigation=CIA(
      confidentiality=float(cia.get("confidentiality", 0.0)),
      integrity=float(cia.get("integrity", 0.0)),
      availability=float(cia.get("availability", 0.0))
    ),
    counters_attack_techniques=item.get("counters_attack_techniques", []),
    applicable_to=tuple(item.get("applicable_to", ["Asset"])),
    applicable_in_phases=tuple(item.get("applicable_in_phases", []))
  )
