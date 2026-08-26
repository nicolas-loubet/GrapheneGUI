import unittest

from graphenegui.logic.graphene import Graphene
from graphenegui.logic.plate_registry import PlateRegistry


class TestBasicRegistration(unittest.TestCase):
    def test_add_returns_stable_ids(self):
        reg= PlateRegistry()
        plate= Graphene.create_from_params(2, 2, 0, 0, 0, 1.0, False)
        id1= reg.add(plate)
        id2= reg.add(plate)
        self.assertEqual([id1, id2], ["plate1", "plate2"])

    def test_list_like_access(self):
        reg= PlateRegistry()
        plate= Graphene.create_from_params(2, 2, 0, 0, 0, 1.0, False)
        reg.add(plate)
        self.assertEqual(len(reg), 1)
        self.assertIs(reg[0], plate)
        self.assertEqual(list(reg), [plate])

    def test_id_at_and_position_of_are_inverses(self):
        reg= PlateRegistry()
        plate= Graphene.create_from_params(2, 2, 0, 0, 0, 1.0, False)
        id= reg.add(plate)
        self.assertEqual(reg.id_at(0), id)
        self.assertEqual(reg.position_of(id), 0)


class TestRemoveAtNeedsNoIndexShifting(unittest.TestCase):
    def test_remove_middle_keeps_other_ids_valid(self):
        """El caso que rompía el bookkeeping viejo por posición: borrar una placa del
        medio no debe requerir tocar las referencias duplicate_of de las demás."""
        reg= PlateRegistry()
        base= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        base_id= reg.add(base)
        reg.add(Graphene.create_from_params(2, 2, 0, 0, 0, 1.0, False))  # placa sin relación
        dup= base.duplicate([0, 0, 0.34])
        dup_id= reg.add(dup, duplicate_of=base_id, translation=[0, 0, 0.34])

        reg.remove_at(1)  # borra la placa sin relación del medio

        self.assertEqual(len(reg), 2)
        self.assertEqual(reg.id_at(0), base_id)
        self.assertEqual(reg.id_at(1), dup_id)
        self.assertEqual(reg.entry_at(1).duplicate_of, base_id)  # sigue apuntando bien, sin tocar nada


class TestResolveDuplicateGroups(unittest.TestCase):
    def test_untouched_duplicate_is_detected(self):
        reg= PlateRegistry()
        base= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        base_id= reg.add(base)
        translation= [0.0, 0.0, 0.34]
        reg.add(base.duplicate(translation), duplicate_of=base_id, translation=translation)

        duplicates, roots= reg.resolve_duplicate_groups()
        self.assertEqual(duplicates, [2])
        self.assertEqual(roots, [1])

    def test_edited_duplicate_is_excluded(self):
        """El punto central del rediseño: si el duplicado se editó después (acá,
        oxidado), deja de coincidir con la fuente trasladada y sale del grupo SOLO,
        sin que nadie tenga que avisarle a esta función."""
        reg= PlateRegistry()
        base= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        base_id= reg.add(base)
        translation= [0.0, 0.0, 0.34]
        dup= base.duplicate(translation)
        reg.add(dup, duplicate_of=base_id, translation=translation)

        dup.add_oxydation_to_list_of_carbon(dup.get_carbon_coords()[:2], z_mode=2, prob_oh=100)

        duplicates, roots= reg.resolve_duplicate_groups()
        self.assertEqual(duplicates, [])
        self.assertEqual(roots, [])

    def test_edited_base_also_excludes_its_duplicate(self):
        """Si en cambio se edita la BASE después de duplicar, el duplicado (que
        quedó con la geometría vieja) tampoco debería seguir matcheando."""
        reg= PlateRegistry()
        base= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        base_id= reg.add(base)
        translation= [0.0, 0.0, 0.34]
        reg.add(base.duplicate(translation), duplicate_of=base_id, translation=translation)

        base.add_oxydation_to_list_of_carbon(base.get_carbon_coords()[:2], z_mode=2, prob_oh=100)

        duplicates, roots= reg.resolve_duplicate_groups()
        self.assertEqual(duplicates, [])
        self.assertEqual(roots, [])

    def test_chain_of_duplicates_resolves_to_ultimate_root(self):
        """C es duplicado de B, que es duplicado de A. Si ninguno se tocó, C debe
        resolver como duplicado de A (el root real), no de B."""
        reg= PlateRegistry()
        a= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        a_id= reg.add(a)
        t_ab= [0.0, 0.0, 0.34]
        b= a.duplicate(t_ab)
        b_id= reg.add(b, duplicate_of=a_id, translation=t_ab)
        t_bc= [0.0, 0.0, 0.34]
        c= b.duplicate(t_bc)
        reg.add(c, duplicate_of=b_id, translation=t_bc)

        duplicates, roots= reg.resolve_duplicate_groups()
        # posiciones 1-indexadas: a=1, b=2, c=3
        self.assertEqual(duplicates, [2, 3])
        self.assertEqual(roots, [1, 1])

    def test_middle_of_chain_edited_breaks_chain_but_not_unrelated_links(self):
        reg= PlateRegistry()
        a= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        a_id= reg.add(a)
        t_ab= [0.0, 0.0, 0.34]
        b= a.duplicate(t_ab)
        b_id= reg.add(b, duplicate_of=a_id, translation=t_ab)
        t_bc= [0.0, 0.0, 0.34]
        c= b.duplicate(t_bc)
        reg.add(c, duplicate_of=b_id, translation=t_bc)

        b.add_oxydation_to_list_of_carbon(b.get_carbon_coords()[:2], z_mode=2, prob_oh=100)  # se edita B

        duplicates, roots= reg.resolve_duplicate_groups()
        self.assertEqual(duplicates, [])  # ni B (editada) ni C (su fuente ya no matchea) quedan
        self.assertEqual(roots, [])

    def test_deleted_source_excludes_orphan_duplicate(self):
        reg= PlateRegistry()
        base= Graphene.create_from_params(4, 4, 0, 0, 0, 1.0, False)
        base_id= reg.add(base)
        translation= [0.0, 0.0, 0.34]
        reg.add(base.duplicate(translation), duplicate_of=base_id, translation=translation)

        reg.remove_at(0)  # se borra la fuente

        duplicates, roots= reg.resolve_duplicate_groups()
        self.assertEqual(duplicates, [])
        self.assertEqual(roots, [])


if __name__ == "__main__":
    unittest.main()
