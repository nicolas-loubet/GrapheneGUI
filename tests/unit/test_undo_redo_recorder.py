import unittest

from graphenegui.logic.recorder import SessionRecorder


class TestUndoRedoBasics(unittest.TestCase):
    def test_undo_with_empty_stack_is_noop(self):
        rec= SessionRecorder()
        self.assertFalse(rec.can_undo())
        self.assertFalse(rec.undo())

    def test_redo_with_empty_stack_is_noop(self):
        rec= SessionRecorder()
        self.assertFalse(rec.can_redo())
        self.assertFalse(rec.redo())

    def test_undo_plate_creation_empties_session(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 10, "height": 10}, name="p1")
        self.assertFalse(rec.is_empty())

        self.assertTrue(rec.can_undo())
        self.assertTrue(rec.undo())
        self.assertTrue(rec.is_empty())
        self.assertEqual(rec.known_plates(), [])

    def test_redo_restores_undone_plate_creation(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 10, "height": 10}, name="p1")
        rec.undo()
        self.assertTrue(rec.can_redo())
        self.assertTrue(rec.redo())
        self.assertFalse(rec.is_empty())
        self.assertEqual(rec.known_plates(), ["p1"])

    def test_new_action_after_undo_clears_redo_stack(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 10}, name="p1")
        rec.undo()
        self.assertTrue(rec.can_redo())

        rec.record_plate_created({"width": 10}, name="p2")
        self.assertFalse(rec.can_redo(), "una accion nueva invalida cualquier redo pendiente")


class TestUndoRedoMultiStep(unittest.TestCase):
    def setUp(self):
        self.rec= SessionRecorder()
        self.rec.record_plate_created({"width": 10}, name="p1")
        self.rec.record_oxidation_hard("p1", [(0.0, 0.0, 0.1, "OO")])
        self.rec.record_reduce_borders("p1")

    def test_sequential_undo_reverses_steps_in_order(self):
        d= self.rec.to_dict()
        self.assertEqual([s["type"] for s in d["plates"][0]["steps"]], ["oxidation", "reduce_borders"])

        self.rec.undo()
        d= self.rec.to_dict()
        self.assertEqual([s["type"] for s in d["plates"][0]["steps"]], ["oxidation"])

        self.rec.undo()
        d= self.rec.to_dict()
        self.assertEqual(d["plates"][0]["steps"], [])

        self.rec.undo()
        self.assertTrue(self.rec.is_empty())

        self.assertFalse(self.rec.can_undo())

    def test_full_undo_then_full_redo_reaches_identical_state(self):
        original= self.rec.to_dict()
        for _ in range(3):
            self.rec.undo()
        for _ in range(3):
            self.rec.redo()
        self.assertEqual(self.rec.to_dict(), original)
        self.assertFalse(self.rec.can_redo())

    def test_step_list_still_usable_after_undo_redo_roundtrip(self):
        """Etapa 27: _step_lists se reconstruye con _index_step_lists()
        después de restaurar -- si quedara apuntando a una lista vieja
        (huérfana, no la que cuelga de self._roots), agregar un step nuevo
        después de un undo/redo no aparecería en to_dict()."""
        self.rec.undo()
        self.rec.redo()
        self.rec.record_reduce_borders("p1")  # ya estaba, pero no importa: solo valida que se registre
        d= self.rec.to_dict()
        self.assertEqual(len(d["plates"][0]["steps"]), 3)


class TestUndoRedoDuplicates(unittest.TestCase):
    def test_undo_duplicate_removes_nested_step_from_source(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 10}, name="p1")
        rec.record_duplicate("p1", [1, 0, 0], name="p1_dup")
        self.assertIn("p1_dup", rec.known_plates())
        self.assertTrue(rec.has_plate("p1_dup"))

        rec.undo()
        self.assertNotIn("p1_dup", rec.known_plates())
        self.assertFalse(rec.has_plate("p1_dup"))
        d= rec.to_dict()
        self.assertEqual(d["plates"][0]["steps"], [])

    def test_redo_duplicate_restores_it_fully_usable(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 10}, name="p1")
        rec.record_duplicate("p1", [1, 0, 0], name="p1_dup")
        rec.undo()
        rec.redo()

        self.assertTrue(rec.has_plate("p1_dup"))
        rec.record_oxidation_hard("p1_dup", [(0.0, 0.0, 0.1, "OO")])  # debe poder seguir usándose
        d= rec.to_dict()
        dup_step= d["plates"][0]["steps"][0]
        self.assertEqual(dup_step["type"], "duplicate")
        self.assertEqual(len(dup_step["steps"]), 1)


class TestUndoRedoRemovePlate(unittest.TestCase):
    def test_undo_remove_plate_restores_it(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 10}, name="p1")
        rec.record_plate_created({"width": 20}, name="p2")
        rec.remove_plate("p1")
        self.assertEqual(rec.known_plates(), ["p2"])

        rec.undo()
        self.assertIn("p1", rec.known_plates())
        self.assertIn("p2", rec.known_plates())

    def test_remove_unknown_plate_is_noop_and_not_checkpointed(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 10}, name="p1")
        rec.remove_plate("does_not_exist")  # no debería empujar nada al undo stack
        self.assertTrue(rec.can_undo())

        rec.undo()  # deshace record_plate_created, no un remove_plate fantasma
        self.assertTrue(rec.is_empty())
        self.assertFalse(rec.can_undo())


class TestUndoRedoAtomTypes(unittest.TestCase):
    def test_undo_atom_type_registration(self):
        rec= SessionRecorder()
        rec.record_atom_type("custom1", 0.1, 3.0)
        self.assertEqual(rec.to_dict()["atom_types"], [{"name": "custom1", "epsilon": 0.1, "sigma": 3.0}])

        rec.undo()
        self.assertEqual(rec.to_dict()["atom_types"], [])


if __name__ == "__main__":
    unittest.main()
