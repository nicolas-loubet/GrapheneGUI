"""
Etapa 14: tests de validate_steps + apply_step para el step 'cnt_restored'
(deshacer un CNT, plate.restore_plate()).

Corridos de verdad contra el paquete completo (core.py + graphene.py +
export_formats.py + import_formats.py + plate_registry.py).
"""
import unittest
from graphenegui.logic import core
from graphenegui.logic.graphene import Graphene


class TestValidateStepsWithCntRestored(unittest.TestCase):
    def test_cnt_alone_at_the_end_still_valid(self):
        """Caso viejo (antes de la Etapa 14): cnt sin restaurar, al final."""
        core.validate_steps("p", [{"type": "cnt", "vector": [1, 0]}])
        core.validate_steps("p", [{"type": "oxidation"}, {"type": "cnt", "vector": [1, 0]}])

    def test_editing_after_unrestored_cnt_still_rejected(self):
        with self.assertRaises(ValueError):
            core.validate_steps("p", [{"type": "cnt", "vector": [1, 0]}, {"type": "oxidation"}])

    def test_reduce_borders_before_cnt_still_rejected(self):
        with self.assertRaises(ValueError):
            core.validate_steps("p", [{"type": "reduce_borders"}, {"type": "cnt", "vector": [1, 0]}])

    def test_cnt_restored_without_active_cnt_rejected(self):
        with self.assertRaises(ValueError):
            core.validate_steps("p", [{"type": "cnt_restored"}])

    def test_cnt_then_restored_is_valid(self):
        core.validate_steps("p", [{"type": "cnt", "vector": [1, 0]}, {"type": "cnt_restored"}])

    def test_can_keep_editing_after_restore(self):
        core.validate_steps("p", [
            {"type": "cnt", "vector": [1, 0]}, {"type": "cnt_restored"}, {"type": "oxidation"},
        ])

    def test_can_roll_again_after_restore(self):
        core.validate_steps("p", [
            {"type": "cnt", "vector": [1, 0]}, {"type": "cnt_restored"}, {"type": "cnt", "vector": [2, 0]},
        ])

    def test_restored_cnt_before_reduce_borders_is_valid(self):
        """Nuevo permitido en la Etapa 14: la placa volvió a estar plana antes
        de reducir bordes, no hay conflicto real (a diferencia de reduce_borders
        antes de un cnt, que sigue prohibido más abajo)."""
        core.validate_steps("p", [
            {"type": "cnt", "vector": [1, 0]}, {"type": "cnt_restored"}, {"type": "reduce_borders"},
        ])

    def test_reduce_borders_after_restored_cnt_but_cnt_came_first_still_rejected(self):
        """reduce_borders bloquea cnt para siempre de ahí en más, incluso si
        ese cnt después se restaura -- el orden real importa."""
        with self.assertRaises(ValueError):
            core.validate_steps("p", [
                {"type": "reduce_borders"}, {"type": "cnt", "vector": [1, 0]}, {"type": "cnt_restored"},
            ])


class TestApplyStepCntRestored(unittest.TestCase):
    def setUp(self):
        self.plate= Graphene.create_from_params(12, 8, 0, 0, 0, 1.0, False, False)

    def test_restores_exact_previous_state(self):
        carbons_before= [list(c) for c in self.plate.get_carbon_coords()]
        core.apply_step(self.plate, {"type": "cnt", "vector": [2, 0]})
        self.assertTrue(self.plate.get_is_CNT())
        core.apply_step(self.plate, {"type": "cnt_restored"})
        self.assertFalse(self.plate.get_is_CNT())
        carbons_after= [list(c) for c in self.plate.get_carbon_coords()]
        self.assertEqual(carbons_after, carbons_before)

    def test_raises_clear_error_without_active_cnt(self):
        with self.assertRaises(ValueError):
            core.apply_step(self.plate, {"type": "cnt_restored"})

    def test_supports_roll_restore_roll_again(self):
        """El ciclo completo que la GUI permite: enrollar, deshacer, enrollar
        con OTRO vector."""
        core.apply_step(self.plate, {"type": "cnt", "vector": [2, 0]})
        core.apply_step(self.plate, {"type": "cnt_restored"})
        core.apply_step(self.plate, {"type": "cnt", "vector": [3, 0]})
        self.assertTrue(self.plate.get_is_CNT())


if __name__ == "__main__":
    unittest.main()
