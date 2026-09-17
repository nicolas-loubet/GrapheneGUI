"""
Lógica pura del proyecto (sin dependencias de Qt): todo lo que no necesita
una main_window ni widgets vive acá. Es el módulo que comparten la GUI
(a través de functionalities.py) y el futuro modo headless (cli.py).
"""
import random
import math
import re
import numpy as np
from .graphene import Graphene, generatePatterns, DEFAULT_CARBON_TYPE
from .import_formats import readGRO, readXYZ, readPDB, readMOL2
from .export_formats import writeGRO, writeXYZ, writeTOP, writePDB, writeMOL2, ATOM_PARAMS_TOP
from .plate_registry import PlateRegistry


# ================================
# Duplicados (bookkeeping de placas)
# ================================

# register_duplicate sigue viva: la usa cli.py (build_duplicates) para el
# schema plano viejo (bloque 'duplicates:' del YAML, la rama de
# compatibilidad hacia atrás explícita en main() -- "schema plano, sin
# cambios"). NO es el mismo camino que la GUI: main_window/functionalities
# usan graphenegui/logic/plate_registry.py (PlateRegistry) para bookkeeping
# de duplicados, que identifica placas por un id estable en vez de por
# índice, y DERIVA si dos placas siguen siendo copias idénticas comparando
# átomos en vez de mantener un flag que hay que invalidar a mano. Pero el
# CLI headless en su modo plano (no 'plates: [...]') sigue con el formato
# viejo [lista_de_duplicados, lista_de_originales] por índice, y esta
# función es la única pieza de ese mecanismo que seguía haciendo falta --
# manage_duplicates_for_deletion (borrado de una placa reparentando a sus
# hijos) y resolve_duplicate_root (seguir la cadena hasta el root) no tenían
# ningún caller real, confirmado con grep sobre todo el repo -- se
# borraron acá. Los tests que las ejercitaban directamente (test_core.py,
# TestDuplicatesBookkeeping) se podaron junto con esto.
def register_duplicate(duplicates_list, new_plate_index, root_index):
    """duplicates_list es [lista_de_duplicados, lista_de_originales] (mismo
    formato que usaba main_window.plates_corresponding_to_duplicates antes
    de PlateRegistry)."""
    duplicates_list[0].append(new_plate_index)
    duplicates_list[1].append(root_index)


def compute_duplicate_translation(delta_x, delta_y, delta_z, absolute, plate_center):
    """delta_* vienen en Å (como los spinboxes de la GUI); se devuelven en nm."""
    translation= [delta_x*.1, delta_y*.1, delta_z*.1]
    if absolute:
        for i in range(3):
            translation[i] -= plate_center[i]
    return translation


# ================================
# Oxidación
# ================================

# Regex con \b (límite de palabra) para envolver and/or/not con espacios antes
# de eval() -- reemplaza el .replace() ingenuo de antes, que corrompía CUALQUIER
# aparición de esas 3 letras dentro de otra palabra (ej. "constant" -> "const
# and t") y explotaba con SyntaxError si el texto era EXACTAMENTE "and"/"or"/
# "not" sin nada más -- que es justo lo que pasa en el medio de tipear "not (...)"
# en entryVMD, porque evalúa en cada tecla (textChanged), no solo al terminar.
_BOOLEAN_KEYWORD_RE= re.compile(r"\b(and|or|not)\b")

def evaluate_condition(x, y, z, i_atom, expr):
    if expr.strip() == "": return True
    expr= _BOOLEAN_KEYWORD_RE.sub(r" \1 ", expr)
    return eval(expr, {'x': x, 'y': y, 'z': z, 'index': i_atom, 'and': lambda a, b: a and b, 'or': lambda a, b: a or b, 'not': lambda x: not x})

def get_list_carbons_in_expr(plate, expr):
    list_carbons_in_expression= []
    for coord in plate.get_carbon_coords():
        x, y, z, _, i_atom= coord[:5]
        x, y, z= x * 10, y * 10, z * 10
        if evaluate_condition(x, y, z, i_atom, expr):
            list_carbons_in_expression.append(coord)
    return list_carbons_in_expression

