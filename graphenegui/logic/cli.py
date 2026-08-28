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


def build_plate_from_create(create_cfg):
    """El mismo cálculo que build_plate(), pero recibiendo directamente el dict
    'create' de una entrada de 'plates' (schema multi-placa, Etapa 1) en vez de
    todo el cfg. Comparten exactamente la misma lógica."""
    width= create_cfg.get("width", 100)      # Å
    height= create_cfg.get("height", 100)    # Å
    factor= create_cfg.get("factor", 1.0)
    center= create_cfg.get("center", [0, 0, 0])  # Å
    periodic_x= create_cfg.get("periodic_boundary_x", False)

    n_x, n_y= core.compute_plate_grid(width, height, factor)
    fits, max_atoms= core.check_plate_size(n_x, n_y)
    if not fits:
        sys.exit(f"Plate too large ({max_atoms} atom names available in the naming scheme). Reduce width/height.")

    center_x_nm, center_y_nm, center_z_nm= [c / 10 for c in center]
    plate= Graphene.create_from_params(n_x, n_y, center_x_nm, center_y_nm, center_z_nm, factor, periodic_x)
    print(f"Plate built: {n_x}x{n_y} ({plate.get_number_atoms()} atoms)")
    return plate


def build_plate(cfg):
    return build_plate_from_create(cfg.get("plate", {}))


def _validate_cnt_vector(vector):
    if not vector or len(vector) != 2 or (vector[0] == 0 and vector[1] == 0):
        sys.exit("cnt vector is missing or invalid (expected [x, y], not [0, 0])")


def apply_oxidation_step(plate, step):
    """Un solo step de oxidación (mode: soft o hard). Compartido entre el schema
    plano (apply_oxidations) y el multi-placa (apply_step)."""
    mode= step.get("mode", "soft")

    if mode == "hard":
        oxides= step.get("oxides")
        if not oxides:
            sys.exit("oxidation step with mode: hard needs a non-empty 'oxides' list")
        # cada entrada es [x, y, z, type] en Å (mismas unidades que el resto del
        # config); se convierte a nm, que es lo que usa Graphene internamente.
        oxide_atoms= [(x/10, y/10, z/10, t) for x, y, z, t in oxides]
        done= core.apply_oxidation_explicit(plate, oxide_atoms)
        print(f"  oxidized {done} sites (hard replica, {len(oxides)} oxide atoms)")
        return

    if mode != "soft":
        sys.exit(f"Unknown oxidation mode: {mode!r} (expected 'soft' or 'hard')")

    z_mode_map= {"+z": 0, "-z": 1, "random": 2}
    expr= step.get("expression", "")
    prob_oh= step.get("prob_oh", 100)
    fraction= step.get("fraction", 1.0)
    z_mode= z_mode_map.get(step.get("z_mode", "random"), 2)

    selected= core.select_atoms(plate, expr, fraction, z_mode, prob_oh)
    if not selected:
        print(f"  oxidation step skipped (nothing matched): {expr!r}")
        return
    done= core.apply_oxidation(plate, selected, z_mode, prob_oh)
    print(f"  oxidized {done} sites (expression: {expr!r})")


def apply_oxidations(plate, cfg):
    for step in cfg.get("oxidation", []):
        apply_oxidation_step(plate, step)


def apply_cnt(plate, cfg, periodicity_conditions):
    cnt_cfg= cfg.get("cnt", {})
    if not cnt_cfg.get("enabled", False):
        return plate
    vector= cnt_cfg.get("vector")
    _validate_cnt_vector(vector)
    core.apply_cnt(plate, vector)
    print(f"  rolled into CNT (vector={vector})")
    return plate


def apply_reduce_borders(plate, cfg):
    if not cfg.get("reduce_borders", False):
        return plate
    core.reduce_borders(plate)
    print(f"  reduced borders ({len(plate.get_hydrogens_coords())} H atoms added)")
    return plate


# ================================
# Schema multi-placa (Etapa 8) — plates: [...] con steps ordenados por placa
# ================================

def apply_oxidation_removed_step(plate, step):
    x, y, z, oxide_type= step["oxide"]
    x, y, z= x/10, y/10, z/10  # Å -> nm
    for ox in plate.get_oxide_coords():
        if ox[3] == oxide_type and abs(ox[0]-x) < 1e-6 and abs(ox[1]-y) < 1e-6 and abs(ox[2]-z) < 1e-6:
            plate.remove_atom_oxide(ox)
            print(f"  removed oxide atom ({oxide_type} at {step['oxide'][:3]})")
            return
    sys.exit(f"oxidation_removed step: no matching oxide atom found at {step['oxide']}")

