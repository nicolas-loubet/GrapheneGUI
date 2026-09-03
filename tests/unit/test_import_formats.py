import os
import tempfile
import unittest

from graphenegui.logic import export_formats as ef
from graphenegui.logic import import_formats as inf
from graphenegui.logic.graphene import Graphene
from graphenegui.logic.import_formats import _PlateAccumulator


class TestPlateAccumulator(unittest.TestCase):
    def test_closes_plate_on_molec_change(self):
        # Graphene.create_from_coords necesita >=2 carbonos por placa para calcular
        # el scale_factor (mide distancia al vecino más cercano), así que cada
        # "placa" de prueba lleva 2 carbonos a distancia real de enlace C-C (~0.142 nm).
        acc= _PlateAccumulator()
        acc.start_new_plate_if_needed(1)
        acc.carbons.append([0.0, 0.0, 0.0, "C1", 1, False, "ca"])
        acc.carbons.append([0.142, 0.0, 0.0, "C2", 2, False, "ca"])
        acc.start_new_plate_if_needed(1)   # mismo molec: no cierra nada
        acc.carbons.append([0.284, 0.0, 0.0, "C3", 3, False, "ca"])
        acc.start_new_plate_if_needed(2)   # sube el molec: cierra la placa 1 (3 carbonos)
        acc.carbons.append([0.0, 0.142, 0.0, "C4", 4, False, "ca"])
        acc.carbons.append([0.142, 0.142, 0.0, "C5", 5, False, "ca"])
        acc.close_plate()

        self.assertEqual(len(acc.plates), 2)
        self.assertEqual(acc.plates[0].get_number_atoms(), 3)
        self.assertEqual(acc.plates[1].get_number_atoms(), 2)

    def test_close_plate_guarded_by_default(self):
        acc= _PlateAccumulator()
        acc.close_plate()  # nada acumulado: no crea una placa vacía
        self.assertEqual(len(acc.plates), 0)

    def test_close_plate_force_on_empty_accumulator_raises(self):
        """Límite conocido, heredado del comportamiento original: si el acumulador
        está totalmente vacío (ej. un .gro con natoms=0), Graphene.create_from_coords
        no puede calcular el scale_factor (necesita >=2 carbonos) y explota con
        IndexError. Ya pasaba en el código viejo (append incondicional al final de
        readGRO) — no es una regresión de _PlateAccumulator, queda documentado acá."""
        acc= _PlateAccumulator()
        with self.assertRaises(IndexError):
            acc.close_plate(force=True)


class TestMol2RoundTrip(unittest.TestCase):
    def test_roundtrip_preserves_atom_count(self):
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        carbons= plate.get_carbon_coords()
        plate.add_oxydation_to_list_of_carbon(list(carbons), z_mode=2, prob_oh=100)
        n_before= plate.get_number_atoms()

        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "roundtrip.mol2")
            ef.writeMOL2(path, [plate], [False, False])
            plates_read= inf.readMOL2(path)

        self.assertEqual(len(plates_read), 1)
        self.assertEqual(plates_read[0].get_number_atoms(), n_before)


class TestGroRoundTrip(unittest.TestCase):
    def test_roundtrip_preserves_atom_count(self):
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        n_before= plate.get_number_atoms()

        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "roundtrip.gro")
            ef.writeGRO(path, [plate], [False, False])
            plates_read= inf.readGRO(path)

        self.assertEqual(len(plates_read), 1)
        self.assertEqual(plates_read[0].get_number_atoms(), n_before)

    def test_border_hydrogens_survive_roundtrip_not_miscounted_as_carbon(self):
        """Regresión Etapa T1: readMOL2 no tenía 'ha' (el tipo SYBYL de los H de
        borde) en atom_type_map -> caía al default 'C' -> un hidrógeno de borde
        se leía como si fuera un carbono (corrupción silenciosa, peor que un
        crash). Ahora 'ha' mapea a H y se trackea aparte."""
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        plate.reduce_borders()
        n_h_before= len(plate.get_hydrogens_coords())
        n_c_before= len(plate.get_carbon_coords())
        self.assertGreater(n_h_before, 0)

        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "with_borders.mol2")
            ef.writeMOL2(path, [plate], [False, False])
            plates_read= inf.readMOL2(path)

        self.assertEqual(len(plates_read[0].get_hydrogens_coords()), n_h_before)
        self.assertEqual(len(plates_read[0].get_carbon_coords()), n_c_before)  # no inflado con H


class TestXyzRoundTrip(unittest.TestCase):
    def test_roundtrip_preserves_atom_count(self):
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        n_before= plate.get_number_atoms()

        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "roundtrip.xyz")
            ef.writeXYZ(path, [plate], [False, False])
            plates_read= inf.readXYZ(path)

        self.assertEqual(len(plates_read), 1)
        self.assertEqual(plates_read[0].get_number_atoms(), n_before)


class TestPdbRoundTrip(unittest.TestCase):
    def test_roundtrip_preserves_atom_count(self):
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        n_before= plate.get_number_atoms()

        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "roundtrip.pdb")
            ef.writePDB(path, [plate], [False, False])
            plates_read= inf.readPDB(path)

        self.assertEqual(len(plates_read), 1)
        self.assertEqual(plates_read[0].get_number_atoms(), n_before)

    def test_border_hydrogens_survive_roundtrip(self):
        """Regresión Etapa T1: readPDB no trackeaba hidrógenos de borde -- un H
        de nombre 'H1' no matcheaba ni carbono ni óxido y explotaba con
        'Unknown atom type'. Ahora se trackean igual que en readGRO."""
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        plate.reduce_borders()
        n_h_before= len(plate.get_hydrogens_coords())
        n_c_before= len(plate.get_carbon_coords())
        self.assertGreater(n_h_before, 0)  # que el test realmente ejercite algo

        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "with_borders.pdb")
            ef.writePDB(path, [plate], [False, False])
            plates_read= inf.readPDB(path)  # no debe explotar

        self.assertEqual(len(plates_read[0].get_hydrogens_coords()), n_h_before)
        self.assertEqual(len(plates_read[0].get_carbon_coords()), n_c_before)  # sin H mezclados acá


if __name__ == "__main__":
    unittest.main()
