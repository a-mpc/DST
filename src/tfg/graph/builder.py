# src/cyberdef/graph/builder.py
from owlready2 import Ontology
from pathlib import Path
from tfg.models import Event
from tfg.scenario import ScenarioElement, flatten_scenario, populate_ontology
from tfg.scenario.loader import RELATIONS
import networkx


def build(onto: Ontology, scenario: dict[str, list[ScenarioElement]], events: list[Event], onto_path: str | Path) -> networkx.DiGraph:
  individuals = populate_ontology(onto, scenario, events, onto_path=onto_path)
  graph = networkx.DiGraph()
  flat = flatten_scenario(scenario)

  for node_id, ind in individuals.items():
    row = flat[node_id]
    graph.add_node(
      node_id,
      type=ind.is_a[0].name,
      name=row.name or node_id,
      weight=row.weight,
      impact=row.impact,
      start_date=row.start_date,
      end_date=row.end_date,
      critical=row.critical,
      **(row.model_extra or {})
    )

  for class_name, rows in scenario.items():
    hier_prop = RELATIONS.get(class_name)
    for row in rows:
      if hier_prop and row.parent_id:
        graph.add_edge(row.parent_id, row.id, rel=hier_prop, weight=row.weight, kind="hierarchy")
      for tid in row.depends_on:
        if tid in graph:
          graph.add_edge(row.id, tid, rel="dependsOn", weight=1.0, kind="dependency")

  return graph
