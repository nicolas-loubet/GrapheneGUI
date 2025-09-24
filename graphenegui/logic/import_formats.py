from .graphene import Graphene

def readGRO(filename):
    with open(filename, 'r') as f:
        f.readline()
        natoms= int(f.readline().strip())

        plates= []
        carbons, oxides= [], []
        for _ in range(natoms):
            line= f.readline()
            molecnum= int(line[0:5])
            atomname= line[10:15].strip()
            atomid= int(line[15:20])
            x= float(line[20:28])
            y= float(line[28:36])
            z= float(line[36:44])

            if molecnum > len(plates)+1:
                plates.append(Graphene.create_from_coords(carbons, oxides))
                carbons, oxides= [], []

            if atomname.startswith("C"):
                carbons.append([x, y, z, atomname, atomid, False, "ca"])
            else:
                atomname_without_numbers= atomname
                while atomname_without_numbers[-1].isdigit():
                    atomname_without_numbers= atomname_without_numbers[:-1]
                oxides.append([x, y, z, atomname_without_numbers, atomid, False, atomname_without_numbers])

        plates.append(Graphene.create_from_coords(carbons, oxides))
    return plates

def readXYZ(filename):
    with open(filename, 'r') as f:
        natoms= int(f.readline().strip())
        f.readline()

        carbons, oxides= [], []
        for i in range(natoms):
            parts= f.readline().split()
            sym= parts[0]
            x= float(parts[1]) / 10.0
            y= float(parts[2]) / 10.0
            z= float(parts[3]) / 10.0

            atomname= sym

            if atomname == "C":
                carbons.append([x, y, z, "C", i+1, False, "ca"])
            elif atomname == "O":
                oxides.append([x, y, z, "OE", i+1, False, "OE"])
            elif atomname == "H":
                oxides[-1][3]= "OO"
                oxides[-1][6]= "OO"
                oxides.append([x, y, z, "HO", i+1, False, "HO"])
            else:
                raise Exception("Unknown atom type: " + atomname)

        print("Create")
        print(len(carbons), len(oxides))
        plate= Graphene.create_from_coords(carbons, oxides)
        print("Change")
        change_name_carbons_oxidized(plate)
        print("Done")

    return [plate]

def change_name_carbons_oxidized(plate):
    carbons_list= plate.get_carbon_coords()
    for ox in plate.get_oxide_coords():
        for carb in plate.get_nearest_carbons_to_oxide(ox):
            if(ox[6] == "OO"):
                carbons_list[carbons_list.index(carb)][3]= "CO"
                carbons_list[carbons_list.index(carb)][6]= "CO"
            elif(ox[6] == "OE"):
                carbons_list[carbons_list.index(carb)][3]= "CE"
                carbons_list[carbons_list.index(carb)][6]= "CE"
        
def readPDB(filename):
    with open(filename, 'r') as f:
        plates= []
        carbons, oxides= [], []
        current_molec= 0
        
        for line in f:
            if line.startswith("ATOM"):
                atom_id= int(line[6:11].strip())
                atom_name= line[12:16].strip()
                residue_name= line[17:20].strip()
                molec_num= int(residue_name[2:])
                x= float(line[30:38].strip()) / 10.0
                y= float(line[38:46].strip()) / 10.0
                z= float(line[46:54].strip()) / 10.0
                
                if molec_num > current_molec:
                    if carbons or oxides:
                        plates.append(Graphene.create_from_coords(carbons, oxides))
                        carbons, oxides= [], []
                    current_molec= molec_num
                
                if atom_name.startswith("C"):
                    carbons.append([x, y, z, atom_name, atom_id, False, "ca"])
                elif atom_name[:2] in ("OO", "HO", "OE"):
                    oxides.append([x, y, z, atom_name[:2], atom_id, False, atom_name[:2]])
                else:
                    raise Exception("Unknown atom type: " + atom_name)
        
        if carbons or oxides:
            plates.append(Graphene.create_from_coords(carbons, oxides))
        
        for plate in plates:
            change_name_carbons_oxidized(plate)
    
    print("File read from " + filename)
    return plates

def readMOL2(filename):
    with open(filename, 'r') as f:
        plates= []
        carbons, oxides= [], []
        current_molec= 0
        current_section= None
        
        atom_type_map= {"ca": "C", "c3": "CO", "cx": "CE", "oh": "OO", "ho": "HO", "os": "OE"}
        
        for line in f:
            line= line.strip()
            if line.startswith("@<TRIPOS>"):
                current_section= line[9:]
                continue
            
            if current_section == "ATOM":
                parts= line.split()
                if len(parts) < 9:
                    continue
                atom_id= int(parts[0])
                x= float(parts[2]) / 10.0
                y= float(parts[3]) / 10.0
                z= float(parts[4]) / 10.0
                mol2_type= parts[5]
                residue_num= int(parts[6])
                
                internal_type= atom_type_map.get(mol2_type, "C")
                
                if residue_num > current_molec:
                    if carbons or oxides:
                        plate= Graphene.create_from_coords(carbons, oxides)
                        plates.append(plate)
                        carbons, oxides= [], []
                    current_molec= residue_num
                
                if internal_type.startswith("C"):
                    carbons.append([x, y, z, internal_type, atom_id, False, "ca"])
                else:
                    print(internal_type)
                    oxides.append([x, y, z, internal_type, atom_id, False, internal_type])
        
        if carbons or oxides:
            plate= Graphene.create_from_coords(carbons, oxides)
            plates.append(plate)
        
        for plate in plates:
            change_name_carbons_oxidized(plate)
    
    print("File read from " + filename)
    return plates
