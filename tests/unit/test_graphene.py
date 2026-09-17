import unittest
from graphenegui.logic.graphene import Graphene


class TestReduceBordersPeriodicity(unittest.TestCase):

    def test_no_periodicity_adds_h_on_all_sides(self):
        plate= Graphene.create_from_params(6, 6, 0, 0, 0, 1.0, False, False)
        plate.reduce_borders()
        self.assertGreater(len(plate.get_hydrogens_coords()), 0)

    def test_periodic_x_adds_fewer_h_than_flat(self):
        plate_flat= Graphene.create_from_params(6, 6, 0, 0, 0, 1.0, False, False)
        plate_flat.reduce_borders()
        n_flat= len(plate_flat.get_hydrogens_coords())

        plate_px= Graphene.create_from_params(6, 6, 0, 0, 0, 1.0, True, False)
        plate_px.reduce_borders()
        n_px= len(plate_px.get_hydrogens_coords())

        self.assertGreater(n_px, 0)       # sigue habiendo borde real en Y
        self.assertLess(n_px, n_flat)     # pero menos que si X también fuera borde

    def test_periodic_both_axes_adds_no_h(self):
        plate= Graphene.create_from_params(6, 6, 0, 0, 0, 1.0, True, True)
        plate.reduce_borders()
        self.assertEqual(len(plate.get_hydrogens_coords()), 0)

    def test_periodicity_flags_stored_on_instance(self):
        plate= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, True, False)
        self.assertTrue(plate.periodic_boundary_x)
        self.assertFalse(plate.periodic_boundary_y)

    def test_default_is_non_periodic(self):
        plate= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)  # sin pasar periodic_y
        self.assertFalse(plate.periodic_boundary_x)
        self.assertFalse(plate.periodic_boundary_y)


class TestGrapheneCreation(unittest.TestCase):
    def test_atom_count_non_periodic(self):
        n_x, n_y, factor= 3, 2, 1.0
        plate= Graphene.create_from_params(n_x, n_y, 0, 0, 0, factor, periodic_boundary_x=False)
        atoms_per_row= (2 * n_x + 1) * 2
        self.assertEqual(plate.get_number_atoms(), n_y * atoms_per_row)
        self.assertEqual(len(plate.get_oxide_coords()), 0)

    def test_atom_count_periodic_x(self):
        n_x, n_y, factor= 3, 2, 1.0
        plate= Graphene.create_from_params(n_x, n_y, 0, 0, 0, factor, periodic_boundary_x=True)
        atoms_per_row= 4 * n_x
        self.assertEqual(plate.get_number_atoms(), n_y * atoms_per_row)


class TestGrapheneDuplicate(unittest.TestCase):
    def setUp(self):
        self.plate= Graphene.create_from_params(2, 2, 0, 0, 0, 1.0, False)

    def test_duplicate_shifts_coordinates(self):
        translation= [1.0, 2.0, 3.0]
        dup= self.plate.duplicate(translation)
        self.assertEqual(dup.get_number_atoms(), self.plate.get_number_atoms())
        for orig, moved in zip(self.plate.get_carbon_coords(), dup.get_carbon_coords()):
            self.assertAlmostEqual(moved[0] - orig[0], translation[0], places=6)
            self.assertAlmostEqual(moved[1] - orig[1], translation[1], places=6)
            self.assertAlmostEqual(moved[2] - orig[2], translation[2], places=6)

    def test_duplicate_propagates_periodicity_flags(self):
        periodic_plate= Graphene.create_from_params(2, 2, 0, 0, 0, 1.0, True, True)
        dup= periodic_plate.duplicate([0, 0, 0.34])
        self.assertTrue(dup.periodic_boundary_x)
        self.assertTrue(dup.periodic_boundary_y)


class TestOxidation(unittest.TestCase):
    def test_full_oh_oxidation_is_deterministic(self):
        plate= Graphene.create_from_params(3, 3, 0, 0, 0, 1.0, False)
        carbons= plate.get_carbon_coords()
        count= plate.add_oxydation_to_list_of_carbon(list(carbons), z_mode=2, prob_oh=100)
        self.assertEqual(count, len(carbons))
        self.assertEqual(plate.get_oxide_count(), len(carbons))       # cuenta solo los OO
        self.assertEqual(len(plate.get_oxide_coords()), 2 * len(carbons))  # OO + HO por cada uno


class TestRecheckOxIndexes(unittest.TestCase):
    def test_pairs_each_oo_with_an_ho(self):
        plate= Graphene.create_from_params(2, 2, 0, 0, 0, 1.0, False)
        plate.oxide_coords= [
            [0.0, 0.0, 0.15, "OO", -1, False, "OO"],
            [0.2, 0.0, 0.15, "OO", -1, False, "OO"],
        ]
        plate.recheck_ox_indexes()

        types= [ox[3] for ox in plate.get_oxide_coords()]
        self.assertEqual(types, ["OO", "HO", "OO", "HO"])


class TestGetNearestCarbonsToOxideAfterCNT(unittest.TestCase):

    def test_every_oo_and_oe_still_finds_a_carbon_after_cnt(self):
        from graphenegui.logic import core

        plate= Graphene.create_from_params(6, 6, 0, 0, 0, 1.0, False)
        carbons= plate.get_carbon_coords()
        plate.add_oxydation_to_list_of_carbon(carbons[:10], z_mode=2, prob_oh=66)

        core.apply_cnt(plate, [1.5, 0])

        oo_oe= [ox for ox in plate.get_oxide_coords() if ox[3] in ("OO", "OE")]
        self.assertGreater(len(oo_oe), 0)  # que el test realmente ejercite algo
        for ox in oo_oe:
            near= plate.get_nearest_carbons_to_oxide(ox)
            self.assertGreater(len(near), 0, f"sin carbono encontrado para {ox[3]} en {ox[:3]}")

    def test_does_not_match_a_wrong_neighbor_carbon(self):
        plate= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        carbon= plate.get_carbon_coords()[10]
        plate.add_oxydation_to_list_of_carbon([carbon], z_mode=0, prob_oh=100)  # fuerza OO
        oo= next(ox for ox in plate.get_oxide_coords() if ox[3] == "OO")

        near= plate.get_nearest_carbons_to_oxide(oo)
        self.assertEqual(len(near), 1)
        self.assertEqual(near[0][4], carbon[4])  # es el carbono correcto, no un vecino


if __name__ == "__main__":
    unittest.main()
