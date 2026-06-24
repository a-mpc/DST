# src/tfg/scenario/loader.py
from datetime import datetime
from owlready2 import Ontology, sync_reasoner_hermit, OwlReadyInconsistentOntologyError
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from tfg.models import Event
import json

CLASS_KEYS = {
  "mission": "Mission",
  "loo": "LineOfOperation",
  "obj": "Objective",
  "dc": "DecisiveCondition",
  "effect": "Effect",
  "action": "Action",
  "task": "Task",
  "unit": "Unit",
  "asset": "Asset"
}

RELATIONS = {
  "LineOfOperation": "hasLineOfOperation",
  "Objective": "hasObjective",
  "DecisiveCondition": "hasDecisiveCondition",
  "Effect": "isSupportedByEffect",
  "Action": "isProducedByAction",
  "Task": "isExecutedByTask",
  "Unit": "isAssignedToUnit",
  "Asset": "usesAsset"
}

DATA_PROPS = {
  "id": "hasId",
  "name": "hasName",
  "start_date": "hasStartDate",
  "end_date": "hasEndDate"
}

class ScenarioElement(BaseModel):
  model_config = ConfigDict(extra="allow")
  id: str
  parent_id: str | None = None
  name: str | None = None
  weight: float = Field(ge=0.0, le=1.0, default=1.0)
  impact: float = Field(ge=0.0, le=1.0, default=0.0)
  depends_on: list[str] = Field(default_factory=list)
  start_date: datetime | None = None
  end_date: datetime | None = None
  critical: bool = False

def load_scenario(directory: str | Path):
  with (Path(directory) / "mission.json").open(encoding="utf-8") as f:
    data = json.load(f)
  scenario = {}
  for json_key, class_name in CLASS_KEYS.items():
    for i, entry in enumerate(data.get(json_key) or [], start=1):
      try:
        scenario.setdefault(class_name, []).append(ScenarioElement(**entry))
      except Exception as e:
        raise ValueError(f"mission.json '{json_key}' entrada {i}: {e}") from e
  return scenario

def flatten_scenario(scenario: dict[str, list[ScenarioElement]]):
  flat = {}
  for row in (r for rows in scenario.values() for r in rows):
    if row.id in flat:
      raise ValueError(f"Entidad duplicada: '{row.id}'.")
    flat[row.id] = row
  return flat

def populate_ontology(onto: Ontology, scenario: dict[str, list[ScenarioElement]], events: list[Event], onto_path: str | Path | None = None):
  individuals = {}
  for class_name, rows in scenario.items():
    for row in rows:
      owl_class = onto[class_name]
      ind = owl_class(row.id)
      for field, prop in DATA_PROPS.items():
        value = getattr(row, field, None)
        if value is not None:
          getattr(ind, prop).append(value)
      individuals[row.id] = ind

  domain_individuals = {individual.name.lower(): individual for individual in onto.OperationalDomain.instances()}
  phase_individuals = {individual.name.lower(): individual for individual in onto.MissionPhase.instances()}

  for class_name, rows in scenario.items():
    hier_prop = RELATIONS.get(class_name)
    for row in rows:
      ind = individuals[row.id]
      if hier_prop and row.parent_id:
        parent = individuals.get(row.parent_id) or onto[row.parent_id]
        getattr(parent, hier_prop).append(ind)
      for tid in row.depends_on:
        ind.dependsOn.append(individuals.get(tid) or onto[tid])

      domain = getattr(row, "domain", None)
      if domain:
        ind.operatesInDomain.append(domain_individuals.get(domain.lower()))
      phase = getattr(row, "phase", None)
      if phase:
        if ind.is_a[0] is onto.Mission:
          ind.missionHasPhase.append(phase_individuals.get(phase.lower()))
        else:
          ind.occursInPhase.append(phase_individuals.get(phase.lower()))

  for event in events:
    ind = onto.Event(event.id)
    ind.hasId.append(event.id)
    description = getattr(event, "description", None)
    if description:
      ind.hasDescription.append(description)
    target = individuals.get(event.targets_asset)
    if target is None:
      raise ValueError(f"El evento '{event.id}' tiene como objetivo un activo no declarado '{event.targets_asset}'.")
    else:
      ind.affectsAsset.append(target)
    for technique in getattr(event, "attack_techniques", None) or []:
      technique_ind = onto[technique] or onto.AttackTechnique(technique)
      ind.implementsTechnique.append(technique_ind)
    phase = getattr(row, "phase", None)
    if phase:
      ind.occursInPhase.append(phase_individuals.get(phase.lower()))

  try:
    sync_reasoner_hermit([onto])
  except OwlReadyInconsistentOntologyError as error:
    raise ValueError("El escenario es logicamente inconsistente segun HermiT.") from error
  inconsistents = list(onto.inconsistent_classes())
  if inconsistents:
    raise ValueError(f"Clases inconsistentes: {[c.name for c in inconsistents]}.")

  if onto_path is not None:
    onto_path = Path(onto_path)
    onto_path.parent.mkdir(parents=True, exist_ok=True)
    onto.save(file=str(onto_path), format="rdfxml")

  return individuals