def select_atoms(plate, expr, fraction_oxidation, z_mode, prob_oh):
    """Devuelve la lista de carbonos a oxidar según la expresión y el % pedido,
    o None si la expresión es inválida o no hay nada para oxidar."""
    if not expr: expr= ""

    try:
        list_carbons_in_expression= get_list_carbons_in_expr(plate, expr)
        number_total_carbons= len(list_carbons_in_expression)
        number_oxidations_desired= int(number_total_carbons * fraction_oxidation)

        if number_total_carbons == 0 or number_oxidations_desired == 0: return None

        plate_try= plate.duplicate([0, 0, 0])
        plate_try.add_oxydation_to_list_of_carbon(list_carbons_in_expression, z_mode, prob_oh)
        max_theorical_oxidations= plate_try.get_oxide_count()

        if max_theorical_oxidations <= number_oxidations_desired:
            selected_atoms= list_carbons_in_expression
        else:
            correction_factor= int(fraction_oxidation * prob_oh * number_oxidations_desired / 200)
            selected_atoms= random.sample(list_carbons_in_expression, min(number_oxidations_desired + correction_factor, number_total_carbons))

        print(" "*70, end="\r")
        return selected_atoms

    except Exception as e:
        print("Not valid expression, exc=", e, " "*20, end="\r")
        return None

def apply_oxidation(plate, list_carbons, z_mode, prob_oh):
    """Aplica la oxidación sobre la placa y devuelve la cantidad de oxidaciones hechas."""
    if not list_carbons: return 0
    return plate.add_oxydation_to_list_of_carbon(list_carbons, z_mode, prob_oh)

def apply_oxidation_explicit(plate, oxide_atoms):
    """Modo 'hard replica': agrega exactamente estos átomos de óxido ya resueltos
    (posición + tipo), SIN volver a elegir al azar OO vs OE como hace
    add_oxydation_to_list_of_carbon. Pensado para reproducir una sesión real tal
    cual quedó, no una sesión "parecida".
    oxide_atoms es una lista de (x, y, z, oxide_type) en nm — el mismo formato que
    devuelve plate.get_oxide_coords() sin el índice ni el flag 'modified'.
    Devuelve la cantidad de sitios de oxidación agregados (cuenta OO/OE, no los
    HO que los acompañan, igual que add_oxydation_to_list_of_carbon)."""
    added= 0
    for x, y, z, oxide_type in oxide_atoms:
        i_atom= plate.allocate_atom_index()
        temp_ox= [x, y, z, oxide_type, i_atom, False, oxide_type]
        bonded= plate.get_nearest_carbons_to_oxide(temp_ox)
        bonded_indices= tuple(c[4] for c in bonded) if bonded else None
        plate.add_oxide(x, y, z, oxide_type, i_atom, bonded_carbon_indices=bonded_indices)
        if oxide_type != "HO":
            added+= 1
    return added


# ================================
# Tipo de carbono
# ================================

def find_carbon_at(plate, x, y, z, tolerance=1e-6):
    """Busca el carbono en esta posición exacta (nm), con la misma tolerancia
    que ya usa apply_oxidation_removed_step para óxidos. Devuelve None si no
    encuentra ninguno."""
    for carbon in plate.get_carbon_coords():
        if abs(carbon[0]-x) < tolerance and abs(carbon[1]-y) < tolerance and abs(carbon[2]-z) < tolerance:
            return carbon
    return None

def apply_carbon_type_explicit(plate, carbons, new_type):
    """carbons: lista de (x, y, z) en nm -- posiciones ya resueltas de los
    carbonos a los que hay que asignarles new_type (mismo criterio 'hard' que
    apply_oxidation_explicit). Devuelve la cantidad de carbonos modificados.
    Levanta ValueError con un mensaje claro si alguna posición no matchea
    ningún carbono de la placa (típicamente: se está replayeando un step
    fuera de orden, o sobre una placa distinta a la que se grabó)."""
    changed= 0
    for x, y, z in carbons:
        carbon= find_carbon_at(plate, x, y, z)
        if carbon is None:
            raise ValueError(f"set_carbon_type: no carbon found at position "
                              f"({x*10:.3f}, {y*10:.3f}, {z*10:.3f}) Å")
        plate.set_carbon_type(carbon, new_type)
        changed+= 1
    return changed

