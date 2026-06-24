# src/tfg/ontology/loader.py
from owlready2 import get_ontology, Ontology
from pathlib import Path

def load_ontology(path: str | Path) -> Ontology:
  path = Path(path)
  return get_ontology(path.resolve().as_uri()).load()
