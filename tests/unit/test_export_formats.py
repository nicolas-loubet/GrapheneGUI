import os
import tempfile
import unittest

from graphenegui.logic import export_formats as ef
from graphenegui.logic.graphene import Graphene


class TestChargeTable(unittest.TestCase):
    def test_charge_table_derived_from_atom_params(self):
        """CHARGE_TABLE (mol2) y ATOM_PARAMS_TOP (.top) tienen que seguir siendo
        la misma fuente de verdad, no dos números copiados a mano."""
        for key, params in ef.ATOM_PARAMS_TOP.items():
            self.assertEqual(ef.CHARGE_TABLE[key], params[1])

    def test_get_partial_charge_known(self):
        self.assertAlmostEqual(ef.get_partial_charge("HO"), 0.39)

    def test_get_partial_charge_unknown_defaults_zero(self):
        self.assertEqual(ef.get_partial_charge("XX"), 0.0)


class FakePlate:
    """Doble mínimo para testear locate_global_atom sin construir un Graphene real."""
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


if __name__ == "__main__":
    unittest.main()