def apply_carbon_type_step(plate, step):
    """Un step 'set_carbon_type' del schema multi-placa: {carbon_type, carbons}.
    'carbons' viene en Å (mismo criterio que el resto del schema); se convierte
    a nm antes de buscar, que es lo que usa Graphene internamente."""
    new_type= step.get("carbon_type")
    if not new_type:
        raise ValueError("set_carbon_type step needs a non-empty 'carbon_type'")
    carbons= step.get("carbons")
    if not carbons:
        raise ValueError("set_carbon_type step needs a non-empty 'carbons' list")
    carbons_nm= [(x/10, y/10, z/10) for x, y, z in carbons]
    changed= apply_carbon_type_explicit(plate, carbons_nm, new_type)
    print(f"  set carbon type to {new_type!r} for {changed} carbon(s)")


# ================================
# Geometría de placa
# ================================

def compute_plate_grid(width_ang, height_ang, factor):
    """Convierte ancho/alto (como los spinboxes del diálogo 'Create', en Å) a la grilla n_x, n_y."""
    width_nm= width_ang / 10
    height_nm= height_ang / 10
    n_x= math.floor(width_nm / (2 * 0.1225 * factor))
    n_y= math.floor(height_nm / (6 * 0.071 * factor)) + 1
    return n_x, n_y

def check_plate_size(n_x, n_y):
    """Devuelve (cabe: bool, max_atoms) según el esquema de nombres de átomos disponible."""
    max_atoms= len(generatePatterns())
    max_n_x_n_y= max_atoms // (2 * (2 * n_x + 1)) if n_x > 0 else 0
    return n_y <= max_n_x_n_y, max_atoms


# ================================
# CNT
# ================================

def remove_overlapping_atoms(atoms):
    to_remove_list= []
    for i in range(len(atoms)):
        for j in range(i+1, len(atoms)):
            x1,y1,z1= atoms[i][:3]
            x2,y2,z2= atoms[j][:3]
            if np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2) < .02:
                to_remove_list.append(j)
    print(f"Removed {len(to_remove_list)} overlapping atoms")
    return np.delete(atoms, to_remove_list, axis=0)

def roll_atoms_as_CNT(atoms, roll_vec, center=[0,0,0]):
    atoms= np.array(atoms, dtype=object)
    ux, uy= roll_vec
    L= np.sqrt(ux**2 + uy**2)
    if L == 0: raise ValueError("The rolling vector cannot be (0,0).")

    R= L / (2 * np.pi)

    e_u, e_v= np.array([ux,uy])/L, np.array([-uy,ux])/L

    xy= np.array(atoms[:,:2].tolist(), dtype=float)
    atom_z= np.array(atoms[:,2].tolist(), dtype=float)

    is_carbon= np.array([str(a).startswith("C") for a in atoms[:,3]])
    z_ref= np.mean(atom_z[is_carbon])

    delta_z= atom_z - z_ref

    u,v= np.dot(xy, e_u), np.dot(xy, e_v)
    theta= 2*np.pi * u / L
    R_eff= R - delta_z
    new_x, new_y, new_z= R_eff*np.cos(theta), R_eff*np.sin(theta), v

    new_atoms= atoms.copy()
    for i in range(len(new_atoms)):
        new_atoms[i][0], new_atoms[i][1], new_atoms[i][2]= new_x[i], new_y[i], new_z[i]

    carbons= new_atoms[is_carbon]
    carbon_coords= np.array([list(c[:3]) for c in carbons], dtype=float)
    new_center= np.mean(carbon_coords, axis=0)
    displacement= new_center - np.array(center)

    for i in range(len(new_atoms)):
        new_atoms[i][:3]= np.array(new_atoms[i][:3], dtype=float) - displacement

    return remove_overlapping_atoms(new_atoms)


def apply_cnt(plate, roll_vec, center=None):
    """Enrolla la placa como CNT, replicando main_window.handle_btn_cnt_clicked: mismo orden
    (set_is_CNT ANTES de set_atoms, si no restore_plate() queda roto) y sin hidrógenos de
    borde (ese flujo es excluyente con reduce_borders en la GUI). Muta la placa in-place."""
    if center is None:
        center= plate.get_geometric_center()
    atoms= plate.get_carbon_coords() + plate.get_oxide_coords()
    new_atoms= roll_atoms_as_CNT(atoms, roll_vec, center)
    plate.set_is_CNT(True)
    plate.set_atoms(new_atoms)
    return plate

