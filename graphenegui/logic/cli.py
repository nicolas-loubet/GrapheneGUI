"""
Modo headless de GrapheneGUI: crear, oxidar, enrollar (CNT), duplicar y
exportar placas de grafeno sin abrir la interfaz gráfica.

Uso:
    graphene-gui-cli -c config.yaml
    graphene-gui-cli -c config.yaml --set plate.factor=1.2 --set export.output_dir=./salida

Ver notas/headless_config_example.yaml para el schema completo.
"""
import argparse
import sys
from pathlib import Path

import yaml

from . import core


def build_plate(cfg):
    try:
        return core.build_plate_from_create(cfg.get("plate", {}))
    except ValueError as e:
        sys.exit(str(e))


def apply_oxidations(plate, cfg):
    for step in cfg.get("oxidation", []):
        try:
            core.apply_oxidation_step(plate, step)
        except ValueError as e:
            sys.exit(str(e))


def apply_cnt(plate, cfg, periodicity_conditions):
    cnt_cfg= cfg.get("cnt", {})
    if not cnt_cfg.get("enabled", False):
        return plate
    vector= cnt_cfg.get("vector")
    try:
        core.validate_cnt_vector(vector)
        core.apply_cnt(plate, vector)
    except ValueError as e:
        sys.exit(str(e))
    print(f"  rolled into CNT (vector={vector})")
    return plate


def apply_reduce_borders(plate, cfg):
    if not cfg.get("reduce_borders", False):
        return plate
    core.reduce_borders(plate)
    print(f"  reduced borders ({len(plate.get_hydrogens_coords())} H atoms added)")
    return plate


def build_atom_types(cfg):
    return core.build_atom_types(cfg)


def run_multiplate(cfg):
    try:
        plates_by_name, plates, duplicates_list, atom_types, periodicity_conditions= core.build_session_from_config(cfg)
    except ValueError as e:
        sys.exit(str(e))
    export_all(plates, duplicates_list, atom_types, cfg, periodicity_conditions)


def build_duplicates(base_plate, cfg):
    """Cada entrada de 'duplicates' crea una nueva placa duplicada de la base
    (no encadena duplicados entre sí, a diferencia de la GUI donde se puede
    duplicar cualquier placa ya creada)."""
    plates= [base_plate]
    duplicates_list= [[], []]
    center= base_plate.get_geometric_center()

    for entry in cfg.get("duplicates", []):
        dx, dy, dz= entry["translation"]
        absolute= entry.get("absolute", False)
        translation= core.compute_duplicate_translation(dx, dy, dz, absolute, center)
        plates.append(base_plate.duplicate(translation))
        core.register_duplicate(duplicates_list, len(plates), 1)
        print(f"  duplicate added (translation={entry['translation']}, absolute={absolute})")

    return plates, duplicates_list


def export_all(plates, duplicates_list, atom_types, cfg, periodicity_conditions):
    export_cfg= cfg.get("export", {})
    formats= export_cfg.get("formats", ["mol2"])
    output_dir= Path(export_cfg.get("output_dir", "."))
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name= export_cfg.get("name", "graphene")

    for fmt in formats:
        file_name= str(output_dir / f"{base_name}.{fmt}")
        core.export_plates(file_name, plates, periodicity_conditions,
                            atom_types=atom_types, duplicates_list=duplicates_list)
        print(f"  exported {file_name}")


def _parse_overrides(raw_overrides):
    """--set plate.factor=1.2 -> {'plate': {'factor': 1.2}}"""
    overrides= {}
    for item in raw_overrides:
        key, sep, value= item.partition("=")
        if not sep:
            sys.exit(f"Invalid --set value (expected section.field=value): {item}")
        try:
            value= yaml.safe_load(value)
        except yaml.YAMLError:
            pass
        section, _, field= key.partition(".")
        overrides.setdefault(section, {})[field]= value
    return overrides


def _deep_merge(base, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key]= value
    return base


def load_config(config_path, raw_overrides):
    cfg= {}
    if config_path:
        with open(config_path) as f:
            cfg= yaml.safe_load(f) or {}
    return _deep_merge(cfg, _parse_overrides(raw_overrides))


def parse_args(argv=None):
    parser= argparse.ArgumentParser(
        description="GrapheneGUI headless: crear/oxidar/exportar placas de grafeno sin interfaz gráfica.")
    parser.add_argument("-c", "--config", help="Archivo YAML de configuración")
    parser.add_argument("--set", action="append", default=[], metavar="section.field=value",
                         help="Override puntual sobre el config, ej: --set plate.factor=1.2 (repetible)")
    return parser.parse_args(argv)


def main(argv=None):
    args= parse_args(argv)
    cfg= load_config(args.config, args.set)

    if not cfg:
        sys.exit("No config given. Use -c config.yaml and/or --set section.field=value")

    if "plates" in cfg:
        run_multiplate(cfg)
        print("Done.")
        return

    # ---- schema plano (compatibilidad hacia atrás, sin cambios) ----
    if cfg.get("reduce_borders", False) and cfg.get("cnt", {}).get("enabled", False):
        sys.exit("reduce_borders and cnt are mutually exclusive: can't roll a CNT after "
                  "adding border hydrogens (same restriction as the GUI)")

    plate= build_plate(cfg)

    periodicity_conditions= [
        cfg.get("plate", {}).get("periodic_boundary_x", False),
        cfg.get("plate", {}).get("periodic_boundary_y", False),
    ]

    apply_oxidations(plate, cfg)
    apply_reduce_borders(plate, cfg)
    apply_cnt(plate, cfg, periodicity_conditions)
    atom_types= build_atom_types(cfg)
    plates, duplicates_list= build_duplicates(plate, cfg)
    export_all(plates, duplicates_list, atom_types, cfg, periodicity_conditions)

    print("Done.")


if __name__ == "__main__":
    main()
