# src/tfg/recommendator/engine.py
from dataclasses import replace
from tfg.catalog import filter_applicable, filter_by_tactic, filter_in_time
from tfg.evaluator import evaluate
from tfg.models import CIA, Countermeasure, EvaluationResult, Event, RankedCountermeasure
from tfg.recommendator.topsis import rank
import networkx

_EPSILON = 1e-6

def recommend(
    graph: networkx.DiGraph,
    event: Event,
    evaluation: EvaluationResult,
    catalog: list[Countermeasure],
    weights: dict[str, float] | None = None,
    top_k: int = 5,
    phase: str | None = None,
    viability_threshold: float = 0.5
):
  candidates = {}
  for cm in filter_applicable(catalog, event.targets_asset, phase):
    candidates[cm.id] = cm
  candidates = list(candidates.values())
  if not candidates:
    return []
  print(f"Las contramedidas que son aplicables sobre el evento afectado, y en la fase de la misión actual, son: {', '.join(cm.id for cm in candidates)}")

  candidates = filter_in_time(graph, event, candidates)
  if not candidates:
    return []
  print(f"Las contramedidas que se pueden desplegar en el tiempo disponible son: {', '.join(cm.id for cm in candidates)}")

  candidates = filter_by_tactic(event, candidates)
  if not candidates:
    return []
  print(f"Las contramedidas que se pueden aplicar finalmente sobre el evento son: {', '.join(cm.id for cm in candidates)}")

  simulations = []
  for cm in candidates:
    mitigated = _apply_countermeasure(event, cm)
    new_eval = evaluate(graph, mitigated, evaluation.mission_id, viability_threshold)
    viability_gain = max(0.0, new_eval.mission_viability - evaluation.mission_viability)
    mission_rr = max(0.0, evaluation.mission_impact - new_eval.mission_impact)
    force_rr = max(0.0, getattr(evaluation, "force_impact", 0.0) - getattr(new_eval, "force_impact", 0.0))
    simulations.append((cm, new_eval, viability_gain, mission_rr, force_rr))

  simulations = [s for s in simulations if s[2] > _EPSILON or s[3] > _EPSILON or s[4] > _EPSILON]
  if not simulations:
    return []

  criteria = ["cost", "deployment_time", "viability_gain", "mission_impact_reduction", "force_impact_reduction"]
  is_benefit = [False, False, True, True, True]
  ordered_weights = [weights[c] for c in criteria]

  matrix = [[cm.cost, cm.deployment_time, viability_gain, mission_rr, force_rr] for cm, _, viability_gain, mission_rr, force_rr in simulations]
  scores = rank(matrix, ordered_weights, is_benefit)

  ranked = [
    _build_ranked(cm, new_eval, viability_gain, mission_rr, force_rr, score)
    for (cm, new_eval, viability_gain, mission_rr, force_rr), score in zip(simulations, scores)
  ]
  ranked.sort(key=lambda r: r.score, reverse=True)
  return ranked[:top_k]

def _build_ranked(cm, new_eval, viability_gain, mission_rr, force_rr, score):
  base_kwargs = dict(
    countermeasure=cm,
    score=score,
    projected_viability=new_eval.mission_viability,
    viability_gain=viability_gain,
    projected_impact=new_eval.mission_impact,
    impact_reduction=mission_rr
  )
  projected_force_impact = getattr(new_eval, "force_impact", 0.0)
  try:
    return RankedCountermeasure(
      **base_kwargs,
      force_impact_reduction=force_rr,
      projected_force_impact=projected_force_impact
    )
  except TypeError:
    return RankedCountermeasure(**base_kwargs)

def _apply_countermeasure(event: Event, cm: Countermeasure) -> Event:
  if event.targets_asset not in cm.applicable_to:
    return event

  c = event.cia_degradation.confidentiality * (1 - cm.cia_mitigation.confidentiality)
  i = event.cia_degradation.integrity * (1 - cm.cia_mitigation.integrity)
  a = event.cia_degradation.availability * (1 - cm.cia_mitigation.availability)

  mitigated_cia = CIA(max(0.0, c), max(0.0, i), max(0.0, a))
  return replace(event, cia_degradation=mitigated_cia)
