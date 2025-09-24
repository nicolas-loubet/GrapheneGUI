# Graphene GUI

**Graphene GUI** is a Qt (PySide6)-based graphical interface for creating and functionalizing graphene and graphene oxide slabs. It allows rapid construction, modification, and export of graphene structures for molecular simulations.

### Versión: 3.4

## 🧪 Purpose

The program's goal is to facilitate and accelerate the creation of customized graphene and oxidized graphene models, exportable in multiple formats compatible with simulation packages such as **GROMACS** and **AMBER**.

## 🖼️ Features

- Interactive creation of graphene slabs.
- Oxidation based on selection using Boolean expressions (VMD type) and random percentage.
- Manual addition and removal of oxide groups (OH and O).
- Multi-slab support for stacked systems.
- Export in formats:
  - `.gro` (GROMACS)
  - `.pdb` (standard PDB format)
  - `.xyz` (simple XYZ format)
  - `.top` (topology for GROMACS)
  - `.mol2` (MOL2 format for computational chemistry)
- Convert graphene to CNT (zigzag or armchair)

## 🚀 Getting Started

### Prerequisites

- Python ≥ 3.6
- [PySide6](https://pypi.org/project/PySide6/)
- NumPy

## Installation on Linux

### Option 1: Using pip (recommended if possible)


1. Clone the repository:

```bash
git clone https://github.com/nicolas-loubet/GrapheneGUI.git && cd GrapheneGUI/
```

2. Install requirements:

Make sure you have Python 3.8+ installed.

```bash
pip install -r requirements.txt
```

> **Note:** If you find an error at this point, try option 2.

3. Install the package using pip:

```bash
pip install .
```

4. After installation, run the program using:

```bash
graphene-gui
```

Alternatively, install directly from GitHub:

```bash
pip install git+https://github.com/nicolas-loubet/GrapheneGUI.git
```

And run with:

```bash
python3 main.py
```

### Option 2: If you get the "externally-managed-environment" error

On modern Linux distributions (Ubuntu 23.04+, Debian 12+, etc.), the system Python is externally managed according to PEP 668.
This means pip cannot install packages system-wide to avoid breaking the OS.

If you see an error like:

```bash
error: externally-managed-environment
× This environment is externally managed
```

You have some safe alternatives. I recommend creating a virtual environment.

This is the most flexible option and works everywhere.

```bash
python3 -m venv graphene-gui-env && source graphene-gui-env/bin/activate && pip install git+https://github.com/nicolas-loubet/GrapheneGUI.git
```

Then you just run it with

```bash
graphene-gui
```

### Option 3: Manual running

Also, you can just download the repository and run it:

```bash
python3 main.py
```


## Installation on Windows

### 1) Download Python 3
Go to the official website:  
🔗 https://www.python.org/downloads/windows/  
Click on **Download Python 3.x.x** (choose the latest stable version).

### 2) Download the ZIP from GitHub
In the top-right corner of this page, click the green **Code** button, select **Download ZIP**, and save it on your computer (e.g., in your *Downloads* folder).

### 3) Extract the ZIP
Navigate to the folder where you saved the ZIP file.  
Right-click it, choose **Extract All**, and select your target destination (e.g., `C:\Users\<YourUser>\Documents\GrapheneGUI`).

### 4) Open the folder in Windows Terminal
Go to the extracted project folder.  
Right-click on an empty space inside the folder and choose **Open in Windows Terminal** (or **Open in PowerShell**, depending on your Windows version).

### 5) Continue with installation
Once the terminal is open in the project folder, run the following command to install dependencies:

```powershell
pip install -r requirements.txt
```

### 6) Run the project from the module
> Note: There is no main.py in the root directory. Instead, the application runs from the graphenegui module using __main__.py. Therefore, use:

```powershell
python -m graphenegui
```

If it fails, it could be that you need to use `py -m graphenegui` instead.

📌 Important: Make sure your terminal's current directory is the one containing graphenegui, requirements.txt, etc. For example:

```powershell
cd "C:\Users\<YourUser>\Documents\GrapheneGUI\GrapheneGUI-main\GrapheneGUI-main"
python -m graphenegui
```

## 🧭 Typical Workflow
1. Create a graphene plate via the `Create` button (+ sign).

2. Apply oxidation:

   - Use expressions like "x > 10 and y < 5" or equivalent to target specific atoms.

   - Control oxidation type (OH or O) and percentage.

3. Edit manually:

   - Add `OH` or `O` groups using the respective modes.

   - Remove existing oxide groups.

4. Add more plates if needed.

5. Export the system using the `Export` dialog and select .gro, .pdb, .xyz, .mol2, or .top.


## 📁 File Formats
- .gro: Atom positions and box for GROMACS.

- .pdb: Standard atom coordinates.

- .xyz: Simple atomic format for visualization.

- .mol2: Coordinates + Bond information

- .top: GROMACS-compatible topology with atoms, bonds, pairs, angles, and dihedrals.


## ⚙️ Internals
- Coordinates are stored in nanometers, presented in Å.

- Oxidation modes are determined by the Z direction:
  - +Z, -Z, or random.

- Atoms are classified with codes:
  - C → Carbon sp2
  - CE, CO → Carbon sp3
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
- AMBER names compatibility
- Auto add H in the borders
- More atoms / groups available
