from .graphene import Graphene

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

def checkBounds(plates):
    max_coords = [0.0, 0.0, 0.0]
    min_coords = [0.0, 0.0, 0.0]

    for plate in plates:
        atoms= plate.get_carbon_coords() + plate.get_oxide_coords()

        for coord in atoms:
            x,y,z= coord[:3]
            min_coords[0] = min(min_coords[0], x)
            min_coords[1] = min(min_coords[1], y)
            min_coords[2] = min(min_coords[2], z)
            max_coords[0] = max(max_coords[0], x)
            max_coords[1] = max(max_coords[1], y)
            max_coords[2] = max(max_coords[2], z)

    max_coords[0] -= min_coords[0]
    max_coords[1] -= min_coords[1]
    max_coords[2] -= min_coords[2]

    return min_coords, max_coords

def writeGRO(filename, plates):
    with open(filename, 'w') as f:
        f.write("Graphene, generated with Graphene GUI.\n")
        total_atoms = sum(len(plate.get_carbon_coords()) + len(plate.get_oxide_coords()) for plate in plates)
        f.write(f"{total_atoms}\n")

        min_coords,bounds= checkBounds(plates)
        for i_plate,plate in enumerate(plates):
            atoms= plate.get_carbon_coords() + plate.get_oxide_coords()
            for coord in atoms:
                x,y,z,name,i_atom= coord[:5]
                f.write(formatGRO((i_plate + 1, "GR"+str(i_plate+1), name, i_atom, x-min_coords[0], y-min_coords[1], z-min_coords[2])))

        f.write(f"{bounds[0]:10.5f}{bounds[1]:10.5f}{bounds[2]:10.5f}\n")

        print("File exported to " + filename)

def writeXYZ(filename, plates):
    symbol_dict = {
        "CE": "C", "CO": "C",
        "OE": "O", "OO": "O",
        "HO": "H"
    }
    with open(filename, 'w') as f:
        all_atoms = []
        for plate in plates:
            all_atoms += plate.get_carbon_coords() + plate.get_oxide_coords()

        f.write(f"{len(all_atoms)}\n")
        f.write("Graphene structure exported in XYZ format.\n")

        min_coords,bounds= checkBounds(plates)

        for atom in all_atoms:
            x, y, z, name = atom[:4]
            symbol = symbol_dict.get(name[:2],"C")
            f.write(f"{symbol} {(x-min_coords[0])*10:.6f} {(y-min_coords[1])*10:.6f} {(z-min_coords[2])*10:.6f}\n")

        print("File exported to " + filename)

def writePDB(filename, plates):
    symbol_dict = {"C": "C", "CO": "C", "CE": "C", "OO": "O", "HO": "H", "OE": "O"}
    
    with open(filename, 'w') as f:
        f.write("REMARK Graphene structure generated with Graphene GUI\n")
        
        all_atoms = []
        for plate in plates:
            all_atoms += plate.get_carbon_coords() + plate.get_oxide_coords()
        
        min_coords, bounds = checkBounds(plates)
        
        f.write(f"CRYST1{bounds[0]*10:9.3f}{bounds[1]*10:9.3f}{bounds[2]*10:9.3f}  90.00  90.00  90.00 P 1           1\n")
        
        for i_plate, plate in enumerate(plates):
            atoms = plate.get_carbon_coords() + plate.get_oxide_coords()
            residue_name = f"GR{i_plate+1}"
            for i_atom, atom in enumerate(atoms, 1):
                x, y, z, name = atom[:4]
                x_ang = (x - min_coords[0]) * 10
                y_ang = (y - min_coords[1]) * 10
                z_ang = (z - min_coords[2]) * 10
                element = symbol_dict.get(name, "C")
                f.write(f"ATOM  {i_atom:5d} {name:<4} {residue_name:3} X{i_plate+1:4d}    "
                        f"{x_ang:8.3f}{y_ang:8.3f}{z_ang:8.3f}  0.00  0.00      SHT {element:>2}\n")
        
        f.write("END\n")
    
    print("File exported to " + filename)

