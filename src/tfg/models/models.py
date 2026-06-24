# src/tfg/models/models.py
from dataclasses import dataclass
from enum import Enum

class NodeType(str, Enum):
  MISSION = "Mission"
  LOO = "LineOfOperation"
  OBJECTIVE = "Objective"
  DC = "DecisiveCondition"
  EFFECT = "Effect"
  ACTION = "Action"
  TASK = "Task"
  UNIT = "Unit"
  ASSET = "Asset"

@dataclass(frozen=True)
class AttackTechnique:
  id: str
  name: str
  tactic: str

@dataclass
class CIA:
  confidentiality: float
  integrity: float
  availability: float

  @property
  def aggregate(self) -> float:
    c = self.confidentiality
    i = self.integrity
    a = self.availability
    return 1.0 - (1.0 - c) * (1.0 - i) * (1.0 - a)

@dataclass(frozen=True)
class Countermeasure:
  id: str
  name: str
  description: str
  cost: float
  deployment_time: float
  cia_mitigation: CIA
  applicable_to: list[str]
  applicable_in_phases: list[str]
  counters_attack_techniques: list[str]

@dataclass(frozen=True)
class EntityNode:
  id: str
  parent_id: str
  type: NodeType
  name: str
  weight: float
  impact: float
  properties: dict

@dataclass
class EvaluationResult:
  event_id: str
  mission_id: str
  mission_viability: float
  mission_impact: float
  force_impact: float
  is_viable: bool
  node_degradations: dict[str, float]

@dataclass(frozen=True)
class Event:
  id: str
  description: str
  targets_asset: str
  cia_degradation: CIA
  attack_techniques: list[str]
  timestamp: str

  @property
  def initial_degradation(self) -> float:
    return self.cia_degradation.aggregate

@dataclass
class RankedCountermeasure:
  countermeasure: Countermeasure
  score: float
  projected_viability: float
  viability_gain: float
  projected_impact: float
  impact_reduction: float
  projected_force_impact: float
  force_impact_reduction: float
