"""
Lógica pura del proyecto (sin dependencias de Qt): todo lo que no necesita
una main_window ni widgets vive acá. Es el módulo que comparten la GUI
(a través de functionalities.py) y el futuro modo headless (cli.py).
"""
import random
import math
import numpy as np
from .graphene import Graphene, generatePatterns
from .import_formats import readGRO, readXYZ, readPDB, readMOL2
from .export_formats import writeGRO, writeXYZ, writeTOP, writePDB, writeMOL2
from .plate_registry import PlateRegistry


# ================================
# Duplicados (bookkeeping de placas)
# ================================

# ⚠️ DEPRECADO: main_window/functionalities ya no usan estas 3 funciones — el
# bookkeeping de duplicados por posición (main_window.plates_corresponding_to_duplicates)
# se reemplazó por graphenegui/logic/plate_registry.py (PlateRegistry), que identifica
# placas por un id estable en vez de por índice, y DERIVA si dos placas siguen siendo
# copias idénticas comparando átomos en vez de mantener un flag que hay que invalidar
# a mano (esa invalidación manual, repartida en varios handlers, era la fuente real de
# los bugs). Se dejan sin tocar acá solo para no romper los tests existentes que las
# ejercitan directamente — candidatas a borrar en una limpieza futura.
def manage_duplicates_for_deletion(duplicates_list, index, index_would_be_removed):
    """duplicates_list es [lista_de_duplicados, lista_de_originales] (mismo formato
    que main_window.plates_corresponding_to_duplicates)."""
    if index in duplicates_list[0]:
        index_in_list= duplicates_list[0].index(index)
        duplicates_list[0].pop(index_in_list)
        duplicates_list[1].pop(index_in_list)
    elif index in duplicates_list[1]:
        indexes_in_list= []
        for i in range(len(duplicates_list[1])):
            if duplicates_list[1][i] == index:
                indexes_in_list.append(i)

        if len(indexes_in_list) == 1:
            duplicates_list[0].pop(indexes_in_list[0])
            duplicates_list[1].pop(indexes_in_list[0])
        else:
            new_base= duplicates_list[0][indexes_in_list[0]]
            for i in range(1, len(indexes_in_list)):
                duplicates_list[1][indexes_in_list[i]]= new_base
            duplicates_list[0].pop(indexes_in_list[0])
            duplicates_list[1].pop(indexes_in_list[0])

    # Nota: si index no participa de ninguna relación de duplicados (ni como root ni
    # como duplicado), no hay nada que popear arriba — pero el shift de abajo tiene
    # que correr igual, porque borrar CUALQUIER placa corre la numeración de todas
    # las que están después. Antes había un "else: return" acá que lo cortaba.
    if index_would_be_removed:
        for i in range(len(duplicates_list[0])):
            for j in range(2):
                if duplicates_list[j][i] > index:
                    duplicates_list[j][i] -= 1


def resolve_duplicate_root(duplicates_list, index_base):
    while index_base in duplicates_list[0]:
        index_in_list= duplicates_list[0].index(index_base)
        index_base= duplicates_list[1][index_in_list]
    return index_base


def register_duplicate(duplicates_list, new_plate_index, root_index):
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

def evaluate_condition(x, y, z, i_atom, expr):
    if expr == "": return True
    expr= expr.replace('and', ' and ').replace('or', ' or ').replace('not', ' not ')
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
        i_atom= plate.get_number_atoms() + 1
        plate.add_oxide(x, y, z, oxide_type, i_atom)
        if oxide_type != "HO":
            added+= 1
    return added


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
# Movido acá desde cli.py en la Etapa 9: tiene que ser reusable tanto por el
# headless (cli.py, que atrapa ValueError y hace sys.exit) como por la GUI
# (functionalities.py, que atrapa ValueError y muestra un QMessageBox) — por
# eso estas funciones NUNCA llaman sys.exit ni tocan Qt, solo levantan
# ValueError con un mensaje claro.

def build_plate_from_create(create_cfg):
    """Construye una Graphene a partir del dict 'create' de una entrada 'plates'
    (o del 'plate' del schema plano — ambos comparten esta función)."""
    width= create_cfg.get("width", 100)      # Å
    height= create_cfg.get("height", 100)    # Å
    factor= create_cfg.get("factor", 1.0)
    center= create_cfg.get("center", [0, 0, 0])  # Å
    periodic_x= create_cfg.get("periodic_boundary_x", False)

    n_x, n_y= compute_plate_grid(width, height, factor)
    fits, max_atoms= check_plate_size(n_x, n_y)
    if not fits:
        raise ValueError(f"Plate too large ({max_atoms} atom names available in the naming scheme). Reduce width/height.")

    center_x_nm, center_y_nm, center_z_nm= [c / 10 for c in center]
    plate= Graphene.create_from_params(n_x, n_y, center_x_nm, center_y_nm, center_z_nm, factor, periodic_x)
    print(f"Plate built: {n_x}x{n_y} ({plate.get_number_atoms()} atoms)")
    return plate