def writeMOL2(filename, plates, factor=1.0):
    atom_type_dict = {"C": "ca", "CO": "c3", "CE": "cx", "OO": "oh", "HO": "ho", "OE": "os"}
    
    with open(filename, 'w') as f:
        total_atoms = sum(len(plate.get_carbon_coords()) + len(plate.get_oxide_coords()) for plate in plates)
        bonds = []
        for i_plate, plate in enumerate(plates):
            plate_bonds = get_bonds_top(plate, factor)
            for bond in plate_bonds:
                offset = sum(len(p.get_carbon_coords()) + len(p.get_oxide_coords()) for p in plates[:i_plate])
                bonds.append([bond[0] + offset, bond[1] + offset])
        
        total_residues = len(plates)
        
        f.write("@<TRIPOS>MOLECULE\n")
        f.write("GrapheneGUI\n")
        f.write(f"{total_atoms:>6} {len(bonds):>6} {total_residues:>6}    0    0\n")
        f.write("SMALL\nNO_CHARGES\n\n")
        f.write("File created by GrapheneGUI\n")
        
        f.write("@<TRIPOS>ATOM\n")
        min_coords, _ = checkBounds(plates)
        global_atom_id = 1
        for i_plate, plate in enumerate(plates):
            residue_name = f"GRA{i_plate+1}"
            atoms = plate.get_carbon_coords() + plate.get_oxide_coords()
            for atom in atoms:
                x, y, z, name = atom[:4]
                x_ang = (x - min_coords[0]) * 10
                y_ang = (y - min_coords[1]) * 10
                z_ang = (z - min_coords[2]) * 10
                mol2_type = atom_type_dict.get(name, atom_type_dict["C"])
                if(mol2_type == atom_type_dict["C"]):
                    list_ox= plate.get_oxides_for_carbon(atom)
                    if(len(list_ox) != 0):
                        if(list_ox[0][3] == "OO"): mol2_type= atom_type_dict.get("CO")
                        if(list_ox[0][3] == "OE"): mol2_type= atom_type_dict.get("CE")
                f.write(f"{global_atom_id:>7} {name:<8} {x_ang:>8.4f} {y_ang:>8.4f} {z_ang:>8.4f} "
                        f"{mol2_type:<8} {i_plate+1:>3} {residue_name:<8} 0.0000\n")
                global_atom_id += 1
        
        f.write("@<TRIPOS>BOND\n")
        for i, bond in enumerate(bonds, 1):
            ai, aj = bond
            plate_idx_ai = 0
            plate_idx_aj = 0
            atom_count = 0
            for i_plate, plate in enumerate(plates):
                plate_atoms = len(plate.get_carbon_coords()) + len(plate.get_oxide_coords())
                if ai - 1 < atom_count + plate_atoms:
                    plate_idx_ai = i_plate
                    local_idx_ai = (ai - 1) - atom_count
                    break
                atom_count += plate_atoms
            atom_count = 0
            for i_plate, plate in enumerate(plates):
                plate_atoms = len(plate.get_carbon_coords()) + len(plate.get_oxide_coords())
                if aj - 1 < atom_count + plate_atoms:
                    plate_idx_aj = i_plate
                    local_idx_aj = (aj - 1) - atom_count
                    break
                atom_count += plate_atoms
            atom_ai = (plates[plate_idx_ai].get_carbon_coords() + plates[plate_idx_ai].get_oxide_coords())[local_idx_ai]
            atom_aj = (plates[plate_idx_aj].get_carbon_coords() + plates[plate_idx_aj].get_oxide_coords())[local_idx_aj]
            bond_type = "ar" if atom_ai[3].startswith("C") and atom_aj[3].startswith("C") else "1"
            f.write(f"{i:>6} {ai:>4} {aj:>4} {bond_type}\n")
        
        f.write("@<TRIPOS>SUBSTRUCTURE\n")
        global_atom_id = 1
        for i_plate, plate in enumerate(plates):
            residue_name = f"GRA{i_plate+1}"
            f.write(f"{i_plate+1:>6} {residue_name:<8} {global_atom_id:>4} RESIDUE           1 X     GRA     2 ROOT\n")
            global_atom_id += len(plate.get_carbon_coords()) + len(plate.get_oxide_coords())
    
    print("File exported to " + filename)

