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

from .graphene import Graphene
from . import core


def build_plate(cfg):
    plate_cfg= cfg.get("plate", {})
    width= plate_cfg.get("width", 100)      # Å
    height= plate_cfg.get("height", 100)    # Å
    factor= plate_cfg.get("factor", 1.0)
    center= plate_cfg.get("center", [0, 0, 0])  # Å
    periodic_x= plate_cfg.get("periodic_boundary_x", False)

    n_x, n_y= core.compute_plate_grid(width, height, factor)
    fits, max_atoms= core.check_plate_size(n_x, n_y)
    if not fits:
        sys.exit(f"Plate too large ({max_atoms} atom names available in the naming scheme). Reduce width/height.")

    center_x_nm, center_y_nm, center_z_nm= [c / 10 for c in center]
    plate= Graphene.create_from_params(n_x, n_y, center_x_nm, center_y_nm, center_z_nm, factor, periodic_x)
    print(f"Plate built: {n_x}x{n_y} ({plate.get_number_atoms()} atoms)")
    return plate


def apply_oxidations(plate, cfg):
    z_mode_map= {"+z": 0, "-z": 1, "random": 2}
    for step in cfg.get("oxidation", []):
        expr= step.get("expression", "")
        prob_oh= step.get("prob_oh", 100)
        fraction= step.get("fraction", 1.0)
        z_mode= z_mode_map.get(step.get("z_mode", "random"), 2)

        selected= core.select_atoms(plate, expr, fraction, z_mode, prob_oh)
        if not selected:
            print(f"  oxidation step skipped (nothing matched): {expr!r}")
            continue
        done= core.apply_oxidation(plate, selected, z_mode, prob_oh)
        print(f"  oxidized {done} sites (expression: {expr!r})")


def apply_cnt(plate, cfg, periodicity_conditions):
    cnt_cfg= cfg.get("cnt", {})
    if not cnt_cfg.get("enabled", False):
        return plate
    vector= cnt_cfg.get("vector")
    if not vector or len(vector) != 2 or (vector[0] == 0 and vector[1] == 0):
        sys.exit("cnt.enabled is true but cnt.vector is missing or invalid (expected [x, y], not [0, 0])")
    core.apply_cnt(plate, vector)
    print(f"  rolled into CNT (vector={vector})")
    return plate


def build_atom_types(cfg):
    atom_types= {}
    for entry in cfg.get("atom_types", []):
        atom_types[entry["name"]]= {"epsilon": entry["epsilon"], "sigma": entry["sigma"]}
    return atom_types


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

    plate= build_plate(cfg)

    periodicity_conditions= [
        cfg.get("plate", {}).get("periodic_boundary_x", False),
        cfg.get("plate", {}).get("periodic_boundary_y", False),
    ]

    apply_oxidations(plate, cfg)
    apply_cnt(plate, cfg, periodicity_conditions)
    atom_types= build_atom_types(cfg)
    plates, duplicates_list= build_duplicates(plate, cfg)
    export_all(plates, duplicates_list, atom_types, cfg, periodicity_conditions)

    print("Done.")


if __name__ == "__main__":
    main()
