# src/tfg/evaluation/evaluator.py
from tfg.models import EvaluationResult, Event
import networkx

_MISSION = frozenset({"Mission", "LineOfOperation", "Objective", "DecisiveCondition", "Effect", "Action", "Task"})
_FORCE = frozenset({"Unit", "Asset"})

def evaluate(graph: networkx.DiGraph, event: Event, mission_id: str, viability_threshold: float) -> EvaluationResult:
  children = {node: [] for node in graph.nodes}
  dependencies = {node: [] for node in graph.nodes}
  hierarchy = networkx.DiGraph()
  hierarchy.add_nodes_from(graph.nodes)

  for source, target, data in graph.edges(data=True):
    if data.get("kind", "hierarchy") == "hierarchy":
      weight = data.get("weight", 1.0)
      critical = graph.nodes[target].get("critical", False)
      children[source].append((target, weight, critical))
      hierarchy.add_edge(source, target)
    else:
      dependencies[source].append(target)

  node_list = list(networkx.topological_sort(hierarchy))[::-1]

  criticalities = {}
  node_kinds = {}
  for node in graph.nodes:
    attrs = graph.nodes[node]
    if "criticality" in attrs:
      criticalities[node] = float(attrs["criticality"])
    else:
      criticalities[node] = float(attrs.get("criticality", 0.0))
    node_kinds[node] = _classify_node(attrs)

  degradations = {node: 0.0 for node in graph.nodes}
  for node, value in _propagate(event, children, dependencies, node_list, graph.nodes, viability_threshold).items():
    if value > degradations[node]:
      degradations[node] = value

  viability = 1.0 - degradations[mission_id]
  mission_impact, force_impact = _compute_impact(degradations, criticalities, node_kinds)

  return EvaluationResult(
    event_id=event.id,
    mission_id=mission_id,
    mission_viability=viability,
    mission_impact=mission_impact,
    force_impact=force_impact,
    is_viable=viability >= viability_threshold,
    node_degradations=degradations
  )

def _classify_node(attrs: dict) -> str:
  node_type = attrs.get("node_type") or attrs.get("type")
  if node_type:
    if node_type in _MISSION:
      return "mission"
    if node_type in _FORCE:
      return "force"

def _propagate(event: Event, children, dependencies, node_list, nodes, viability_threshold: float) -> dict[str, float]:
  degradations = {node: 0.0 for node in nodes}
  degradations[event.targets_asset] = event.initial_degradation
  dc_nodes = { node for node in nodes if (nodes[node].get("node_type") or nodes[node].get("type")) == "DecisiveCondition" }

  changed = True
  while changed:
    changed = False
    for parent in node_list:
      if not children[parent]:
        continue
      total_weight = sum(weight for _, weight, _ in children[parent])
      if total_weight <= 0:
        continue
      weighted = sum(degradations[child] * weight for child, weight, _ in children[parent]) / total_weight
      critical_degradation = max((degradations[child] for child, _, is_critical in children[parent] if is_critical), default=0.0)
      propagated = max(weighted, critical_degradation)

      if propagated > degradations[parent]:
        degradations[parent] = propagated
        changed = True

    for dependent, targets in dependencies.items():
      for target in targets:
        if degradations[target] > degradations[dependent]:
          degradations[dependent] = degradations[target]
          changed = True

    for node in dc_nodes:
      if degradations[node] < 1.0 and 1.0 - degradations[node] < viability_threshold:
        degradations[node] = 1.0
        changed = True

  return degradations

def _compute_impact(degradations: dict[str, float], criticalities: dict[str, float], node_kinds: dict[str, str]) -> tuple[float, float]:
  mission_contribs = []
  force_contribs = []
  for node, degradation in degradations.items():
    if degradation <= 0:
      continue
    contribution = degradation * criticalities[node]
    if node_kinds[node] == "force":
      force_contribs.append(contribution)
    else:
      mission_contribs.append(contribution)

  mission_impact = min(1.0, max(mission_contribs)) if mission_contribs else 0.0
  force_impact = min(1.0, max(force_contribs)) if force_contribs else 0.0
  return mission_impact, force_impact
