def formatGRO(atom_gro):
    i_molec, n_molec, atom_type, i_atom, x, y, z = atom_gro
    output = str(i_molec).rjust(5)
    output += n_molec.ljust(5)
    output += atom_type.rjust(5)
    output += str(i_atom).rjust(5)
    output += str("{:.3f}".format(x)).rjust(8)
    output += str("{:.3f}".format(y)).rjust(8)
    output += str("{:.3f}".format(z)).rjust(8)
    return output+"\n"

def getMaxCoords(coords):
    max_coord = [0, 0, 0]
    for c in coords:
        for i in range(3):
            if c[i] > max_coord[i]:
                max_coord[i] = c[i]
    return max_coord

def writeGRO(filename, plates):
    with open(filename, 'w') as f:
        f.write("Graphene, generated with Graphene GUI.\n")
        total_atoms = sum(len(plate.get_carbon_coords()) + len(plate.get_oxide_coords()) for plate in plates)
        f.write(f"{total_atoms}\n")

        max_coords = [0.0, 0.0, 0.0]
        min_coords = [0.0, 0.0, 0.0]

        for i_plate,plate in enumerate(plates):
            coords = plate.get_carbon_coords()
            oxides = plate.get_oxide_coords()
            atoms= coords + oxides

            for coord in atoms:
                x,y,z,name,i_atom= coord
                min_coords[0] = min(min_coords[0], x)
                min_coords[1] = min(min_coords[1], y)
                min_coords[2] = min(min_coords[2], z)
                max_coords[0] = max(max_coords[0], x)
                max_coords[1] = max(max_coords[1], y)
                max_coords[2] = max(max_coords[2], z)

        for i_plate,plate in enumerate(plates):
            coords = plate.get_carbon_coords()
            oxides = plate.get_oxide_coords()
            atoms= coords + oxides

            for coord in atoms:
                x,y,z,name,i_atom= coord
                x -= min_coords[0]
                y -= min_coords[1]
                z -= min_coords[2]
                f.write(formatGRO((i_plate + 1, "GR"+str(i_plate+1), name, i_atom, x, y, z)))

        max_coords[0] -= min_coords[0]
        max_coords[1] -= min_coords[1]
        max_coords[2] -= min_coords[2]
        f.write(f"{max_coords[0]:10.5f}{max_coords[1]:10.5f}{max_coords[2]:10.5f}\n")

        print("File exported to " + filename)