def build_atom_types(cfg):
    atom_types= {}
    for entry in cfg.get("atom_types", []):
        atom_types[entry["name"]]= {"epsilon": entry["epsilon"], "sigma": entry["sigma"]}
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
    else:
        raise ValueError(f"Unknown step type: {step_type!r}")

def validate_steps(plate_name, steps):
    """Mismas restricciones que la GUI: reduce_borders y cnt son excluyentes entre
    sí, y una vez enrollada en CNT no se puede seguir editando la placa."""
    types= [s.get("type") for s in steps]
    if "reduce_borders" in types and "cnt" in types:
        raise ValueError(f"plate {plate_name!r}: reduce_borders and cnt are mutually exclusive "
                          "(same restriction as the GUI)")
    if "cnt" in types and types.index("cnt") != len(types) - 1:
        raise ValueError(f"plate {plate_name!r}: 'cnt' must be the last step (same restriction "
                          "as the GUI: further edits are disabled after rolling into a CNT)")

def build_session_from_config(cfg):
    """Construye TODAS las placas de un schema multi-placa (cfg['plates']). Cada
    entrada es una placa nueva (con 'create') O un duplicado de una placa YA
    procesada más arriba en la lista (con 'duplicate_of' + 'translation'), y en
    cualquiera de los dos casos puede tener su propia secuencia de 'steps' — así
    un duplicado se puede seguir editando igual que cualquier otra placa (Etapa 11:
    antes 'duplicates' era una sección aparte sin steps propios, y cualquier
    edición posterior sobre un duplicado se perdía).

    Devuelve (plates_by_name, plates, duplicates_list, atom_types,
    periodicity_conditions). duplicates_list se DERIVA comparando átomos (arma un
    PlateRegistry interno y reusa resolve_duplicate_groups en vez de reimplementar
    la comparación) — si un duplicado se editó vía sus steps y ya no coincide con
    su fuente, sale solo del grupo, igual que en la GUI.

    Levanta ValueError ante cualquier problema — no decide cómo mostrarlo, eso es
    trabajo de quien llama (cli.py hace sys.exit, la GUI muestra un QMessageBox).
    Compartida por cli.py (headless) y main_window.py (GUI, Etapa 9)."""
    plates_cfg= cfg.get("plates", [])
    if not plates_cfg:
        raise ValueError("'plates' is present but empty — nothing to build")

    # Nota: periodic_boundary_x/y vive dentro de cada placa que tenga 'create',
    # pero export/checkBounds solo soportan UNA periodicidad global para todo el
    # sistema (igual que main_window.periodicity_conditions en la GUI). Se toma
    # la de la PRIMERA placa que tenga 'create' (un duplicado no tiene el suyo).
    first_create= next((p.get("create", {}) for p in plates_cfg if "create" in p), {})
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

        if "duplicate_of" in plate_cfg:
            source_name= plate_cfg["duplicate_of"]
            if source_name not in plates_by_name:
                raise ValueError(f"plate {name!r}: unknown source plate {source_name!r} "
                                  "(a duplicate must come after its source in 'plates')")
            source_plate= plates_by_name[source_name]
            dx, dy, dz= plate_cfg["translation"]
            absolute= plate_cfg.get("absolute", False)
            translation= compute_duplicate_translation(dx, dy, dz, absolute, source_plate.get_geometric_center())
            plate= source_plate.duplicate(translation)
            plate_id= registry.add(plate, duplicate_of=name_to_id[source_name], translation=translation)
            print(f"  duplicate of {source_name!r} added (translation={plate_cfg['translation']}, absolute={absolute})")
        else:
            plate= build_plate_from_create(plate_cfg.get("create", {}))
            plate_id= registry.add(plate)

        plates_by_name[name]= plate
        name_to_id[name]= plate_id

        steps= plate_cfg.get("steps", [])
        validate_steps(name, steps)
        for step in steps:
            apply_step(plate, step)

    plates= list(registry)
    duplicates_list= registry.resolve_duplicate_groups()
    atom_types= build_atom_types(cfg)

    return plates_by_name, plates, duplicates_list, atom_types, periodicity_conditions
