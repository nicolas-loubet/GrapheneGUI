# Graphene GUI

**Graphene GUI** is a GTK-based graphical interface for creating and functionalizing graphene and graphene oxide sheets. It allows fast construction, modification, and export of graphene structures for use in molecular simulations.

### Version: 0.5

## 🧪 Purpose

The aim of this program is to make it simple and fast to build custom graphene or graphene oxide models and export them in various formats compatible with simulation packages like **GROMACS**.


## 🖼️ Features

- Interactive creation of graphene plates.
- Oxidation of graphene based on pattern selection (with support for VMD-like boolean expressions) and random percentage.
- Manual addition/removal of oxide groups (OH and O).
- Multi-plate support for building layered systems.
- Export to:
  - `.gro` (GROMACS)
  - `.pdb` (standard PDB)
  - `.xyz` (XYZ format)
  - `.top` (topology for GROMACS)


## 🚀 Getting Started

### Prerequisites

You need a Linux system with the following installed:

- Python ≥ 3.6
- GTK+ 3 (via PyGObject)
- NumPy
- System dependencies: python3-gi, python3-gi-cairo, gir1.2-gtk-3.0

Install system dependencies via:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-numpy
```

### Installation

1. Clone the repository:

```bash
git clone https://github.com/nicolas-loubet/GrapheneGUI.git
cd GrapheneGUI/
```

2. Install the package using pip:

```bash
pip install .
```

Alternatively, install directly from GitHub:

```bash
pip install git+https://github.com/nicolas-loubet/GrapheneGUI.git
```

### Running the Program

After installation, run the program using:

```bash
graphene-gui
```

Or, if you prefer to run without installing, just download the repository and use:

```bash
python3 main.py
```

## 🧭 Typical Workflow
1. Create a graphene plate via the Create dialog.

2. Apply oxidation:

   - Use expressions like x > 10 and z < 5 to target specific atoms.

   - Control oxidation type (OH or O) and percentage.

3. Edit manually:

   - Add OH or O groups using the respective modes.

   - Remove existing oxide groups.

4. Add more plates if needed.

5. Export the system using the Export dialog and select .gro, .pdb, .xyz, or .top.


## 📁 File Formats
- .gro: Atom positions and box for GROMACS.

- .pdb: Standard atom coordinates.

- .xyz: Simple atomic format for visualization.

- .top: GROMACS-compatible topology with atoms, bonds, pairs, angles, and dihedrals.


## ⚙️ Internals
- Coordinates are stored in nanometers, presented in Å.

- Oxidation modes are determined by the Z direction:
  - +Z, -Z, or random.

- Atoms are classified with codes:
  - CE, CO → Carbon
  - OE, OO → Oxygen
  - HO → Hydrogen


## 📜 License
This project is licensed under the GNU General Public License (GPL).


## 👤 Author
Nicolás Alfredo Loubet
Email: nicolas.loubet@uns.edu.ar


## 📸 Screenshots

| Step | Screenshot | Description |
|------|------------|-------------|
| 1 | ![Create Plate](screenshots/1-create.png) | Creating a new graphene plate with custom dimensions and center position. |
| 2 | ![Reduced Graphene](screenshots/2-reduced_graphene.png) | A clean graphene sheet. You can see name and coordinates of each atom by placing the cursor over. |
| 3 | ![Oxidation Rules](screenshots/3-oxide_with_rules.png) | Applying oxidation using boolean expressions and random percentage. |
| 4 | ![Manual Oxide Adding](screenshots/4-manual_adding.png) | Manually adding OH and O groups to selected atoms. |
| 5 | ![Export Options](screenshots/5-export.png) | Export dialog for saving the system in `.gro`, `.pdb`, `.xyz`, or `.top` formats. |
| 6 | ![Multiple Plates](screenshots/6-add_multi_plates.png) | Adding multiple graphene plates to build stacked systems. |
| 7 | ![Use with VMD](screenshots/7-use_vmd_for_rendering.png) | Rendering the exported structure using VMD for visualization. |


## 📦 Future ideas
- LAMMPS export support
- Windows compatibility

