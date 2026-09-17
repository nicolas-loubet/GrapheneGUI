import random
import numpy as np

# Tipo de carbono por defecto al crear una placa. Único lugar donde se define
# el literal — antes estaba repetido 6 veces en este archivo (create_from_params,
# add_carbon, set_atoms) y una vez más en main_window.py (self.atom_types). La
# Etapa 12 (reset de tipo de carbono a mano) necesita esta constante para no
# repetir el string "ca" una vez más.
DEFAULT_CARBON_TYPE= "ca"

class Graphene:
    def __init__(self, carbon_coords=None, oxide_coords=None, hydrogens_coords=None, scale_factor=1.0,
                 periodic_boundary_x=False, periodic_boundary_y=False):
        self.carbon_coords= carbon_coords if carbon_coords is not None else []
        self.oxide_coords= oxide_coords if oxide_coords is not None else []
        self.hydrogens_coords= hydrogens_coords if hydrogens_coords is not None else []
        self.scale_factor= scale_factor
        self.is_CNT= False
        self.periodic_boundary_x= periodic_boundary_x
        self.periodic_boundary_y= periodic_boundary_y
        # Etapa 19: atom_index del óxido -> tupla de atom_index de los
        # carbonos REALMENTE unidos a él (1 para OO, 2 para OE), grabado en
        # el momento de oxidar (add_oxide). Un dict APARTE, no un campo más
        # en la tupla del óxido -- roll_atoms_as_CNT arma un array de NumPy
        # 2D a partir de carbon_coords+oxide_coords concatenados, que exige
        # todas las filas del MISMO largo; agregarle un campo más a los
        # óxidos nomás (sin tocar los carbonos) las desempareja y rompe ese
        # array. atom_index sobrevive traducciones y rolls sin cambiar
        # (set_atoms lo preserva tal cual viene), así que este dict se puede
        # seguir consultando después de cualquier transformación.
        self.oxide_bonds= {}

    @classmethod
    def create_from_coords(cls, carbon_coords, oxide_coords, hydrogens_coords=None):
        plate= cls(carbon_coords, oxide_coords, hydrogens_coords)
        neighbors= plate.carbons_adjacent(plate.carbon_coords[0])
        distance= plate.distance_2D(plate.carbon_coords[0][0], plate.carbon_coords[0][1], neighbors[0][0], neighbors[0][1])
        factor= distance / 0.141588
        plate.scale_factor= np.round(factor, 1)
        return plate

    @classmethod
    def create_from_params(cls, n_x, n_y, center_x, center_y, center_z, factor, periodic_boundary_x, periodic_boundary_y=False):
        dx= 0.1225 * factor
        dy= 0.071 * factor
        name_atoms= generatePatterns()
        coords= []
        i_atom= 1

        width= n_x * 2 * dx
        height= ((n_y - 1) * 6 + 4) * dy
        center_x_geom= width / 2
        center_y_geom= height / 2

        offset_x= center_x - center_x_geom
        offset_y= center_y - center_y_geom

        for iy in range(n_y):
            ybase= iy * 6 * dy
            for ix in range(n_x):
                coords.append([dx * ix * 2 + offset_x, ybase + dy + offset_y, center_z, name_atoms[i_atom-1], i_atom, False, DEFAULT_CARBON_TYPE])
                i_atom+= 1
                coords.append([dx * (ix * 2 + 1) + offset_x, ybase + offset_y, center_z, name_atoms[i_atom-1], i_atom, False, DEFAULT_CARBON_TYPE])
                i_atom+= 1
            if(not periodic_boundary_x):
                coords.append([dx * n_x * 2 + offset_x, ybase + dy + offset_y, center_z, name_atoms[i_atom-1], i_atom, False, DEFAULT_CARBON_TYPE])
                i_atom+= 1

            ybase= ybase + dy * 3
            for ix in range(n_x):
                coords.append([dx * ix * 2 + offset_x, ybase + offset_y, center_z, name_atoms[i_atom-1], i_atom, False, DEFAULT_CARBON_TYPE])
                i_atom+= 1
                coords.append([dx * (ix * 2 + 1) + offset_x, ybase + dy + offset_y, center_z, name_atoms[i_atom-1], i_atom, False, DEFAULT_CARBON_TYPE])
                i_atom+= 1
            if(not periodic_boundary_x):
                coords.append([dx * n_x * 2 + offset_x, ybase + offset_y, center_z, name_atoms[i_atom-1], i_atom, False, DEFAULT_CARBON_TYPE])
                i_atom+= 1

        plate= cls(coords, [], [], periodic_boundary_x=periodic_boundary_x, periodic_boundary_y=periodic_boundary_y)
        return plate

    def _translated(self, coords, translations):
        dx, dy, dz= translations
        return [[c[0]+dx, c[1]+dy, c[2]+dz, c[3], c[4], c[5], c[6]] for c in coords]

    def duplicate(self, translations):
        carbons= self._translated(self.carbon_coords, translations)
        oxides= self._translated(self.oxide_coords, translations)
        hydrogens= self._translated(self.hydrogens_coords, translations)
        new_plate= Graphene.create_from_coords(carbons, oxides, hydrogens)
        new_plate.periodic_boundary_x= self.periodic_boundary_x
        new_plate.periodic_boundary_y= self.periodic_boundary_y
        new_plate.oxide_bonds= dict(self.oxide_bonds)
        return new_plate

    def add_carbon(self, x, y, z, atom_name, atom_index, modified=False, atom_type=DEFAULT_CARBON_TYPE):
        self.carbon_coords.append([x, y, z, atom_name, atom_index, modified, atom_type])

    def add_oxide(self, x, y, z, oxide_type, atom_index, modified=False, bonded_carbon_indices=None):
        """bonded_carbon_indices (Etapa 19): atom_index (posición 4 de la
        tupla) del/los carbono(s) REALMENTE unidos a este óxido -- 1 para
        OO (HO no lo necesita, ver comentario en change_name_oxides), 2 para
        OE (puentea dos carbonos). Se graba EN EL MOMENTO en que se conoce
        con certeza (al oxidar, mientras la placa está plana -- nunca se
        puede oxidar una placa ya enrollada), en self.oxide_bonds (no en la
        tupla del óxido, ver comentario en __init__), y sobrevive
        traducciones/rolls porque atom_index no cambia con esas
        transformaciones (a diferencia de re-derivar el vecino por geometría
        DESPUÉS de enrollar: la curvatura puede acercar en 3D carbonos que
        no tienen nada que ver, confirmado en vivo con un CNT [2,0] sobre
        una placa 30x20). None si no se conoce (óxidos importados de un
        archivo, o creados antes de este cambio) -- en ese caso se cae al
        mecanismo geométrico viejo como mejor esfuerzo (ver
        get_bonded_carbons_for_oxide)."""
        self.oxide_coords.append([x, y, z, oxide_type, atom_index, modified, oxide_type])
        if bonded_carbon_indices:
            self.oxide_bonds[atom_index]= tuple(bonded_carbon_indices)

    def set_atoms(self, atoms):
        self.carbon_coords= []
        self.oxide_coords= []
        for x, y, z, atom_name, atom_index, modified, *extra in atoms:  
            atom_type= extra[0] if extra else DEFAULT_CARBON_TYPE
            if atom_name.startswith("C"):
                self.carbon_coords.append([x, y, z, atom_name, atom_index, modified, atom_type])
            else:
                self.oxide_coords.append([x, y, z, atom_name, atom_index, modified, atom_type])

    def set_is_CNT(self, is_CNT):
        self.is_CNT= is_CNT
        if is_CNT:
            self.backup_not_CNT= [self.carbon_coords.copy(), self.oxide_coords.copy(), self.hydrogens_coords.copy()]

    def restore_plate(self):
        self.carbon_coords= self.backup_not_CNT[0]
        self.oxide_coords= self.backup_not_CNT[1]
        self.hydrogens_coords= self.backup_not_CNT[2]
        self.is_CNT= False
    
    def get_is_CNT(self):
        return self.is_CNT
    
    def get_carbon_coords(self):
        return self.carbon_coords

    def get_oxide_coords(self):
        return self.oxide_coords
    
    def get_hydrogens_coords(self):
        return self.hydrogens_coords

    def get_scale_factor(self):
        return self.scale_factor

    def get_oxide_count(self):
        count= 0
        for ox in self.oxide_coords:
            if ox[3] == "HO": continue
            count+= 1
        return count
    
    def get_number_atoms(self):
        return len(self.carbon_coords)+len(self.oxide_coords)+len(self.hydrogens_coords)
    
    def remove_oxides(self):
        ox= self.oxide_coords
        self.oxide_coords= []
        self.oxide_bonds= {}
        return ox
    
    def remove_atom_oxide(self, ox):
        self.oxide_coords.remove(ox)
        self.oxide_bonds.pop(ox[4], None)
    
    def add_oxydation_to_list_of_carbon(self, list_carbons, z_mode, prob_oh):
        i_atom= self.get_number_atoms()
        count_oxidations= 0
        
        oxidized_carbons= []
        for ox in self.oxide_coords:
            if ox[3] == "HO": continue
            oxidized_carbons.append(self.get_nearest_carbon(ox[0], ox[1]))

        for carbon in list_carbons:
            if carbon in oxidized_carbons: continue
            rand= random.random()*100
            x1, y1, z1= carbon[:3]

            z_dir= 1 if z_mode == 0 else -1 if z_mode == 1 else random.choice([-1,1])

            if rand <= prob_oh:
                i_atom+= 1
                self.add_oxide(x1, y1, z1+z_dir*0.149, "OO", i_atom, bonded_carbon_indices=(carbon[4],))
                i_atom+= 1
                self.add_oxide(x1+.093, y1, z1+z_dir*0.181, "HO", i_atom)
                oxidized_carbons.append(carbon)
                count_oxidations+= 1

            else:
                adjacent= self.carbons_adjacent(carbon)
                random.shuffle(adjacent)
                found= False
                for adj in adjacent:
                    if adj in oxidized_carbons:
                        continue
                    x2, y2, z2= adj[:3]
                    x_mid= (x1 + x2) / 2
                    y_mid= (y1 + y2) / 2
                    z_mid= (z1 + z2) / 2

                    i_atom+= 1
                    self.add_oxide(x_mid, y_mid, z_mid+z_dir*0.126, "OE", i_atom,
                                    bonded_carbon_indices=(carbon[4], adj[4]))
                    oxidized_carbons.append(carbon)
                    oxidized_carbons.append(adj)
                    count_oxidations+= 1
                    found= True
                    break

                if not found:
                    i_atom+= 1
                    self.add_oxide(x1, y1, z1+z_dir*0.149, "OO", i_atom, bonded_carbon_indices=(carbon[4],))
                    count_oxidations+= 1
                    i_atom+= 1
                    self.add_oxide(x1+.093, y1, z1+z_dir*0.18, "HO", i_atom)
                    oxidized_carbons.append(carbon)

        return count_oxidations


    def carbons_adjacent(self, carbon_center):
        adjacent_carbons= []
        min_dist= float("inf")
        tolerance= .01
        x,y= carbon_center[:2]

        for carbon in self.carbon_coords:
            if carbon == carbon_center: continue
            x2,y2= carbon[:2]
            d= self.distance_2D(x,y,x2,y2)
            if d < min_dist-tolerance:
                min_dist= d
                adjacent_carbons= [carbon]
            elif d <= min_dist+tolerance and d >= min_dist-tolerance:
                adjacent_carbons.append(carbon)
        return adjacent_carbons
    
    def get_nearest_carbon(self, x, y):
        min_dist= float("inf")
        nearest_carbon= None
        for carbon in self.carbon_coords:
            x2,y2= carbon[:2]
            d= self.distance_2D(x,y,x2,y2)
            if d < min_dist:
                min_dist= d
                nearest_carbon= carbon
        return nearest_carbon

    def get_bonded_carbons_for_oxide(self, ox, threshold=0.17):
        """Devuelve los carbonos REALMENTE unidos a este óxido. Si está en
        self.oxide_bonds (Etapa 19, grabado en el momento de oxidar), los
        busca por atom_index: exacto, no depende de la geometría actual ni
        de cuánto se haya enrollado la placa desde entonces. Si no
        (óxidos importados de un archivo, o alguna vía que todavía no lo
        setee), cae al mecanismo geométrico de mejor esfuerzo
        (get_nearest_carbons_to_oxide)."""
        bonded_indices= self.oxide_bonds.get(ox[4])
        if bonded_indices:
            by_index= {c[4]: c for c in self.carbon_coords}
            found= [by_index[i] for i in bonded_indices if i in by_index]
            if found:
                return found
        return self.get_nearest_carbons_to_oxide(ox, threshold=threshold)

    def resolve_oxide_carbon_bonds(self, threshold=0.17):
        """Asigna a cada óxido su/sus carbono(s). Etapa 19: los óxidos con
        bond grabado en self.oxide_bonds se resuelven DIRECTO por índice,
        sin ninguna ambigüedad ni necesidad de comparar distancias -- son la
        mayoría en cualquier sesión nueva. Para los que NO lo tengan (óxidos
        importados de un archivo), se arma la asignación geométrica greedy
        de antes (candidatos por distancia, ordenados, el más cercano gana
        primero) pero SOLO entre los carbonos que los óxidos con índice
        conocido no se hayan quedado ya -- así ninguna resolución exacta
        puede perder su carbono ante una geométrica ambigua."""
        needed= {id(ox): (1 if ox[3] in ("OO", "HO") else 2) for ox in self.oxide_coords}
        assigned= {id(ox): [] for ox in self.oxide_coords}
        carbon_taken= set()

        by_index= {c[4]: c for c in self.carbon_coords}
        needs_geometry= []
        for ox in self.oxide_coords:
            bonded_indices= self.oxide_bonds.get(ox[4])
            if not bonded_indices:
                needs_geometry.append(ox)
                continue
            found= [by_index[i] for i in bonded_indices if i in by_index]
            for c in found:
                if id(c) in carbon_taken: continue
                assigned[id(ox)].append(c)
                carbon_taken.add(id(c))

        if needs_geometry:
            candidates= []
            for ox in needs_geometry:
                for carbon in self.carbon_coords:
                    if id(carbon) in carbon_taken: continue
                    d= self.distance_3D(ox[0], ox[1], ox[2], carbon[0], carbon[1], carbon[2])
                    if d < threshold:
                        candidates.append((d, ox, carbon))
            candidates.sort(key=lambda triple: triple[0])
            for d, ox, carbon in candidates:
                oxid= id(ox)
                if len(assigned[oxid]) >= needed[oxid]: continue
                if id(carbon) in carbon_taken: continue
                assigned[oxid].append(carbon)
                carbon_taken.add(id(carbon))

        return assigned

    def get_nearest_carbons_to_oxide(self, ox, threshold=0.17):
        """Devuelve los carbonos REALMENTE unidos a este óxido: 1 para OO/HO
        (hidroxilo), 2 para OE (epóxido, puentea dos carbonos). Antes
        devolvía TODOS los carbonos dentro de un umbral fijo de distancia --
        funcionaba en una lámina plana, pero en una placa enrollada en CNT la
        curvatura puede acercar en 3D carbonos que no tienen nada que ver
        entre sí, haciendo que un mismo OE "encuentre" 3 o 4 vecinos en vez
        de 2 (confirmado en vivo: CNT [2,0] sobre una placa 30x20 -- de 122
        OE, 55 encontraban 4 vecinos y 34 encontraban 3; el/los de más se
        marcaban como el otro lado del epóxido en change_name_oxides sin
        serlo, corrompiendo su carga/tipo en el .mol2/.top exportado).

        Ahora se ordenan TODOS los candidatos dentro del umbral por distancia
        real y se devuelven los K más cercanos -- ya no importa cuántos
        caigan bajo el corte, el orden decide. El umbral (0.17, sin cambios)
        pasa a ser solo un resguardo de sanidad (si ni el más cercano cae
        ahí, algo más está mal -- mejor devolver menos de lo esperado que
        inventar un vecino a kilómetros), no la herramienta de desambiguación
        -- esa ahora es el orden por distancia, que no depende de ajustar el
        número para cada geometría/radio de enrollado."""
        k= 1 if ox[3] in ("OO", "HO") else 2
        candidates= []
        for carbon in self.carbon_coords:
            d= self.distance_3D(ox[0], ox[1], ox[2], carbon[0], carbon[1], carbon[2])
            if d < threshold:
                candidates.append((d, carbon))
        candidates.sort(key=lambda pair: pair[0])
        return [carbon for _, carbon in candidates[:k]]

    def is_position_occupied(self, x, y, z, threshold=0.1):
        for ox in self.get_oxide_coords():
            ox_x, ox_y, ox_z= ox[:3]
            dist= self.distance_3D(x, y, z, ox_x, ox_y, ox_z)
            if dist < threshold:
                return True
        return False
    
    def get_oxides_for_carbon(self, carbon_center):
        oxides_to_remove= []
        x, y= carbon_center[:2]
        
        min_dist= float("inf")
        for carbon in self.carbon_coords:
            if carbon == carbon_center: continue
            x2,y2= carbon[:2]
            d= self.distance_2D(x,y,x2,y2)
            if d < min_dist:
                min_dist= d
        
        for ox in self.oxide_coords:
            ox_x, ox_y= ox[:2]
            dist= self.distance_2D(x, y, ox_x, ox_y)
            if dist < min_dist:
                oxides_to_remove.append(ox)
        
        return oxides_to_remove
    
    def recheck_ox_indexes(self):
        original_ox= self.oxide_coords
        old_bonds= self.oxide_bonds
        self.oxide_coords= []
        self.oxide_bonds= {}
        i_atom= len(self.carbon_coords)

        fixed_ox= []
        for i, ox in enumerate(original_ox):
            fixed_ox.append((ox, old_bonds.get(ox[4])))
            if ox[3] == "OO":
                has_paired_h= i+1 < len(original_ox) and original_ox[i+1][3] == "HO"
                if not has_paired_h:
                    z_dir= 1 if ox[2] > self.carbon_coords[0][2] else -1
                    new_ox= [ox[0]+.093, ox[1], ox[2]+z_dir*.032, "HO", -1, ox[5], ox[6]]
                    fixed_ox.append((new_ox, None))

        for ox, bonded in fixed_ox:
            i_atom+= 1
            self.add_oxide(ox[0], ox[1], ox[2], ox[3], i_atom, ox[5], bonded_carbon_indices=bonded)

    def distance_2D(self, x1, y1, x2, y2):
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    
    def distance_3D(self, x1, y1, z1, x2, y2, z2):
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)

    def get_geometric_center(self):
        min_coors, max_coords= [float("inf"), float("inf"), float("inf")], [float("-inf"), float("-inf"), float("-inf")]
        for carbon in self.carbon_coords:
            min_coors= [min(min_coors[i], carbon[i]) for i in range(3)]
            max_coords= [max(max_coords[i], carbon[i]) for i in range(3)]
        return [(min_coors[i] + max_coords[i])*.5 for i in range(3)]

    def set_carbon_type(self, carbon, new_type):
        for i,c in enumerate(self.carbon_coords):
            if c[:6] == carbon[:6]:
                self.carbon_coords[i][6]= new_type
                break

    def reduce_borders(self):
        min_coors, max_coords= [float("inf"), float("inf")], [float("-inf"), float("-inf")]
        n_Hs= 0
        patterns= generatePatterns("H")
        for c in self.carbon_coords:
            min_coors= [min(min_coors[i], c[i]) for i in range(2)]
            max_coords= [max(max_coords[i], c[i]) for i in range(2)]
        min_coors[0]+= .001
        min_coors[1]+= .001
        max_coords[0]-= .001
        max_coords[1]-= .001
        for c in self.carbon_coords:
            xc,yc= c[:2]
            inside_x= xc > min_coors[0] and xc < max_coords[0]
            inside_y= yc > min_coors[1] and yc < max_coords[1]
            if inside_x and inside_y: continue

            # Si el único lado que toca este carbono es periódico, no es un borde de
            # verdad (se conecta con su imagen periódica) -> no le corresponde H acá.
            if not inside_x and self.periodic_boundary_x and inside_y: continue
            if not inside_y and self.periodic_boundary_y and inside_x: continue
            if not inside_x and not inside_y and self.periodic_boundary_x and self.periodic_boundary_y: continue

            adj_carbons= self.carbons_adjacent(c)
            if len(adj_carbons) != 2: continue
            
            x1, y1= adj_carbons[0][:2]
            x2, y2= adj_carbons[1][:2]
            xv1,yv1= xc-x1, yc-y1
            xv3,yv3= 2*xc-x1-x2, 2*yc-y1-y2
            f= ( ((xv1*xv1 + yv1*yv1) / (xv3*xv3 + yv3*yv3)) ** .5 ) * .7676
            x3, y3= xc+f*xv3, yc+f*yv3

            self.hydrogens_coords.append([x3, y3, c[2], patterns[n_Hs], n_Hs+1, c[5], "ha"])
            n_Hs+= 1


