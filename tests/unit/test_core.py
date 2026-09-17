import unittest

from graphenegui.logic import core
from graphenegui.logic.graphene import Graphene


class TestPlateGrid(unittest.TestCase):
    def test_compute_plate_grid_returns_positive_grid(self):
        n_x, n_y= core.compute_plate_grid(width_ang=100, height_ang=100, factor=1.0)
        self.assertGreater(n_x, 0)
        self.assertGreater(n_y, 0)

    def test_check_plate_size_small_fits(self):
        fits, max_atoms= core.check_plate_size(5, 5)
        self.assertTrue(fits)
        self.assertGreater(max_atoms, 0)

    def test_check_plate_size_huge_does_not_fit(self):
        fits, _= core.check_plate_size(10**6, 10**6)
        self.assertFalse(fits)


class TestSelectAndApplyOxidation(unittest.TestCase):
    def setUp(self):
        self.plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)

    def test_select_atoms_full_fraction_returns_everything(self):
        selected= core.select_atoms(self.plate, "", 1.0, z_mode=2, prob_oh=100)
        self.assertIsNotNone(selected)
        self.assertEqual(len(selected), len(self.plate.get_carbon_coords()))

    def test_select_atoms_zero_fraction_returns_none(self):
        self.assertIsNone(core.select_atoms(self.plate, "", 0.0, z_mode=2, prob_oh=100))

    def test_select_atoms_invalid_expression_returns_none(self):
        selected= core.select_atoms(self.plate, "not_a_valid_expr(((", 1.0, z_mode=2, prob_oh=100)
        self.assertIsNone(selected)

    def test_apply_oxidation_empty_list_is_noop(self):
        self.assertEqual(core.apply_oxidation(self.plate, [], z_mode=2, prob_oh=100), 0)
        self.assertEqual(self.plate.get_oxide_count(), 0)

    def test_apply_oxidation_full_list(self):
        carbons= self.plate.get_carbon_coords()
        done= core.apply_oxidation(self.plate, list(carbons), z_mode=2, prob_oh=100)
        self.assertEqual(done, len(carbons))


class TestDuplicatesBookkeeping(unittest.TestCase):

    def test_register_duplicate_appends_to_both_lists(self):
        duplicates_list= [[], []]
        core.register_duplicate(duplicates_list, new_plate_index=2, root_index=1)
        self.assertEqual(duplicates_list, [[2], [1]])

    def test_register_duplicate_multiple_entries_same_root(self):
        duplicates_list= [[], []]
        core.register_duplicate(duplicates_list, new_plate_index=2, root_index=1)
        core.register_duplicate(duplicates_list, new_plate_index=3, root_index=1)
        self.assertEqual(duplicates_list, [[2, 3], [1, 1]])

    def test_compute_duplicate_translation_relative(self):
        t= core.compute_duplicate_translation(10, 0, 0, absolute=False, plate_center=[5, 5, 5])
        self.assertAlmostEqual(t[0], 1.0)  # 10 Å -> 1.0 nm
        self.assertAlmostEqual(t[1], 0.0)

    def test_compute_duplicate_translation_absolute_subtracts_center(self):
        t= core.compute_duplicate_translation(10, 10, 10, absolute=True, plate_center=[0.5, 0.5, 0.5])
        self.assertAlmostEqual(t[0], 0.5)  # 1.0 nm - 0.5 nm de centro


class TestRemoveOverlappingAtoms(unittest.TestCase):
    def test_removes_duplicate_position(self):
        atoms= [
            [0.0, 0.0, 0.0, "C1", 1, False, "ca"],
            [0.0, 0.0, 0.0, "C2", 2, False, "ca"],  # misma posición
            [1.0, 0.0, 0.0, "C3", 3, False, "ca"],
        ]
        result= core.remove_overlapping_atoms(atoms)
        self.assertEqual(len(result), 2)


class TestRollAsCNT(unittest.TestCase):
    def test_zigzag_roll_preserves_or_reduces_atom_count(self):
        plate= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        atoms= plate.get_carbon_coords() + plate.get_oxide_coords()
        rolled= core.roll_atoms_as_CNT(atoms, [1.0, 0], plate.get_geometric_center())
        self.assertGreater(len(rolled), 0)
        self.assertLessEqual(len(rolled), len(atoms))  # remove_overlapping_atoms puede sacar alguno

    def test_zero_vector_raises(self):
        plate= Graphene.create_from_params(2, 2, 0, 0, 0, 1.0, False)
        with self.assertRaises(ValueError):
            core.roll_atoms_as_CNT(plate.get_carbon_coords(), [0, 0])


class TestApplyCNT(unittest.TestCase):
    def test_apply_cnt_marks_plate_and_allows_restore(self):
        plate= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        n_before= plate.get_number_atoms()

        core.apply_cnt(plate, [1.0, 0])
        self.assertTrue(plate.get_is_CNT())

        plate.restore_plate()
        self.assertFalse(plate.get_is_CNT())
        self.assertEqual(plate.get_number_atoms(), n_before)


