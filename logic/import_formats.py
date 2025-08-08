from logic.graphene import Graphene

def readGRO(filename):
    with open(filename, 'r') as f:
        f.readline()
        natoms = int(f.readline().strip())

        plates = []
        carbons, oxides = [], []
        for _ in range(natoms):
            line = f.readline()
            molecnum = int(line[0:5])
            atomname = line[10:15].strip()
            atomid = int(line[15:20])
            x = float(line[20:28])
            y = float(line[28:36])
            z = float(line[36:44])

            if molecnum > len(plates)+1:
                plates.append(Graphene.create_from_coords(carbons, oxides))
                carbons, oxides = [], []

            if atomname.startswith("C"):
                carbons.append([x, y, z, atomname, atomid])
            else:
                oxides.append([x, y, z, atomname, atomid])

        plates.append(Graphene.create_from_coords(carbons, oxides))
    return plates

def readXYZ(filename):
    with open(filename, 'r') as f:
        natoms = int(f.readline().strip())
        f.readline()

        carbons, oxides = [], []
        for i in range(natoms):
            parts = f.readline().split()
            sym = parts[0]
            x = float(parts[1]) / 10.0
            y = float(parts[2]) / 10.0
            z = float(parts[3]) / 10.0

            atomname = sym

            if atomname == "C":
                carbons.append([x, y, z, "C", i+1])
            elif atomname == "O":
                oxides.append([x, y, z, "OE", i+1])
            elif atomname == "H":
                oxides[-1][3]= "OO"
                oxides.append([x, y, z, "HO", i+1])
            else:
                raise Exception("Unknown atom type: " + atomname)

        print("Create")
        print(len(carbons), len(oxides))
        plate = Graphene.create_from_coords(carbons, oxides)
        print("Change")
        change_name_carbons_oxidized(plate)
        print("Done")

    return [plate]

def change_name_carbons_oxidized(plate):
    carbons_list= plate.get_carbon_coords()
    for ox in plate.get_oxide_coords():
        for carb in plate.get_nearest_carbons_to_oxide(ox):
            carbons_list[carbons_list.index(carb)][3]= "CO"
        

def readPDB(filename):
    pass