def writeTOP(filename, plates, duplicate_list, atom_types, progress_callback):
    list_carbons= ""
    for a_type in atom_types:
        sigma,epsilon= atom_types[a_type]["sigma"]/10, atom_types[a_type]["epsilon"]
        epsilon_formatted= f"{epsilon:.5e}"
        if epsilon_formatted[-2] == 'e': epsilon_formatted= epsilon_formatted[:-1] + '0' + epsilon_formatted[-1]
        sigma_formatted= f"{sigma:.5e}"
        if sigma_formatted[-2] == 'e': sigma_formatted= sigma_formatted[:-1] + '0' + sigma_formatted[-1]
        list_carbons+= f" {a_type:<4}     {a_type:<4}       12.01000  0.00000   A    {sigma_formatted:>12}  {epsilon_formatted:>12}\n"
        list_carbons+= f" c{a_type:<3}     c{a_type:<3}       12.01000  0.18000   A    {sigma_formatted:>12}  {epsilon_formatted:>12}\n"

    top= ["; Topology created with Graphene-GUI\n\n",
        "[ defaults ]\n",
        "; nbfunc        comb-rule       gen-pairs       fudgeLJ fudgeQQ\n",
        "1               2               yes             0.5     0.8333\n\n",
        "[ atomtypes ]\n",
        ";name   bond_type     mass     charge   ptype   sigma         epsilon\n",
        list_carbons,
        " os       os         15.99940 -0.36000   A     3.16600e-01   6.49775e-01\n",
        " oh       oh         15.99940 -0.57000   A     3.16600e-01   6.49775e-01\n",
        " ho       ho          1.00800  0.39000   A     0.00000e+00   0.00000e+00\n\n"]
    
    molecules_count= ""

    for i_plate,plate in enumerate(plates):
        if i_plate+1 in duplicate_list[0]: continue

        name_molecule= f"GR{i_plate+1}"
        n_atoms= len(plate.get_carbon_coords()) + len(plate.get_oxide_coords())

        top.append("[ moleculetype ]\n;name            nrexcl\n "+name_molecule.ljust(5)+"            3\n")
        top.append("\n[ atoms ]\n")
        top.append(write_atoms_top(plate, i_plate+1))

        bonds= get_bonds_top(plate, plate.get_scale_factor(), progress_callback, i_plate+1, len(plates))
        if(len(bonds) > 0):
            top.append("\n[ bonds ]\n")
            top.append(write_bonds_top(bonds,"   1    1.4140e-01    2.8937e+05"))
            top.append("\n[ pairs ]\n")
            pairs,angles,dihedrals= get_pairs_angles_dihedrals(bonds,n_atoms,progress_callback, i_plate+1, len(plates))
            top.append(write_pairs_top(pairs))
            top.append("\n[ angles ]\n")
            top.append(write_angles_top(angles,plate))
            top.append("\n[ dihedrals ]\n")
            top.append(write_dihedrals_top(dihedrals))
            top.append(write_posres_top(plate))

        repetitions= duplicate_list[1].count(i_plate+1) + 1
        molecules_count += " "+name_molecule.ljust(6)+f"       {repetitions:>5}\n"

    top.append("\n\n[ system ]\nGraphene-GUI\n\n[ molecules ]\n; Compound        nmols\n"+molecules_count)

    with open(filename, 'w') as f:
        f.writelines(top)
    print("File exported to " + filename)

def write_atoms_top(plate, i_molec):
    output= ";   nr  type  resi  res  atom  cgnr     charge      mass\n"
    atoms= plate.get_carbon_coords() + plate.get_oxide_coords()
    name_molec= f"GR{i_molec}"

    atom_type_dict= {
        "CE": ["c",0.18,12.01],
        "CO": ["c",0.18,12.01],
        "OE": ["os",-0.36,15.9994],
        "OO": ["oh",-0.57,15.9994],
        "HO": ["ho",0.39,1.008],
    }
    
    for i,atom in enumerate(atoms):
        name_atom,i_atom= atom[3],atom[4]
        atom_type, q, mass = atom_type_dict.get(name_atom, ["ca", 0.0, 12.01])
            
        output+= str(i+1).rjust(6)
        output+= atom_type.rjust(5)
        output+= str(i_molec).rjust(6)
        output+= name_molec.rjust(6)
        output+= name_atom.rjust(6)
        output+= str(i_atom).rjust(5)
        output+= str("{:.6f}".format(q)).rjust(13)
        output+= str("{:.5f}".format(mass)).rjust(13)
        output+= "\n"
    return output

