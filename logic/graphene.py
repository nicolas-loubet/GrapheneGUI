import random
import numpy as np

class Graphene:
    def __init__(self, carbon_coords=None, oxide_coords=None):
        self.carbon_coords = carbon_coords if carbon_coords is not None else []
        self.oxide_coords = oxide_coords if oxide_coords is not None else []

    @classmethod
    def create_from_coords(cls, carbon_coords, oxide_coords):
        return cls(carbon_coords, oxide_coords)

    @classmethod
    def create_from_params(cls, n_x, n_y, center_x, center_y, center_z, factor):
        dx = 0.1225 * factor
        dy = 0.071 * factor
        name_atoms = generatePatterns()
        coords = []
        i_atom = 1

        width = n_x * 2 * dx
        height = n_y * 6 * dy
        center_x_geom = width / 2
        center_y_geom = height / 2

        offset_x = center_x - center_x_geom
        offset_y = center_y - center_y_geom

        for iy in range(n_y):
            ybase = iy * 6 * dy
            for ix in range(n_x):
                coords.append([dx * ix * 2 + offset_x, ybase + dy + offset_y, center_z, name_atoms[i_atom - 1], i_atom])
                i_atom += 1
                coords.append([dx * (ix * 2 + 1) + offset_x, ybase + offset_y, center_z, name_atoms[i_atom - 1], i_atom])
                i_atom += 1
            coords.append([dx * n_x * 2 + offset_x, ybase + dy + offset_y, center_z, name_atoms[i_atom - 1], i_atom])
            i_atom += 1

            ybase = ybase + dy * 3
            for ix in range(n_x):
                coords.append([dx * ix * 2 + offset_x, ybase + offset_y, center_z, name_atoms[i_atom - 1], i_atom])
                i_atom += 1
                coords.append([dx * (ix * 2 + 1) + offset_x, ybase + dy + offset_y, center_z, name_atoms[i_atom - 1], i_atom])
                i_atom += 1
            coords.append([dx * n_x * 2 + offset_x, ybase + offset_y, center_z, name_atoms[i_atom - 1], i_atom])
            i_atom += 1

        return cls(coords, [])

    def add_carbon(self, x, y, z, atom_name, atom_index):
        self.carbon_coords.append([x, y, z, atom_name, atom_index])

    def add_oxide(self, x, y, z, oxide_type, atom_index):
        self.oxide_coords.append([x, y, z, oxide_type, atom_index])

    def get_carbon_coords(self):
        return self.carbon_coords

    def get_oxide_coords(self):
        return self.oxide_coords
    
    def get_number_atoms(self):
        return len(self.carbon_coords)+len(self.oxide_coords)
    
    def remove_oxides(self):
        ox= self.oxide_coords
        self.oxide_coords = []
        return ox
    
    def remove_atom_oxide(self, ox):
        self.oxide_coords.remove(ox)
    
    def add_oxydation_to_list_of_carbon(self, list_carbons, z_mode, prob_oh):
        i_atom = self.get_number_atoms()
        
        oxidized_carbons = []
        for ox in self.oxide_coords:
            if ox[3] == "HO": continue
            oxidized_carbons.append(self.get_nearest_carbon(ox[0], ox[1]))

        for carbon in list_carbons:
            if carbon in oxidized_carbons: continue
            rand = random.random()*100
            x1, y1, z1 = carbon[:3]

            z_dir = 1 if z_mode == 0 else -1 if z_mode == 1 else random.choice([-1,1])

            if rand <= prob_oh:
                i_atom += 1
                self.add_oxide(x1, y1, z1+z_dir*0.149, "OO", i_atom)
                i_atom += 1
                self.add_oxide(x1+.093, y1, z1+z_dir*0.181, "HO", i_atom)
                oxidized_carbons.append(carbon)

            else:
                adjacent = self.carbons_adjacent(carbon)
                random.shuffle(adjacent)
                found = False
                for adj in adjacent:
                    if adj in oxidized_carbons:
                        continue
                    x2, y2, z2 = adj[:3]
                    x_mid = (x1 + x2) / 2
                    y_mid = (y1 + y2) / 2
                    z_mid = (z1 + z2) / 2

                    i_atom += 1
                    self.add_oxide(x_mid, y_mid, z_mid+z_dir*0.126, "OE", i_atom)
                    oxidized_carbons.append(carbon)
                    oxidized_carbons.append(adj)
                    found = True
                    break

                if not found:
                    #print(f"No adjacent carbon available for OE near {carbon[3]}, added OH instead")
                    i_atom += 1
                    self.add_oxide(x1, y1, z1+z_dir*0.149, "OO", i_atom)
                    i_atom += 1
                    self.add_oxide(x1+.093, y1, z1+z_dir*0.18, "HO", i_atom)
                    oxidized_carbons.append(carbon)


    def carbons_adjacent(self, carbon_center):
        adjacent_carbons = []
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

    def get_nearest_carbons_to_oxide(self, ox):
        output= []
        for carbon in self.carbon_coords:
            if self.distance_2D(ox[0],ox[1],carbon[0],carbon[1]) < 0.1:
                output.append(carbon)
        return output

    def is_position_occupied(self, x, y, z, threshold=0.1):
        for ox in self.get_oxide_coords():
            ox_x, ox_y, ox_z = ox[:3]
            dist = self.distance_3D(x, y, z, ox_x, ox_y, ox_z)
            if dist < threshold:
                return True
        return False
    
    def get_oxides_for_carbon(self, carbon_center):
        oxides_to_remove = []
        x, y = carbon_center[:2]
        
        min_dist= float("inf")
        for carbon in self.carbon_coords:
            if carbon == carbon_center: continue
            x2,y2= carbon[:2]
            d= self.distance_2D(x,y,x2,y2)
            if d < min_dist:
                min_dist= d
        
        for ox in self.oxide_coords:
            ox_x, ox_y = ox[:2]
            dist = self.distance_2D(x, y, ox_x, ox_y)
            if dist < min_dist:
                oxides_to_remove.append(ox)
        
        return oxides_to_remove
    
    def recheck_ox_indexes(self):
        prev_ox= self.oxide_coords
        self.oxide_coords= []
        i_atom= len(self.carbon_coords)

        for i in range(len(prev_ox)):
            if prev_ox[i][3] == "OO":
                if i+1 < len(prev_ox) and prev_ox[i+1][3] == "HO": continue

                z_dir= 1 if prev_ox[i][2] > self.carbon_coords[0][2] else -1
                new_ox= [prev_ox[i][0]+.093, prev_ox[i][1], prev_ox[i][2]+z_dir*.032, "HO", -1]
                prev_ox= prev_ox[:i+1] + [new_ox] + prev_ox[i+1:]

        for ox in prev_ox:
            i_atom += 1
            self.add_oxide(ox[0], ox[1], ox[2], ox[3], i_atom)

    def distance_2D(self, x1, y1, x2, y2):
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    
    def distance_3D(self, x1, y1, z1, x2, y2, z2):
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)

def generatePatterns(initial_character="C"):
    result = []
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
