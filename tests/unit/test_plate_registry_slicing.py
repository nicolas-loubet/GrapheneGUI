"""
Bug encontrado en vivo durante la Etapa 19 (validación end-to-end), no
achacable a ninguna etapa anterior: PlateRegistry.__getitem__ nunca soportó
slices (solo índices enteros). writeMOL2 (export_formats.py) calcula el
offset de bonds entre placas con `plates[:i_plate]` -- con una lista plana
(el camino headless/CLI, que es todo lo que se pudo probar en el sandbox
hasta ahora) esto funciona nativo de Python. Con PlateRegistry (el camino
real de la GUI) explotaba: self._order[slice] devuelve una LISTA de ids, y
usar esa lista como clave de self._entries (un dict) tira
"TypeError: unhashable type: 'list'". Nunca se había disparado porque los
129 tests existentes prueban todos el camino headless (listas planas).
"""
import unittest
from graphenegui.logic.plate_registry import PlateRegistry
from graphenegui.logic.graphene import Graphene


class TestPlateRegistrySlicing(unittest.TestCase):
    def setUp(self):
        self.registry= PlateRegistry()
        self.p1= Graphene.create_from_params(4, 3, 0, 0, 0, 1.0, False, False)
        self.p2= Graphene.create_from_params(3, 2, 0, 0, 40, 1.0, False, False)
        self.p3= Graphene.create_from_params(2, 2, 0, 0, 80, 1.0, False, False)
        self.registry.add(self.p1)
        self.registry.add(self.p2)
        self.registry.add(self.p3)

    def test_empty_slice_from_start(self):
        self.assertEqual(self.registry[:0], [])

    def test_slice_returns_plain_list_of_plates_in_order(self):
        self.assertEqual(self.registry[:1], [self.p1])
        self.assertEqual(self.registry[:2], [self.p1, self.p2])
        self.assertEqual(self.registry[:3], [self.p1, self.p2, self.p3])

    def test_full_slice(self):
        self.assertEqual(self.registry[:], [self.p1, self.p2, self.p3])

    def test_integer_indexing_still_works(self):
        """El fix no debería romper el acceso normal por índice entero."""
        self.assertIs(self.registry[0], self.p1)
        self.assertIs(self.registry[1], self.p2)
        self.assertIs(self.registry[2], self.p3)

    def test_writemol2_offset_pattern_does_not_crash(self):
        """Reproduce el patrón exacto que crasheaba: sum(...) sobre
        registry[:i_plate] para cada i_plate en un enumerate."""
        for i_plate, plate in enumerate(self.registry):
            offset= sum(p.get_number_atoms() for p in self.registry[:i_plate])
            expected= sum(p.get_number_atoms() for p in [self.p1, self.p2, self.p3][:i_plate])
            self.assertEqual(offset, expected)


if __name__ == "__main__":
    unittest.main()