def get_bonds_top(plate, factor, progress_callback=None, number_present_plate=None, number_total_plates=None):
    r_dist= .146*factor
    output= []

    carbons= plate.get_carbon_coords()
    oxides= plate.get_oxide_coords()
    n_carbons= len(carbons)
    n_oxides= len(oxides)
    factor_division_total= 0.5*(n_carbons+n_oxides)
    for ai in range(n_carbons):
        if progress_callback:
            progress_callback((number_present_plate-1+(ai+1)*factor_division_total)/number_total_plates)
        print(f"TOP: Evaluating bonds carbons {ai+1:5} / {n_carbons:5}"+" "*20,end="\r")
        for aj in range(ai+1,n_carbons):
            if(plate.distance_3D(carbons[ai][0],carbons[ai][1],carbons[ai][2],carbons[aj][0],carbons[aj][1],carbons[aj][2]) < r_dist):
                output.append([ai+1,aj+1])

    r_dist+= .02*factor
    for ai in range(n_oxides):
        if progress_callback:
            progress_callback((number_present_plate-1+(ai+1+n_carbons)*factor_division_total)/number_total_plates)
        print(f"TOP: Evaluating bonds oxides {ai+1:5} / {n_oxides:5}"+" "*20,end="\r")
        if oxides[ai][3].startswith("H"): continue
        for aj in range(n_carbons):
            if(plate.distance_3D(oxides[ai][0],oxides[ai][1],oxides[ai][2],carbons[aj][0],carbons[aj][1],carbons[aj][2]) < r_dist):
                output.append([ai+1+n_carbons,aj+1])

        if oxides[ai][3] == "OO":
            output.append([ai+1+n_carbons,ai+2+n_carbons]) # Always next to each other
    
    return output

def get_pairs_angles_dihedrals(bonds,n_atoms, progress_callback, number_present_plate, number_total_plates):
    pairs, angles, dihedrals= [], [], []
    factor_division_total= 0.5/n_atoms

    for i in range(1,n_atoms+1):
        progress_callback((number_present_plate-0.5 + i*factor_division_total)/number_total_plates)
        print(f"TOP: Evaluating pairs & angles {i:5} / {n_atoms:5}"+" "*20,end="\r")
        for neighbor_1 in get_bounded(bonds,i):
            for neighbor_2 in get_bounded(bonds,neighbor_1):
                if(i == neighbor_2): continue
                if(not [i,neighbor_1,neighbor_2] in angles and not [neighbor_2,neighbor_1,i] in angles):
                    angles.append([i,neighbor_1,neighbor_2])
                for neighbor_3 in get_bounded(bonds,neighbor_2):
                    if(neighbor_1 == neighbor_3): continue
                    if(not [neighbor_3,i] in pairs and not [i,neighbor_3] in pairs):
                        pairs.append([i,neighbor_3])
                    if(not already_exists([i,neighbor_1,neighbor_2,neighbor_3],dihedrals)):
                        dihedrals.append([i,neighbor_1,neighbor_2,neighbor_3])

    print(f"Pairs computed: {len(pairs):5}, Angles computed: {len(angles):5}, Dihedrals computed: {len(dihedrals):5}")
    return pairs,angles,dihedrals

def get_bounded(bonds,i):
    output= []
    for b in bonds:
        if(b[0] == i): output.append(b[1])
        if(b[1] == i): output.append(b[0])
    return output

def already_exists(searched,list_values):
    val_s= sorted(searched)
    for val in list_values:
        val_s2= sorted(val)
        if(val_s == val_s2): return True
    return False

def write_bonds_top(bonds,frk):
    output= ";   ai     aj funct   r             k\n"
    for b in bonds:
        output+= str(b[0]).rjust(6)
        output+= str(b[1]).rjust(7)
        output+= frk+"\n"
    return output

def write_pairs_top(pairs):
    output= ";   ai     aj    funct\n"
    for p in pairs:
        if(len(set(p)) != len(p)): continue
        output+= str(p[0]).rjust(6)
        output+= str(p[1]).rjust(7)
        output+= "      1\n"
    return output

def write_angles_top(angles,plate):
    output= ";   ai     aj     ak    funct   theta         cth\n"
    for ang in angles:
        output+= str(ang[0]).rjust(6)
        output+= str(ang[1]).rjust(7)
        output+= str(ang[2]).rjust(7)
        output+= "      1"
        output+= str("{:.2f}".format(180)).rjust(14)
        output+= "    5.6233e+02\n"
    return output

def write_dihedrals_top(dihedrals):
    output= ";    i      j      k      l   func   phase     kd      pn\n"
    for dih in dihedrals:
        if(len(set(dih)) != len(dih)): continue
        for d,space in zip(dih,[6,7,7,7]):
            output+= str(d).rjust(space)
        output+= "      9"
        output+= "   180.00"
        output+= "  15.16700   2\n"
    return output

def write_posres_top(plate):
    output= "\n#ifdef POSRES\n[ position_restraints ]\n;  i funct       fcx        fcy        fcz\n"
    atoms= plate.get_carbon_coords() + plate.get_oxide_coords()
    for i in range(len(atoms)):
        if atoms[i][3] == "HO": continue
        output+= str(i+1).rjust(4)
        output+= "    1       20000       20000       20000\n"
    output+= "\n#endif\n"
    return output
