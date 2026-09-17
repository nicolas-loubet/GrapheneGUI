import unittest
from graphenegui.logic.graphene import Graphene
from graphenegui.logic import core


def _load_remove_oxides_from_selection():
    import importlib.util
    import re
    spec= importlib.util.find_spec("graphenegui.logic.functionalities")
    with open(spec.origin) as f:
        src= f.read()
    start= src.index("def remove_oxides_from_selection")
    next_def= re.search(r"\ndef ", src[start+1:])
    end= start+1+next_def.start() if next_def else len(src)
    ns= {}
    exec(src[start:end], ns)
    return ns["remove_oxides_from_selection"]


class FakeRecorder:
    def __init__(self):
        self.calls= []
    def has_plate(self, pid):
        return True
    def record_oxidation_removed(self, plate_id, ox):
        self.calls.append(ox)

class FakePlates:
    def __init__(self, plate):
        self.plate= plate
    def id_at(self, pos):
        return "plateA"
    def __getitem__(self, pos):
        return self.plate

class FakeCombo:
    def currentIndex(self):
        return 0

class FakeUI:
    def __init__(self):
        self.comboDrawings= FakeCombo()

class FakeMainWindow:
    def __init__(self, plate):
        self.plates= FakePlates(plate)
        self.session_recorder= FakeRecorder()
        self.ui= FakeUI()
        self.update_calls= 0
    def update_drawing_area(self):
        self.update_calls+= 1


class TestRemoveOxidesFromSelection(unittest.TestCase):
    def setUp(self):
        self.remove_oxides_from_selection= _load_remove_oxides_from_selection()

    def test_empty_selection_is_noop(self):
        plate= Graphene.create_from_params(4, 3, 0, 0, 0, 1.0, False, False)
        mw= FakeMainWindow(plate)
        result= self.remove_oxides_from_selection(mw, [])
        self.assertEqual(result, 0)
        self.assertEqual(mw.update_calls, 0)

    def test_removes_all_oxides_in_full_selection(self):
        plate= Graphene.create_from_params(6, 4, 0, 0, 0, 1.0, False, False)
        carbons= plate.get_carbon_coords()
        core.apply_oxidation(plate, carbons, z_mode=2, prob_oh=50)
        self.assertGreater(len(plate.get_oxide_coords()), 0)
        mw= FakeMainWindow(plate)

        self.remove_oxides_from_selection(mw, carbons)
        self.assertEqual(len(plate.get_oxide_coords()), 0)
        self.assertEqual(mw.update_calls, 1)

    def test_shared_epoxide_between_two_selected_carbons_is_not_double_removed(self):
        plate= Graphene.create_from_params(6, 4, 0, 0, 0, 1.0, False, False)
        carbons= plate.get_carbon_coords()
        # prob_oh=0 fuerza epóxidos (OE) siempre que haya un vecino libre
        core.apply_oxidation(plate, carbons, z_mode=2, prob_oh=0)
        oe_oxides= [ox for ox in plate.get_oxide_coords() if ox[3] == "OE"]
        self.assertGreater(len(oe_oxides), 0, "necesito al menos un OE para este test")

        ox= oe_oxides[0]
        parents= plate.get_nearest_carbons_to_oxide(ox)
        self.assertEqual(len(parents), 2, "un OE debería tener exactamente 2 carbonos padres")

        mw= FakeMainWindow(plate)
        removed= self.remove_oxides_from_selection(mw, parents)  # ambos carbonos puente
        self.assertEqual(removed, 1, "debería remover UNA sola vez el óxido compartido")
        self.assertEqual(len(mw.session_recorder.calls), 1, "debería grabarse UNA sola vez")

    def test_records_removed_oxides(self):
        plate= Graphene.create_from_params(4, 3, 0, 0, 0, 1.0, False, False)
        carbons= plate.get_carbon_coords()
        core.apply_oxidation(plate, carbons, z_mode=2, prob_oh=100)  # solo OH, sin epóxidos
        mw= FakeMainWindow(plate)
        oxide_count= len([ox for ox in plate.get_oxide_coords() if ox[3] != "HO"])

        removed= self.remove_oxides_from_selection(mw, carbons)
        self.assertEqual(removed, len(mw.session_recorder.calls))
        self.assertGreater(removed, 0)


if __name__ == "__main__":
    unittest.main()
