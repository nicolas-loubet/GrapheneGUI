from .graphene import Graphene

class _PlateAccumulator:
    """Junta átomos por número de molécula y va cerrando/abriendo placas a
    medida que ese número sube. Común a readGRO/readPDB/readMOL2."""
    def __init__(self, track_hydrogens=False):
        self.plates= []
        self.carbons= []
        self.oxides= []
        self.hydrogens= [] if track_hydrogens else None
        self.track_hydrogens= track_hydrogens
        self.current_molec= 0

    def start_new_plate_if_needed(self, molec_num):
        if molec_num > self.current_molec:
            self.close_plate()
            self.current_molec= molec_num

    def close_plate(self, force=False):
        if not (force or self.carbons or self.oxides): return
        if self.track_hydrogens:
            self.plates.append(Graphene.create_from_coords(self.carbons, self.oxides, self.hydrogens))
            self.hydrogens= []
        else:
            self.plates.append(Graphene.create_from_coords(self.carbons, self.oxides))
        self.carbons, self.oxides= [], []

def readGRO(filename):
    with open(filename, 'r') as f:
        f.readline()
        natoms= int(f.readline().strip())

        acc= _PlateAccumulator(track_hydrogens=True)
        for _ in range(natoms):
            line= f.readline()
            molecnum= int(line[0:5])
            atomname= line[10:15].strip()
            atomid= int(line[15:20])
            x= float(line[20:28])
            y= float(line[28:36])
            z= float(line[36:44])

            acc.start_new_plate_if_needed(molecnum)

            if atomname.startswith("C"):
                acc.carbons.append([x, y, z, atomname, atomid, False, "ca"])
            elif atomname.startswith("H") and not atomname.startswith("HO"):
                acc.hydrogens.append([x, y, z, atomname, atomid, False, "ha"])
            else:
                atomname_without_numbers= atomname
                while atomname_without_numbers[-1].isdigit():
                    atomname_without_numbers= atomname_without_numbers[:-1]
                acc.oxides.append([x, y, z, atomname_without_numbers, atomid, False, atomname_without_numbers])

        acc.close_plate(force=True)
    print("File read from " + filename)
    return acc.plates

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

        plate= Graphene.create_from_coords(carbons, oxides)
        change_name_carbons_oxidized(plate)

    print("File read from " + filename)
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
        acc= _PlateAccumulator(track_hydrogens=True)
        
        for line in f:
            if line.startswith("ATOM"):
                atom_id= int(line[6:11].strip())
                atom_name= line[12:16].strip()
                residue_name= line[17:20].strip()
                molec_num= int(residue_name[2:])
                x= float(line[30:38].strip()) / 10.0
                y= float(line[38:46].strip()) / 10.0
                z= float(line[46:54].strip()) / 10.0
                
                acc.start_new_plate_if_needed(molec_num)
                
                if atom_name.startswith("C"):
                    acc.carbons.append([x, y, z, atom_name, atom_id, False, "ca"])
                elif atom_name[:2] in ("OO", "HO", "OE"):
                    acc.oxides.append([x, y, z, atom_name[:2], atom_id, False, atom_name[:2]])
                elif atom_name.startswith("H"):
                    acc.hydrogens.append([x, y, z, atom_name, atom_id, False, "ha"])
                else:
                    raise Exception("Unknown atom type: " + atom_name)
        
        acc.close_plate()
        
        for plate in acc.plates:
            change_name_carbons_oxidized(plate)
    
    print("File read from " + filename)
    return acc.plates

def readMOL2(filename):
    with open(filename, 'r') as f:
        acc= _PlateAccumulator(track_hydrogens=True)
        current_section= None
        
        atom_type_map= {"ca": "C", "c3": "CO", "cx": "CE", "oh": "OO", "ho": "HO", "os": "OE", "ha": "H"}
        
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
                
                acc.start_new_plate_if_needed(residue_num)
                
                if internal_type.startswith("C"):
                    acc.carbons.append([x, y, z, internal_type, atom_id, False, "ca"])
                elif internal_type == "H":
                    acc.hydrogens.append([x, y, z, internal_type, atom_id, False, "ha"])
                else:
                    acc.oxides.append([x, y, z, internal_type, atom_id, False, internal_type])
        
        acc.close_plate()
        
        for plate in acc.plates:
            change_name_carbons_oxidized(plate)
    
    print("File read from " + filename)
    return acc.plates
