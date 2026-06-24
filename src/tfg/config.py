# src/tfg/config.py
from pydantic import BaseModel, Field
from pathlib import Path

class TopsisWeights(BaseModel):
  cost: float = 0.10
  deployment_time: float = 0.10
  viability_gain: float = 0.35
  mission_impact_reduction: float = 0.25
  force_impact_reduction: float = 0.20

class Config(BaseModel):
  ontology_path: Path = Path("data/ontology/mission.owx")
  scenarios_root: Path = Path("data/scenarios")
  output_dir: Path = Path("output")

  viability_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
  top_k: int = Field(default=6, ge=1)
  topsis_weights: TopsisWeights = TopsisWeights()
  tool_version: str = "1.0"

  @classmethod
  def read(cls, config_path: Path) -> "Config":
    return cls.model_validate_json(Path(config_path).read_text(encoding="utf-8"))
