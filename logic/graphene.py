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
        center_z_geom = 0

        offset_x = center_x - center_x_geom
        offset_y = center_y - center_y_geom
        offset_z = center_z - center_z_geom

        for iy in range(n_y):
            ybase = iy * 6 * dy
            for ix in range(n_x):
                coords.append([dx * ix * 2 + offset_x, ybase + dy + offset_y, center_z + offset_z, name_atoms[i_atom - 1], i_atom])
                i_atom += 1
                coords.append([dx * (ix * 2 + 1) + offset_x, ybase + offset_y, center_z + offset_z, name_atoms[i_atom - 1], i_atom])
                i_atom += 1
            coords.append([dx * n_x * 2 + offset_x, ybase + dy + offset_y, center_z + offset_z, name_atoms[i_atom - 1], i_atom])
            i_atom += 1

            ybase = ybase + dy * 3
            for ix in range(n_x):
                coords.append([dx * ix * 2 + offset_x, ybase + offset_y, center_z + offset_z, name_atoms[i_atom - 1], i_atom])
                i_atom += 1
                coords.append([dx * (ix * 2 + 1) + offset_x, ybase + dy + offset_y, center_z + offset_z, name_atoms[i_atom - 1], i_atom])
                i_atom += 1
            coords.append([dx * n_x * 2 + offset_x, ybase + offset_y, center_z + offset_z, name_atoms[i_atom - 1], i_atom])
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
    
    def add_oxydation_to_list_of_carbon(self, list_carbons, z_mode, prob_oh, prob_o):
        pass

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
