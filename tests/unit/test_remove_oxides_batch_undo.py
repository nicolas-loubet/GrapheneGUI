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
    def currentIndex(self):
        return len(self.items) - 1
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
        self.z_mode= 2
        self.last_prob_oh= 100

    def update_drawing_area(self):
        pass

    def buttons_that_depend_of_having_a_plate(self, enabled):
        pass

    def update_ctype_controls_enabled(self):
        pass

    def set_oxide_mode(self, mode):
        pass

    def set_ctype_mode(self, mode):
        pass


class TestRemoveOxidesIsOneUndoableAction(unittest.TestCase):
    """Bug real: un OH comparte carbono entre OO y HO. remove_oxides_from_
    selection los remueve en un for por átomo, y cada uno llamaba a
    record_oxidation_removed por separado -- 2 checkpoints para un solo
    click de "remove", así que un Ctrl-Z devolvía nada más que el H (el
    último de los dos remueves), dejando el O afuera. batch_action()
    agrupa toda la llamada en un solo checkpoint."""

    def setUp(self):
        self.mw= FakeMainWindow()
        create_params= {"width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
                         "periodic_boundary_x": False, "periodic_boundary_y": False}
        plate= core.build_plate_from_create(create_params)
        plate_id= self.mw.plates.add(plate)
        self.mw.session_recorder.record_plate_created(create_params, name=plate_id)
        self.mw.ui.comboDrawings.addItem("Plate 1")

    def _oxidize_one_carbon_with_OH(self):
        plate= self.mw.plates[0]
        carbons= plate.get_carbon_coords()
        target= [carbons[len(carbons) // 2]]
        oxide_count_before= len(plate.get_oxide_coords())
        core.apply_oxidation(plate, target, self.mw.z_mode, prob_oh=100)
        F.record_new_oxides(self.mw, 0, oxide_count_before)
        return target

    def test_removing_a_single_OH_pushes_exactly_one_checkpoint(self):
        target= self._oxidize_one_carbon_with_OH()
        self.assertEqual(len(self.mw.plates[0].get_oxide_coords()), 2)  # OO + HO

        undo_depth_before= len(self.mw.session_recorder._undo_stack)
        F.remove_oxides_from_selection(self.mw, target)
        self.assertEqual(len(self.mw.plates[0].get_oxide_coords()), 0)

        pushed= len(self.mw.session_recorder._undo_stack) - undo_depth_before
        self.assertEqual(pushed, 1, "un solo click de remove tiene que ser un solo checkpoint")

    def test_single_undo_restores_both_oxygen_and_hydrogen(self):
        target= self._oxidize_one_carbon_with_OH()
        F.remove_oxides_from_selection(self.mw, target)
        self.assertEqual(len(self.mw.plates[0].get_oxide_coords()), 0)

        F.handle_undo(self.mw)  # UN solo Ctrl-Z

        oxides= self.mw.plates[0].get_oxide_coords()
        self.assertEqual(len(oxides), 2, "un solo Ctrl-Z tiene que devolver el OH completo")
        self.assertEqual({o[3] for o in oxides}, {"OO", "HO"})

    def test_removing_a_larger_selection_is_still_one_checkpoint(self):
        """No es solo el caso de un OH suelto -- CUALQUIER remove de una
        selección con varios óxidos tiene que ser un solo undo, sea 1 o 50
        átomos removidos."""
        plate= self.mw.plates[0]
        carbons= plate.get_carbon_coords()
        many= carbons[:10]
        oxide_count_before= len(plate.get_oxide_coords())
        core.apply_oxidation(plate, many, self.mw.z_mode, prob_oh=100)
        F.record_new_oxides(self.mw, 0, oxide_count_before)
        oxide_total_before_remove= len(plate.get_oxide_coords())
        self.assertGreater(oxide_total_before_remove, 2)

        undo_depth_before= len(self.mw.session_recorder._undo_stack)
        removed= F.remove_oxides_from_selection(self.mw, many)
        self.assertGreater(removed, 2)

        pushed= len(self.mw.session_recorder._undo_stack) - undo_depth_before
        self.assertEqual(pushed, 1)

        F.handle_undo(self.mw)
        self.assertEqual(len(self.mw.plates[0].get_oxide_coords()), oxide_total_before_remove)


if __name__ == "__main__":
    unittest.main()
