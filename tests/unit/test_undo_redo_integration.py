import unittest

from graphenegui.logic import functionalities as F
from graphenegui.logic.recorder import SessionRecorder
from graphenegui.logic.plate_registry import PlateRegistry
from graphenegui.logic import core


class FakeCombo:
    def __init__(self):
        self.items= []
    def clear(self):
        self.items= []
    def addItem(self, text):
        self.items.append(text)
    def setCurrentIndex(self, i):
        self.current= i


class FakeUI:
    def __init__(self):
        self.comboDrawings= FakeCombo()
        self.comboCType= FakeCombo()


class FakeRenderer:
    def __init__(self):
        self.highlighted_atoms= []


class FakeMainWindow:
    def __init__(self):
        self.session_recorder= SessionRecorder()
        self.plates= PlateRegistry()
        self.ui= FakeUI()
        self.renderer= FakeRenderer()
        self.information_selected_atoms= []
        self.first_carbon= None
        self.atom_types= {}
        self.update_calls= 0
        self.buttons_enabled_calls= []

    def update_drawing_area(self):
        self.update_calls+= 1

    def buttons_that_depend_of_having_a_plate(self, enabled):
        self.buttons_enabled_calls.append(enabled)

    def update_ctype_controls_enabled(self):
        pass

    def set_oxide_mode(self, mode):
        pass

    def set_ctype_mode(self, mode):
        pass


class TestUndoRedoEndToEnd(unittest.TestCase):
    def _create_and_register_plate(self, mw, width=4, height=4):
        """Simula lo que hace un handler real de la GUI (create_plate en
        functionalities.py): construye el Graphene y lo registra en plates +
        recorder, siempre con el MISMO id como nombre en los dos lados."""
        create_params= {"width": width, "height": height, "factor": 1.0,
                         "center": [0, 0, 0], "periodic_boundary_x": False,
                         "periodic_boundary_y": False}
        plate= core.build_plate_from_create(create_params)
        plate_id= mw.plates.add(plate)
        mw.session_recorder.record_plate_created(create_params, name=plate_id)
        return plate_id

    def test_undo_plate_creation_removes_it_from_plates_registry(self):
        mw= FakeMainWindow()
        self._create_and_register_plate(mw)
        self.assertEqual(len(mw.plates), 1)

        F.handle_undo(mw)
        self.assertEqual(len(mw.plates), 0)
        self.assertEqual(mw.ui.comboDrawings.items, [])
        self.assertFalse(mw.session_recorder.can_undo())

    def test_redo_recreates_the_plate(self):
        mw= FakeMainWindow()
        self._create_and_register_plate(mw)
        F.handle_undo(mw)
        F.handle_redo(mw)

        self.assertEqual(len(mw.plates), 1)
        self.assertEqual(mw.ui.comboDrawings.items, ["Plate 1"])

    def test_undo_after_oxidation_reverts_oxide_atoms(self):
        mw= FakeMainWindow()
        plate_id= self._create_and_register_plate(mw, width=6, height=4)
        plate= mw.plates[0]
        carbons= plate.get_carbon_coords()
        core.apply_oxidation(plate, carbons, z_mode=2, prob_oh=100)
        oxide_atoms= [[x, y, z, t] for x, y, z, t, *_ in plate.get_oxide_coords()]
        mw.session_recorder.record_oxidation_hard(plate_id, oxide_atoms)
        self.assertGreater(len(mw.plates[0].get_oxide_coords()), 0)

        F.handle_undo(mw)
        self.assertEqual(len(mw.plates), 1, "la placa sigue existiendo, solo se deshizo la oxidación")
        self.assertEqual(len(mw.plates[0].get_oxide_coords()), 0)

        F.handle_redo(mw)
        self.assertEqual(len(mw.plates[0].get_oxide_coords()), len(oxide_atoms))

    def test_handle_undo_with_nothing_to_undo_is_noop(self):
        mw= FakeMainWindow()
        F.handle_undo(mw)  # no debería explotar
        self.assertEqual(mw.update_calls, 0)

    def test_multiple_plates_undo_redo_roundtrip(self):
        mw= FakeMainWindow()
        self._create_and_register_plate(mw)
        self._create_and_register_plate(mw)
        self.assertEqual(len(mw.plates), 2)

        F.handle_undo(mw)  # saca p2
        self.assertEqual(len(mw.plates), 1)

        F.handle_undo(mw)  # saca p1
        self.assertEqual(len(mw.plates), 0)

        F.handle_redo(mw)
        F.handle_redo(mw)
        self.assertEqual(len(mw.plates), 2)
        self.assertEqual(mw.ui.comboDrawings.items, ["Plate 1", "Plate 2"])


if __name__ == "__main__":
    unittest.main()