def apply_step(plate, step):
    """Un step de la secuencia ordenada de una placa (schema multi-placa)."""
    step_type= step.get("type")
    if step_type == "oxidation":
        apply_oxidation_step(plate, step)
    elif step_type == "oxidation_removed":
        apply_oxidation_removed_step(plate, step)
    elif step_type == "oxidation_cleared":
        removed= plate.remove_oxides()
        print(f"  cleared all oxidation ({len(removed)} oxide atoms removed)")
    elif step_type == "reduce_borders":
        core.reduce_borders(plate)
        print(f"  reduced borders ({len(plate.get_hydrogens_coords())} H atoms added)")
    elif step_type == "cnt":
        vector= step.get("vector")
        _validate_cnt_vector(vector)
        core.apply_cnt(plate, vector)
        print(f"  rolled into CNT (vector={vector})")
    else:
        sys.exit(f"Unknown step type: {step_type!r}")

def validate_steps(plate_name, steps):
    """Mismas restricciones que la GUI: reduce_borders y cnt son excluyentes entre
    sí, y una vez enrollada en CNT no se puede seguir editando la placa (en la GUI
    esto pasa porque buttons_that_depend_of_having_a_plate(False) deshabilita todo
    después de aplicar CNT)."""
    types= [s.get("type") for s in steps]
    if "reduce_borders" in types and "cnt" in types:
        sys.exit(f"plate {plate_name!r}: reduce_borders and cnt are mutually exclusive "
                  "(same restriction as the GUI)")
    if "cnt" in types and types.index("cnt") != len(types) - 1:
        sys.exit(f"plate {plate_name!r}: 'cnt' must be the last step (same restriction "
                  "as the GUI: further edits are disabled after rolling into a CNT)")

def build_duplicates_multi(plates_by_name, cfg):
    """Como build_duplicates(), pero 'source' referencia cualquier placa ya
    construida por nombre, no siempre 'la' placa base."""
    order= list(plates_by_name.keys())
    all_plates= [plates_by_name[name] for name in order]
    name_to_position= {name: i for i, name in enumerate(order)}

    duplicates_list= [[], []]
    for entry in cfg.get("duplicates", []):
        source_name= entry["source"]
        if source_name not in plates_by_name:
            sys.exit(f"duplicates: unknown source plate {source_name!r}")
        source_plate= plates_by_name[source_name]
        dx, dy, dz= entry["translation"]
        absolute= entry.get("absolute", False)
        translation= core.compute_duplicate_translation(dx, dy, dz, absolute, source_plate.get_geometric_center())
        all_plates.append(source_plate.duplicate(translation))
        duplicates_list[0].append(len(all_plates))
        duplicates_list[1].append(name_to_position[source_name] + 1)
        print(f"  duplicate of {source_name!r} added (translation={entry['translation']}, absolute={absolute})")

    return all_plates, duplicates_list

def run_multiplate(cfg):
    plates_cfg= cfg.get("plates", [])
    if not plates_cfg:
        sys.exit("'plates' is present but empty — nothing to build")

    # Nota: periodic_boundary_x/y vive dentro de cada placa (create), pero
    # export/checkBounds solo soportan UNA periodicidad global para todo el
    # sistema (igual que main_window.periodicity_conditions en la GUI). Se toma
    # la de la PRIMERA placa. Si esto no te alcanza, avisar para revisarlo.
    first_create= plates_cfg[0].get("create", {})
    periodicity_conditions= [
        first_create.get("periodic_boundary_x", False),
        first_create.get("periodic_boundary_y", False),
    ]

    plates_by_name= {}
    for plate_cfg in plates_cfg:
        name= plate_cfg.get("name")
        if not name:
            sys.exit("Every entry in 'plates' needs a 'name'")
        if name in plates_by_name:
            sys.exit(f"Duplicate plate name in config: {name!r}")

        plate= build_plate_from_create(plate_cfg.get("create", {}))
        plates_by_name[name]= plate

        steps= plate_cfg.get("steps", [])
        validate_steps(name, steps)
        for step in steps:
            apply_step(plate, step)

    plates, duplicates_list= build_duplicates_multi(plates_by_name, cfg)
    atom_types= build_atom_types(cfg)
    export_all(plates, duplicates_list, atom_types, cfg, periodicity_conditions)


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
