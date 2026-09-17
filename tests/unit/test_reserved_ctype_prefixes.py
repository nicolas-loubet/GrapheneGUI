import unittest
from graphenegui.logic import core


class TestBuildAtomTypesRejectsReservedPrefixes(unittest.TestCase):
    def test_rejects_exact_reserved_names(self):
        for bad in ["CE", "CO", "OE", "OO", "HO"]:
            with self.assertRaises(ValueError):
                core.build_atom_types({"atom_types": [{"name": bad, "epsilon": 0.1, "sigma": 3.0}]})

    def test_rejects_names_starting_with_reserved_prefix(self):
        for bad in ["CE2", "COx", "OE1", "OOxide", "HO99"]:
            with self.assertRaises(ValueError):
                core.build_atom_types({"atom_types": [{"name": bad, "epsilon": 0.1, "sigma": 3.0}]})

    def test_rejects_h_plus_digits_reserved_for_hydrogen_naming(self):
        for bad in ["H2", "H10", "H999", "H0"]:
            with self.assertRaises(ValueError):
                core.build_atom_types({"atom_types": [{"name": bad, "epsilon": 0.1, "sigma": 3.0}]})

    def test_allows_h_names_that_are_not_pure_digits(self):
        for ok_name in ["H2O", "Halo", "Hx"]:
            result= core.build_atom_types({"atom_types": [{"name": ok_name, "epsilon": 0.1, "sigma": 3.0}]})
            self.assertIn(ok_name, result)

    def test_allows_normal_names(self):
        for ok_name in ["ce", "co", "ca", "myType", "X1"]:
            result= core.build_atom_types({"atom_types": [{"name": ok_name, "epsilon": 0.1, "sigma": 3.0}]})
            self.assertIn(ok_name, result)

    def test_empty_atom_types_is_fine(self):
        self.assertEqual(core.build_atom_types({}), {})


if __name__ == "__main__":
    unittest.main()
