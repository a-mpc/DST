# src/tfg/main.py
from tfg.config import Config
from tfg.models import CIA, Event
from tfg.pipeline import run_pipeline
from tfg.scenario import load_events
import argparse
import sys

def main(argv: list[str] | None = None) -> int:
  args = _parse_args(argv)

  config_file = args.config
  if not config_file:
    print(f"Archivo de configuración no encontrado: {config_file}")
    return 1

  config = Config.read(config_file)

  scenario_dir = config.scenarios_root / args.scenario
  if not scenario_dir.is_dir():
    print(f"Escenario no encontrado: {scenario_dir}")
    return 1
  
  events_file = scenario_dir / "events.json"
  if not events_file.exists():
    print(f"Falta incluir un events.json en {scenario_dir}")
    return 1

  meta = load_events(events_file)
  events = [_parse_event(i) for i in meta.get("events", [])]
  if not events:
    print("No hay eventos en el escenario.")
    return 1

  print(f"Ejecutando escenario {args.scenario}...")
  print(f"  {meta.get('name', '(Sin nombre)')}")
  print(f"  Eventos: {len(events)}\n")

  run_pipeline(config, scenario_dir, args.scenario, events)

  print(f"Escenario {args.scenario} evaluado.")
  print(f"   El informe está disponible en: {(config.output_dir / args.scenario).resolve()}")
  return 0

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    prog="tfg",
    description="Ejecuta un escenario y genera un informe evaluando la misión y recomendando contramedidas",
  )
  parser.add_argument(
    "scenario",
    help="Nombre del escenario a ejecutar (carpeta dentro de /data/scenarios)",
  )
  parser.add_argument(
    "--config",
    default="config.json",
    help="Ruta al archivo de configuración (por defecto: config.json)",
  )
  return parser.parse_args(argv)

def _parse_event(data: dict) -> Event:
  cia = data.get("cia_degradation", {})
  return Event(
    id=data["id"],
    description=data.get("description", ""),
    targets_asset=data["targets_asset"],
    cia_degradation=CIA(
      confidentiality=float(cia.get("confidentiality", 0.0)),
      integrity=float(cia.get("integrity", 0.0)),
      availability=float(cia.get("availability", 0.0)),
    ),
    attack_techniques=[technique["id"] for technique in data["attack_techniques"] if technique.get("id")],
    timestamp=data.get("timestamp", "")
  )

if __name__ == "__main__":
  sys.exit(main())
