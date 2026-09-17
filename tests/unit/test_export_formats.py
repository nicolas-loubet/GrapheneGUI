import os
import tempfile
import unittest

from graphenegui.logic import export_formats as ef
from graphenegui.logic.graphene import Graphene


class TestChargeTable(unittest.TestCase):
    def test_charge_table_derived_from_atom_params(self):
        for key, params in ef.ATOM_PARAMS_TOP.items():
            self.assertEqual(ef.CHARGE_TABLE[key], params[1])

    def test_get_partial_charge_known(self):
        self.assertAlmostEqual(ef.get_partial_charge("HO"), 0.39)

    def test_get_partial_charge_unknown_defaults_zero(self):
        self.assertEqual(ef.get_partial_charge("XX"), 0.0)


class FakePlate:
    def __init__(self, n_atoms):
        self._n= n_atoms

    def get_number_atoms(self):
        return self._n


class TestLocateGlobalAtom(unittest.TestCase):
    def test_locate_within_first_plate(self):
        plates= [FakePlate(5), FakePlate(3)]
        self.assertEqual(ef.locate_global_atom(plates, 3), (0, 2))

    def test_locate_within_second_plate(self):
        plates= [FakePlate(5), FakePlate(3)]
        self.assertEqual(ef.locate_global_atom(plates, 6), (1, 0))

    def test_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            ef.locate_global_atom([FakePlate(5)], 99)


class TestWriteMol2Charges(unittest.TestCase):
    def test_mol2_has_real_charges_and_user_charges_header(self):
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        carbons= plate.get_carbon_coords()
        plate.add_oxydation_to_list_of_carbon(list(carbons), z_mode=2, prob_oh=100)

        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "test.mol2")
            ef.writeMOL2(path, [plate], [False, False])
            content= open(path).read()

        self.assertIn("USER_CHARGES", content)
        self.assertNotIn("NO_CHARGES", content)

        atom_block= content.split("@<TRIPOS>ATOM")[1].split("@<TRIPOS>BOND")[0]
        charges= [float(line.split()[-1]) for line in atom_block.strip().splitlines()]
        self.assertTrue(any(abs(c) > 1e-9 for c in charges))  # ya no todo 0.0000


class TestCheckBounds(unittest.TestCase):
    def test_periodicity_adds_expected_margin(self):
        plate= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        _, bounds_flat= ef.checkBounds([plate], [False, False])
        _, bounds_px= ef.checkBounds([plate], [True, False])
        _, bounds_py= ef.checkBounds([plate], [False, True])

        self.assertAlmostEqual(bounds_px[0] - bounds_flat[0], 0.1225 * plate.get_scale_factor(), places=6)
        self.assertAlmostEqual(bounds_py[1] - bounds_flat[1], 0.142 * plate.get_scale_factor(), places=6)

    def test_bounds_are_positive_for_nonempty_plate(self):
        plate= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        _, bounds= ef.checkBounds([plate], [False, False])
        self.assertGreater(bounds[0], 0)
        self.assertGreater(bounds[1], 0)


class TestMol2BondTypes(unittest.TestCase):
    def test_pure_carbon_plate_has_only_aromatic_bonds(self):
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "bonds.mol2")
            ef.writeMOL2(path, [plate], [False, False])
            content= open(path).read()

        bond_block= content.split("@<TRIPOS>BOND")[1].split("@<TRIPOS>SUBSTRUCTURE")[0]
        bond_types= {line.split()[-1] for line in bond_block.strip().splitlines()}
        self.assertEqual(bond_types, {"ar"})  # todo C-C en una placa sin oxidar


class TestWriteTopSmoke(unittest.TestCase):
    def test_top_export_with_custom_atom_type(self):
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        carbons= plate.get_carbon_coords()
        plate.add_oxydation_to_list_of_carbon(list(carbons), z_mode=2, prob_oh=100)

        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "test.top")
            from graphenegui.logic import core
            core.export_plates(path, [plate], [False, False],
                                atom_types={"ca2": {"epsilon": 0.3, "sigma": 3.2}},
                                duplicates_list=[[], []])
            self.assertTrue(os.path.exists(path))
            content= open(path).read()

        self.assertGreater(len(content), 0)
        self.assertIn("ca2", content)


if __name__ == "__main__":
    unittest.main()