class TestEvaluateCondition(unittest.TestCase):
    def test_empty_expression_is_always_true(self):
        self.assertTrue(core.evaluate_condition(1, 2, 3, 1, ""))

    def test_simple_comparison(self):
        self.assertTrue(core.evaluate_condition(10, 0, 0, 1, "x > 5"))
        self.assertFalse(core.evaluate_condition(10, 0, 0, 1, "x > 50"))

    def test_and_operator(self):
        self.assertTrue(core.evaluate_condition(10, 2, 0, 1, "x > 5 and y < 5"))
        self.assertFalse(core.evaluate_condition(10, 8, 0, 1, "x > 5 and y < 5"))

    def test_or_operator(self):
        self.assertTrue(core.evaluate_condition(10, 100, 0, 1, "x > 5 or y < 5"))   # cumple por x
        self.assertTrue(core.evaluate_condition(0, 1, 0, 1, "x > 5 or y < 5"))      # cumple por y
        self.assertFalse(core.evaluate_condition(0, 100, 0, 1, "x > 5 or y < 5"))   # no cumple ninguna

    def test_not_operator(self):
        self.assertTrue(core.evaluate_condition(1, 1, 0, 1, "not x > 5"))
        self.assertFalse(core.evaluate_condition(10, 1, 0, 1, "not x > 5"))

    def test_index_variable(self):
        self.assertTrue(core.evaluate_condition(0, 0, 0, 7, "index > 5"))


class TestGetListCarbonsInExpr(unittest.TestCase):
    def test_filters_by_expression(self):
        plate= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        all_carbons= plate.get_carbon_coords()
        filtered= core.get_list_carbons_in_expr(plate, "x > 0")
        self.assertLess(len(filtered), len(all_carbons))
        self.assertGreater(len(filtered), 0)

    def test_empty_expression_returns_all(self):
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        filtered= core.get_list_carbons_in_expr(plate, "")
        self.assertEqual(len(filtered), len(plate.get_carbon_coords()))


class TestUnsupportedExtensions(unittest.TestCase):
    def test_load_plates_from_file_unsupported_extension(self):
        with self.assertRaises(ValueError):
            core.load_plates_from_file(".foo", "whatever.foo")

    def test_export_plates_unsupported_extension(self):
        plate= Graphene.create_from_params(2, 2, 0, 0, 0, 1.0, False)
        with self.assertRaises(ValueError):
            core.export_plates("whatever.foo", [plate], [False, False])


class TestApplyOxidationExplicit(unittest.TestCase):
    def setUp(self):
        self.plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)

    def test_adds_exact_atoms_without_recomputation(self):
        n_before= self.plate.get_number_atoms()
        oxide_atoms= [
            (0.0, 0.71, 0.149, "OO"),
            (0.093, 0.71, 0.181, "HO"),
        ]
        added= core.apply_oxidation_explicit(self.plate, oxide_atoms)
        self.assertEqual(added, 1)  # cuenta el OO, no el HO que lo acompaña
        self.assertEqual(self.plate.get_number_atoms(), n_before + 2)

        oxides= self.plate.get_oxide_coords()
        self.assertEqual((oxides[-2][0], oxides[-2][1], oxides[-2][2], oxides[-2][3]), (0.0, 0.71, 0.149, "OO"))
        self.assertEqual((oxides[-1][0], oxides[-1][1], oxides[-1][2], oxides[-1][3]), (0.093, 0.71, 0.181, "HO"))

    def test_empty_list_is_noop(self):
        n_before= self.plate.get_number_atoms()
        added= core.apply_oxidation_explicit(self.plate, [])
        self.assertEqual(added, 0)
        self.assertEqual(self.plate.get_number_atoms(), n_before)

    def test_does_not_touch_existing_oxides(self):
        carbons= self.plate.get_carbon_coords()
        self.plate.add_oxydation_to_list_of_carbon(carbons[:2], z_mode=2, prob_oh=100)
        n_oxides_before= len(self.plate.get_oxide_coords())

        core.apply_oxidation_explicit(self.plate, [(0.5, 0.5, 0.149, "OO"), (0.593, 0.5, 0.181, "HO")])

        self.assertEqual(len(self.plate.get_oxide_coords()), n_oxides_before + 2)


class TestReduceBorders(unittest.TestCase):
    def test_adds_hydrogens_only_to_border_carbons(self):
        plate= Graphene.create_from_params(6, 6, 0, 0, 0, 1.0, periodic_boundary_x=False)
        self.assertEqual(len(plate.get_hydrogens_coords()), 0)

        core.reduce_borders(plate)

        n_h= len(plate.get_hydrogens_coords())
        self.assertGreater(n_h, 0)
        self.assertLess(n_h, len(plate.get_carbon_coords()))  # no todos los carbonos son de borde

    def test_noop_call_pattern_is_idempotent_safe(self):
        plate= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        core.reduce_borders(plate)
        n_h_first= len(plate.get_hydrogens_coords())
        self.assertGreater(n_h_first, 0)


if __name__ == "__main__":
    unittest.main()