def reduce_borders(plate):
    """Agrega hidrógenos de borde a los carbonos periféricos (los que no tienen los 3
    vecinos completos). Envuelve Graphene.reduce_borders() -ya es pura, sin Qt- para que
    el headless tenga la misma API por función que el resto de las operaciones de este
    módulo. Mutuamente excluyente con CNT (ver apply_cnt: no incluye hidrógenos de
    borde al enrollar), igual que en la GUI."""
    plate.reduce_borders()
    return plate


# ================================
# Import / Export
# ================================

def load_plates_from_file(ext, file_name):
    readers= {".gro": readGRO, ".xyz": readXYZ, ".pdb": readPDB, ".mol2": readMOL2}
    if ext not in readers:
        raise ValueError(f"Not supported file extension: {ext}")
    return readers[ext](file_name)

def export_plates(file_name, plates, periodicity_conditions, atom_types=None, duplicates_list=None, progress_callback=None):
    """Despacha a la función de export correcta según la extensión de file_name."""
    if file_name.endswith(".top"):
        # writeTOP llama a progress_callback sin chequear None (siempre le llega uno
        # real desde la GUI, vía ExportTopWorker) — desde acá (headless/tests) puede
        # no venir ninguno, así que le damos un no-op por defecto.
        callback= progress_callback or (lambda fraction: None)
        writeTOP(file_name, plates, duplicates_list or [[], []], atom_types or {}, callback, periodicity_conditions)
    elif file_name.endswith(".gro"):
        writeGRO(file_name, plates, periodicity_conditions)
    elif file_name.endswith(".pdb"):
        writePDB(file_name, plates, periodicity_conditions)
    elif file_name.endswith(".xyz"):
        writeXYZ(file_name, plates, periodicity_conditions)
    elif file_name.endswith(".mol2"):
        writeMOL2(file_name, plates, periodicity_conditions)
    else:
        raise ValueError("Unsupported file extension: " + file_name)


# ================================
# Schema multi-placa (plates: [...] con steps ordenados por placa)
# ================================

def build_plate_from_create(create_cfg):
    """Construye una Graphene a partir del dict 'create' de una entrada 'plates'
    (o del 'plate' del schema plano — ambos comparten esta función)."""
    width= create_cfg.get("width", 100)      # Å
    height= create_cfg.get("height", 100)    # Å
    factor= create_cfg.get("factor", 1.0)
    center= create_cfg.get("center", [0, 0, 0])  # Å
    periodic_x= create_cfg.get("periodic_boundary_x", False)
    periodic_y= create_cfg.get("periodic_boundary_y", False)

    n_x, n_y= compute_plate_grid(width, height, factor)
    fits, max_atoms= check_plate_size(n_x, n_y)
    if not fits:
        raise ValueError(f"Plate too large ({max_atoms} atom names available in the naming scheme). Reduce width/height.")

    center_x_nm, center_y_nm, center_z_nm= [c / 10 for c in center]
    plate= Graphene.create_from_params(n_x, n_y, center_x_nm, center_y_nm, center_z_nm, factor, periodic_x, periodic_y)
    print(f"Plate built: {n_x}x{n_y} ({plate.get_number_atoms()} atoms)")
    return plate

_RESERVED_CTYPE_PREFIXES= tuple(k for k in ATOM_PARAMS_TOP if len(k) == 2)

def _is_reserved_ctype_name(name):
    if name[:2] in _RESERVED_CTYPE_PREFIXES:
        return True
    if len(name) > 1 and name[0] == "H":
        try:
            int(name[1:])
            return True
        except ValueError:
            pass
    return False

def build_atom_types(cfg):
    atom_types= {}
    for entry in cfg.get("atom_types", []):
        name= entry["name"]
        if _is_reserved_ctype_name(name):
            raise ValueError(f"atom type {name!r}: reserved by the exporter (oxidized-carbon/oxide "
                              "markers, or the auto-generated hydrogen naming scheme) -- would "
                              "silently export with the wrong element's charge/mass")
        atom_types[name]= {"epsilon": entry["epsilon"], "sigma": entry["sigma"]}
    return atom_types

