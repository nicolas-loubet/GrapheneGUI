"""
Etapa 12: tests de la sección "Tipo de carbono" de core.py --
find_carbon_at / apply_carbon_type_explicit / apply_carbon_type_step, y su
enganche en el dispatcher genérico apply_step.

NO pude correrlos acá (sandbox sin PySide6 y sin plate_registry.py/
import_formats.py/export_formats.py, que core.py necesita para importarse
como paquete) -- la lógica de estas 3 funciones sí se probó aislada durante
el desarrollo (extraídas del archivo y ejecutadas contra un Graphene real).
Van en tests/unit/, van a correr con el resto vía run_tests.py.
"""
import unittest
from graphenegui.logic import core
from graphenegui.logic.graphene import Graphene, DEFAULT_CARBON_TYPE


class TestFindCarbonAt(unittest.TestCase):
    def setUp(self):
        self.plate= Graphene.create_from_params(4, 3, 0, 0, 0, 1.0, False, False)

    def test_finds_existing_carbon(self):
        c0= self.plate.get_carbon_coords()[0]
        found= core.find_carbon_at(self.plate, c0[0], c0[1], c0[2])
        self.assertIs(found, c0)

    def test_returns_none_when_not_found(self):
        self.assertIsNone(core.find_carbon_at(self.plate, 999, 999, 999))


class TestApplyCarbonTypeExplicit(unittest.TestCase):
    def setUp(self):
        self.plate= Graphene.create_from_params(4, 3, 0, 0, 0, 1.0, False, False)

    def test_applies_and_counts(self):
        c0, c1= self.plate.get_carbon_coords()[:2]
        changed= core.apply_carbon_type_explicit(self.plate, [tuple(c0[:3]), tuple(c1[:3])], "ce")
        self.assertEqual(changed, 2)
        self.assertEqual(self.plate.get_carbon_coords()[0][6], "ce")
        self.assertEqual(self.plate.get_carbon_coords()[1][6], "ce")

    def test_raises_clear_error_when_position_not_found(self):
        with self.assertRaises(ValueError):
            core.apply_carbon_type_explicit(self.plate, [(123, 456, 789)], "ce")

    def test_reset_uses_same_mechanism_as_paint(self):
        """No hay un 'modo reset' aparte a nivel dato -- es el mismo
        apply_carbon_type_explicit con new_type=DEFAULT_CARBON_TYPE."""
        c0= self.plate.get_carbon_coords()[0]
        core.apply_carbon_type_explicit(self.plate, [tuple(c0[:3])], "ce")
        core.apply_carbon_type_explicit(self.plate, [tuple(c0[:3])], DEFAULT_CARBON_TYPE)
        self.assertEqual(self.plate.get_carbon_coords()[0][6], DEFAULT_CARBON_TYPE)


class TestApplyCarbonTypeStep(unittest.TestCase):
    def setUp(self):
        self.plate= Graphene.create_from_params(4, 3, 0, 0, 0, 1.0, False, False)

    def test_converts_angstrom_to_nm_and_applies(self):
        c2= self.plate.get_carbon_coords()[2]
        x_ang, y_ang, z_ang= [v * 10 for v in c2[:3]]
        step= {"type": "set_carbon_type", "carbon_type": "co", "carbons": [[x_ang, y_ang, z_ang]]}
        core.apply_carbon_type_step(self.plate, step)
        self.assertEqual(self.plate.get_carbon_coords()[2][6], "co")

    def test_missing_carbon_type_raises(self):
        with self.assertRaises(ValueError):
            core.apply_carbon_type_step(self.plate, {"type": "set_carbon_type", "carbons": [[0, 0, 0]]})

    def test_missing_carbons_raises(self):
        with self.assertRaises(ValueError):
            core.apply_carbon_type_step(self.plate, {"type": "set_carbon_type", "carbon_type": "ce", "carbons": []})

    def test_position_not_found_raises(self):
        with self.assertRaises(ValueError):
            step= {"type": "set_carbon_type", "carbon_type": "ce", "carbons": [[9999, 9999, 9999]]}
            core.apply_carbon_type_step(self.plate, step)

    def test_wired_into_generic_apply_step_dispatch(self):
        """Regresión: confirma que apply_step (el dispatcher genérico que usa
        build_session_from_config/cli.py para leer 'steps') reconoce
        'set_carbon_type' -- no alcanza con que la función aislada funcione."""
        c0= self.plate.get_carbon_coords()[0]
        step= {"type": "set_carbon_type", "carbon_type": "ce",
               "carbons": [[c0[0] * 10, c0[1] * 10, c0[2] * 10]]}
        core.apply_step(self.plate, step)
        self.assertEqual(self.plate.get_carbon_coords()[0][6], "ce")


if __name__ == "__main__":
    unittest.main()
