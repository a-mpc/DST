# src/tfg/pipeline.py
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tfg.catalog import load_catalog
from tfg.config import Config
from tfg.evaluator import evaluate
from tfg.graph import build as build_graph
from tfg.models import EvaluationResult, Event, RankedCountermeasure
from tfg.ontology import load_ontology
from tfg.recommendator import recommend
from tfg.report import generate_mission_graph, generate_report
from tfg.scenario import load_scenario
from typing import Any
import networkx as nx
import re

ORDER = {
  "Asset": 0,
  "Unit": 1,
  "Task": 2,
  "Action": 3,
  "Effect": 4,
  "DecisiveCondition": 5,
  "Objective": 6,
  "LineOfOperation": 7,
  "Mission": 8
}

def run_pipeline(config: Config, scenario_dir: Path, scenario_name: str, events: list[Event], report_filename: str | None = None) -> None:
  print(f"Cargando ontología...")
  onto = load_ontology(config.ontology_path)
  print(f"Cargando escenario...")
  scenario = load_scenario(scenario_dir)
  populated_owl_path = scenario_dir / "populated_ontology.owl"
  graph = build_graph(onto, scenario, events, populated_owl_path)
  print(f"Ontología poblada guardada.")

  print(f"Cargando catálogo de contramedidas...")
  catalog_path = scenario_dir / "countermeasures" / "catalog.json"
  catalog = load_catalog(catalog_path)

  mission_id = scenario["Mission"][0].id
  phase = scenario["Mission"][0].phase

  config.output_dir.mkdir(parents=True, exist_ok=True)
  report_dir = config.output_dir / scenario_name
  report_dir.mkdir(parents=True, exist_ok=True)

  for ev in events:
    print(f"\nProcesando evento {ev.id}...")

    print(f"  Evaluando escenario...")
    evaluation = evaluate(graph, ev, mission_id, config.viability_threshold)

    print(f"  Generando recomendaciones...")
    recommendations = recommend(
      graph=graph,
      event=ev,
      evaluation=evaluation,
      catalog=catalog,
      top_k=config.top_k,
      weights=config.topsis_weights.model_dump(),
      phase=phase,
      viability_threshold=config.viability_threshold
    )

    filename = report_filename or f"report_{re.sub(r"[^A-Za-z0-9._-]", "_", ev.id)}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"
    output_path = report_dir / filename

    print(f"  Generando informe...")
    report_context = _build_report_context(
      config, scenario_dir, catalog_path, graph, ev, evaluation, recommendations
    )
    generate_report(report_context, output_path)

def _build_report_context(
  config: Config, scenario_dir: Path, catalog_path: Path, graph: nx.DiGraph,
  event: Event, evaluation: EvaluationResult, recommendations: list[RankedCountermeasure]
) -> dict[str, Any]:
  mission_id = evaluation.mission_id
  mission_name = graph.nodes[mission_id].get("name", mission_id)

  return {
    "report": {
      "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
      "version": config.tool_version
    },
    "mission": { "id": mission_id, "name": mission_name },
    "event": _event_to_dict(event, graph),
    "evaluation": {
      "mission_viability": evaluation.mission_viability,
      "mission_impact": evaluation.mission_impact,
      "force_impact": evaluation.force_impact,
      "is_viable": evaluation.is_viable,
      "node_degradations": evaluation.node_degradations,
      "node_degradations_ordered": _order_node_degradations(graph, evaluation)
    },
    "recommendations": [_recommendations_to_dict(r) for r in recommendations],
    "figures": {
        "degradation_graph": generate_mission_graph(graph, event),
    },
    "config": {
      "viability_threshold": config.viability_threshold,
      "ranking_algorithm": "TOPSIS",
      "topsis_weights": config.topsis_weights,
      "ontology_path": str(config.ontology_path),
      "scenario_path": str(scenario_dir) + "/mission.json",
      "catalog_path": str(catalog_path)
    },
  }

def _order_node_degradations(graph: nx.DiGraph, evaluation: EvaluationResult) -> list[dict]:
  rows = []
  for node_id, degradation in evaluation.node_degradations.items():
    if degradation <= 0:
      continue
    data = graph.nodes[node_id]
    rows.append({
      "node_id": node_id,
      "name": data.get("name", node_id),
      "type": data.get("type", "Unknown"),
      "degradation": degradation
    })
  rows.sort(key=lambda r:( ORDER.get(r["type"]), -r["degradation"]))
  return rows

def _event_to_dict(ev: Event, graph: nx.DiGraph):
  target_name = graph.nodes[ev.targets_asset].get("name", ev.targets_asset)
  return {
    "id": ev.id,
    "description": ev.description,
    "targets_asset": ev.targets_asset,
    "target_asset_name": target_name,
    "cia_degradation": {
      "confidentiality": ev.cia_degradation.confidentiality,
      "integrity": ev.cia_degradation.integrity,
      "availability": ev.cia_degradation.availability
    },
    "attack_techniques": [t for t in ev.attack_techniques],
    "timestamp": ev.timestamp or "n/a"
  }

def _recommendations_to_dict(r: RankedCountermeasure):
  cm = r.countermeasure
  return {
    "countermeasure": {
      "id": cm.id,
      "name": cm.name,
      "description": cm.description,
      "cost": cm.cost,
      "deployment_time": cm.deployment_time,
      "applicable_to": list(cm.applicable_to),
      "phase": ", ".join(cm.applicable_in_phases) if cm.applicable_in_phases else None
    },
    "score": r.score,
    "projected_viability": r.projected_viability,
    "viability_gain": r.viability_gain,
    "projected_impact": r.projected_impact,
    "impact_reduction": r.impact_reduction,
    "projected_force_impact": r.projected_force_impact,
    "force_impact_reduction": r.force_impact_reduction
  }