def validate_cnt_vector(vector):
    if not vector or len(vector) != 2 or (vector[0] == 0 and vector[1] == 0):
        raise ValueError("cnt vector is missing or invalid (expected [x, y], not [0, 0])")

def apply_oxidation_step(plate, step):
    """Un solo step de oxidación (mode: soft o hard)."""
    mode= step.get("mode", "soft")

    if mode == "hard":
        oxides= step.get("oxides")
        if not oxides:
            raise ValueError("oxidation step with mode: hard needs a non-empty 'oxides' list")
        # cada entrada es [x, y, z, type] en Å; se convierte a nm, que es lo que
        # usa Graphene internamente.
        oxide_atoms= [(x/10, y/10, z/10, t) for x, y, z, t in oxides]
        done= apply_oxidation_explicit(plate, oxide_atoms)
        print(f"  oxidized {done} sites (hard replica, {len(oxides)} oxide atoms)")
        return

    if mode != "soft":
        raise ValueError(f"Unknown oxidation mode: {mode!r} (expected 'soft' or 'hard')")

    z_mode_map= {"+z": 0, "-z": 1, "random": 2}
    expr= step.get("expression", "")
    prob_oh= step.get("prob_oh", 100)
    fraction= step.get("fraction", 1.0)
    z_mode= z_mode_map.get(step.get("z_mode", "random"), 2)

    selected= select_atoms(plate, expr, fraction, z_mode, prob_oh)
    if not selected:
        print(f"  oxidation step skipped (nothing matched): {expr!r}")
        return
    done= apply_oxidation(plate, selected, z_mode, prob_oh)
    print(f"  oxidized {done} sites (expression: {expr!r})")

def apply_oxidation_removed_step(plate, step):
    x, y, z, oxide_type= step["oxide"]
    x, y, z= x/10, y/10, z/10  # Å -> nm
    for ox in plate.get_oxide_coords():
        if ox[3] == oxide_type and abs(ox[0]-x) < 1e-6 and abs(ox[1]-y) < 1e-6 and abs(ox[2]-z) < 1e-6:
            plate.remove_atom_oxide(ox)
            print(f"  removed oxide atom ({oxide_type} at {step['oxide'][:3]})")
            return
    raise ValueError(f"oxidation_removed step: no matching oxide atom found at {step['oxide']}")

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
        reduce_borders(plate)
        print(f"  reduced borders ({len(plate.get_hydrogens_coords())} H atoms added)")
    elif step_type == "cnt":
        vector= step.get("vector")
        validate_cnt_vector(vector)
        apply_cnt(plate, vector)
        print(f"  rolled into CNT (vector={vector})")
    elif step_type == "cnt_restored":
        if not plate.get_is_CNT():
            raise ValueError("cnt_restored step on a plate that isn't currently rolled into a CNT")
        plate.restore_plate()
        print("  cnt restored")
    elif step_type == "set_carbon_type":
        apply_carbon_type_step(plate, step)
    else:
        raise ValueError(f"Unknown step type: {step_type!r}")

def validate_steps(plate_name, steps):
    relevant_types= [s.get("type") for s in steps if s.get("type") != "duplicate"]

    if "reduce_borders" in relevant_types:
        first_reduce= relevant_types.index("reduce_borders")
        if "cnt" in relevant_types[first_reduce:]:
            raise ValueError(f"plate {plate_name!r}: reduce_borders and cnt are mutually exclusive "
                              "(same restriction as the GUI: rolling into a CNT is disabled once "
                              "border hydrogens were added)")

    is_rolled= False
    for step_type in relevant_types:
        if step_type == "cnt_restored":
            if not is_rolled:
                raise ValueError(f"plate {plate_name!r}: 'cnt_restored' with no active 'cnt' before it")
            is_rolled= False
            continue
        if is_rolled:
            raise ValueError(f"plate {plate_name!r}: 'cnt' must be followed by 'cnt_restored' or be "
                              "the last step (same restriction as the GUI: nothing else is editable "
                              "while a plate is rolled into a CNT)")
        if step_type == "cnt":
            is_rolled= True

    for step in steps:
        if step.get("type") == "duplicate":
            validate_steps(step.get("name", "<unnamed duplicate>"), step.get("steps", []))