def generatePatterns(initial_character="C"):
    result= []
    for i in range(1, 1000):
        result.append(f"{initial_character}{i}")
    for letter in range(ord('A'), ord('Z') + 1):
        result.append(f"{initial_character}{chr(letter)}")
    for letter in range(ord('A'), ord('Z') + 1):
        for num in range(1, 10):
            result.append(f"{initial_character}{chr(letter)}{num}")
    for letter1 in range(ord('A'), ord('Z') + 1):
        for letter2 in range(ord('A'), ord('Z') + 1):
            result.append(f"{initial_character}{chr(letter1)}{chr(letter2)}")
    for letter1 in range(ord('A'), ord('Z') + 1):
        for letter2 in range(ord('A'), ord('Z') + 1):
            for letter3 in range(ord('A'), ord('Z') + 1):
                result.append(f"{initial_character}{chr(letter1)}{chr(letter2)}{chr(letter3)}")
    for num in range(1, 10):
        for letter in range(ord('A'), ord('Z') + 1):
            result.append(f"{initial_character}{num}{chr(letter)}")
    for num in range(1, 10):
        for letter1 in range(ord('A'), ord('Z') + 1):
            for letter2 in range(ord('A'), ord('Z') + 1):
                result.append(f"{initial_character}{num}{chr(letter1)}{chr(letter2)}")
    return result
