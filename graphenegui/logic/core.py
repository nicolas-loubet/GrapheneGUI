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


# ================================
# Duplicados (bookkeeping de placas)
# ================================

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
    else:
        return

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
        writeTOP(file_name, plates, duplicates_list or [[], []], atom_types or {}, progress_callback, periodicity_conditions)
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