def _process_steps(plate, steps, registry, plates_by_name, name_to_id, plate_id):
    for step in steps:
        if step.get("type") != "duplicate":
            apply_step(plate, step)
            continue

        name= step.get("name")
        if not name:
            raise ValueError("duplicate step needs a 'name'")
        if name in plates_by_name:
            raise ValueError(f"Duplicate plate name in config: {name!r}")

        dx, dy, dz= step["translation"]
        absolute= step.get("absolute", False)
        translation= compute_duplicate_translation(dx, dy, dz, absolute, plate.get_geometric_center())
        new_plate= plate.duplicate(translation)
        new_plate_id= registry.add(new_plate, duplicate_of=plate_id, translation=translation)
        print(f"  duplicate added as {name!r} (translation={step['translation']}, absolute={absolute})")

        plates_by_name[name]= new_plate
        name_to_id[name]= new_plate_id
        _process_steps(new_plate, step.get("steps", []), registry, plates_by_name, name_to_id, new_plate_id)


def _ends_up_rolled(steps):
    """¿esta placa queda enrollada en CNT al final de sus PROPIOS steps? (sin
    contar 'duplicate', que es una rama aparte -- mismo filtro que
    validate_steps). Devuelve el vector del cnt final, o None si no."""
    relevant= [s for s in steps if s.get("type") != "duplicate"]
    if relevant and relevant[-1].get("type") == "cnt":
        return relevant[-1]["vector"]
    return None


def iter_plate_build_order(cfg):
    """Camina 'plates' en el MISMO orden en que build_session_from_config
    construye cada placa (raíces primero, duplicados anidados en el punto
    exacto de los 'steps' de su fuente) y devuelve una lista de tuplas
    (name, parent_name_or_None, translation_raw, absolute, cnt_vector_or_None)
    -- name_to_id no hace falta acá, cada llamador arma su propia relación
    padre/hijo por nombre."""
    order= []

    def walk(name, parent_name, translation_raw, absolute, steps):
        order.append((name, parent_name, translation_raw, absolute, _ends_up_rolled(steps)))
        for step in steps:
            if step.get("type") == "duplicate":
                walk(step["name"], name, step["translation"], step.get("absolute", False), step.get("steps", []))

    for plate_cfg in cfg.get("plates", []):
        walk(plate_cfg["name"], None, None, None, plate_cfg.get("steps", []))

    return order


def build_session_from_config(cfg):
    plates_cfg= cfg.get("plates", [])
    if not plates_cfg:
        raise ValueError("'plates' is present but empty — nothing to build")

    # Nota: periodic_boundary_x/y vive dentro de cada placa raíz ('create'),
    # pero export/checkBounds solo soportan UNA periodicidad global para todo
    # el sistema (igual que main_window.periodicity_conditions en la GUI). Se
    # toma la de la PRIMERA placa raíz.
    first_create= plates_cfg[0].get("create", {}) if plates_cfg else {}
    periodicity_conditions= [
        first_create.get("periodic_boundary_x", False),
        first_create.get("periodic_boundary_y", False),
    ]

    registry= PlateRegistry()
    plates_by_name= {}
    name_to_id= {}

    for plate_cfg in plates_cfg:
        name= plate_cfg.get("name")
        if not name:
            raise ValueError("Every entry in 'plates' needs a 'name'")
        if name in plates_by_name:
            raise ValueError(f"Duplicate plate name in config: {name!r}")
        if "create" not in plate_cfg:
            raise ValueError(f"plate {name!r}: top-level 'plates' entries need 'create' -- "
                              "duplicates now live as a 'duplicate' step inside their source's "
                              "'steps', not as their own top-level entry")

        plate= build_plate_from_create(plate_cfg["create"])
        plate_id= registry.add(plate)
        plates_by_name[name]= plate
        name_to_id[name]= plate_id

        steps= plate_cfg.get("steps", [])
        validate_steps(name, steps)
        _process_steps(plate, steps, registry, plates_by_name, name_to_id, plate_id)

    plates= list(registry)
    duplicates_list= registry.resolve_duplicate_groups()
    atom_types= build_atom_types(cfg)

    return plates_by_name, plates, duplicates_list, atom_types, periodicity_conditions
