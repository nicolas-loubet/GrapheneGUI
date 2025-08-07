import random
import numpy as np

class Graphene:
    def __init__(self, carbon_coords=None, oxide_coords=None):
        self.carbon_coords = carbon_coords if carbon_coords is not None else []
        self.oxide_coords = oxide_coords if oxide_coords is not None else []

    def __init__(self, n_x, n_y, center_x=0, center_y=0, center_z=0, factor=1):
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

        self.carbon_coords = coords
        self.oxide_coords = []


    def add_carbon(self, x, y, z, atom_name, atom_index):
        self.carbon_coords.append((x, y, z, atom_name, atom_index))

    def add_oxide(self, x, y, z, oxide_type, atom_index):
        self.oxide_coords.append((x, y, z, oxide_type, atom_index))

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
    
    def add_oxydation_to_list_of_carbon(self, list_carbons, z_mode, prob_oh, prob_o):
        i_atom = self.get_number_atoms()
        for carbon in list_carbons:
            rand = random.random()*100
            x,y,z = carbon[:3]
            if rand <= prob_oh:
                i_atom += 1
                self.add_oxide(x,y,z,"OO",i_atom)
            else:
                i_atom += 1
                self.add_oxide(x,y,z,"OE",i_atom)

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
