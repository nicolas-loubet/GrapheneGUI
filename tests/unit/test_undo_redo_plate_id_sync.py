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


class TestRebuildKeepsRecorderNamesInSync(unittest.TestCase):

    def _create_plate(self, mw, width=6, height=4):
        create_params= {"width": width, "height": height, "factor": 1.0,
                         "center": [0, 0, 0], "periodic_boundary_x": False,
                         "periodic_boundary_y": False}
        plate= core.build_plate_from_create(create_params)
        plate_id= mw.plates.add(plate)
        mw.session_recorder.record_plate_created(create_params, name=plate_id)
        mw.ui.comboDrawings.addItem(f"Plate {len(mw.plates)}")
        return plate_id

    def _oxidize_current(self, mw, expr_filter, prob_oh):
        """Simula put_oxides + record_new_oxides tal como los llama la GUI real."""
        plate_index= mw.ui.comboDrawings.currentIndex()
        plate= mw.plates[plate_index]
        carbons= [c for c in plate.get_carbon_coords() if expr_filter(c)]
        oxide_count_before= len(plate.get_oxide_coords())
        mw.last_prob_oh= prob_oh
        core.apply_oxidation(plate, carbons, mw.z_mode, mw.last_prob_oh)
        F.record_new_oxides(mw, plate_index, oxide_count_before)

    def test_ids_stay_in_sync_after_rebuild(self):
        mw= FakeMainWindow()
        plate_id= self._create_plate(mw)
        self.assertEqual(mw.session_recorder.known_plates(), [plate_id])

        core.reduce_borders(mw.plates[0])
        mw.session_recorder.record_reduce_borders(plate_id)
        F.handle_undo(mw)  # deshace reduce_borders -> dispara el rebuild

        new_id= mw.plates.id_at(0)
        self.assertNotEqual(new_id, plate_id, "PlateRegistry no recicla ids -- esto tiene que cambiar")
        self.assertEqual(mw.session_recorder.known_plates(), [new_id],
                          "rename_plate tiene que mantener al recorder apuntando al id real")
        self.assertTrue(mw.session_recorder.has_plate(new_id))

    def test_oxidation_after_undo_is_actually_recorded(self):
        mw= FakeMainWindow()
        self._create_plate(mw, width=8, height=6)
        core.reduce_borders(mw.plates[0])
        mw.session_recorder.record_reduce_borders(mw.plates.id_at(0))
        F.handle_undo(mw)

        self._oxidize_current(mw, lambda c: c[0] > 0 and c[1] < 0, prob_oh=100)

        current_id= mw.plates.id_at(0)
        steps= mw.session_recorder.to_dict()["plates"][0]["steps"]
        self.assertEqual(len(steps), 1, "la oxidación tiene que quedar grabada en el árbol de steps")
        self.assertEqual(steps[0]["type"], "oxidation")
        self.assertTrue(mw.session_recorder.can_undo())

    def test_full_repro_two_oxidations_after_undo_then_undo_once_more(self):
        mw= FakeMainWindow()
        self._create_plate(mw, width=12, height=8)
        core.reduce_borders(mw.plates[0])
        mw.session_recorder.record_reduce_borders(mw.plates.id_at(0))

        F.handle_undo(mw)  # 1er Ctrl-Z: vuelve a la placa lisa
        self.assertEqual(len(mw.plates), 1)

        self._oxidize_current(mw, lambda c: c[0] > 0 and c[1] < 0, prob_oh=100)  # OH
        oh_count= len(mw.plates[0].get_oxide_coords())
        self.assertGreater(oh_count, 0)

        self._oxidize_current(mw, lambda c: c[0] < 0 and c[1] > 0, prob_oh=0)  # OE
        self.assertGreater(len(mw.plates[0].get_oxide_coords()), oh_count)

        F.handle_undo(mw)  # 2do Ctrl-Z: BUG real -- perdía TODA la sesión acá

        self.assertEqual(len(mw.plates), 1, "la placa no debería desaparecer")
        self.assertEqual(len(mw.plates[0].get_oxide_coords()), oh_count,
                          "debería quedar solo la oxidación OH, la OE es la que se deshace")
        self.assertTrue(mw.session_recorder.can_undo(),
                         "todavía debería poder deshacerse el reduce_borders original")


if __name__ == "__main__":
    unittest.main()
