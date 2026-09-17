import unittest
import os
import tempfile
import yaml as yamlmod
from graphenegui.logic.plate_registry import PlateRegistry
from graphenegui.logic.recorder import SessionRecorder


def _load_open_work():
    import importlib.util
    spec= importlib.util.find_spec("graphenegui.logic.functionalities")
    full_src= open(spec.origin).read()

    ns= {
        "core": __import__("graphenegui.logic.core", fromlist=["core"]),
        "yaml": __import__("yaml"),
        "DEFAULT_CARBON_TYPE": __import__("graphenegui.logic.graphene", fromlist=["x"]).DEFAULT_CARBON_TYPE,
    }

    rc_start= full_src.index("def record_carbon_type_change")
    rc_end= full_src.index("def apply_ctype_to_selection")
    exec(full_src[rc_start:rc_end], ns)

    ow_start= full_src.index("def open_work(main_window):")
    exec(full_src[ow_start:], ns)  # open_work es la última función del archivo
    return ns["open_work"], ns


class _FakeFileDialog:
    path= None
    @staticmethod
    def getOpenFileName(*a, **k):
        return (_FakeFileDialog.path, "")

class _FakeMsgBox:
    @staticmethod
    def critical(*a, **k): pass
    @staticmethod
    def information(*a, **k): pass

class _FakeCombo:
    def __init__(self):
        self.items= []
    def addItem(self, t):
        self.items.append(t)
    def setCurrentIndex(self, i):
        pass

class _FakeUI:
    def __init__(self):
        self.comboDrawings= _FakeCombo()
        self.comboCType= _FakeCombo()

class _FakeMainWindow:
    def __init__(self):
        self.plates= PlateRegistry()
        self.session_recorder= SessionRecorder()
        self.ui= _FakeUI()
        self.atom_types= {"ca": {"epsilon": 0.359824, "sigma": 3.39967}}
    def buttons_that_depend_of_having_a_plate(self, active): pass
    def update_ctype_controls_enabled(self): pass
    def update_drawing_area(self): pass


class TestOpenWorkWithNestedDuplicateSchema(unittest.TestCase):
    def setUp(self):
        self.open_work, self.ns= _load_open_work()
        self.ns["QFileDialog"]= _FakeFileDialog
        self.ns["QMessageBox"]= _FakeMsgBox

    def _run_open_work_on(self, cfg):
        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "session.yaml")
            with open(path, "w") as f:
                yamlmod.safe_dump(cfg, f)
            _FakeFileDialog.path= path
            mw= _FakeMainWindow()
            self.open_work(mw)
            return mw

    def test_duplicated_plate_reappears_in_the_registry(self):
        cfg= {"plates": [{
            "name": "plate1",
            "create": {"width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
                       "periodic_boundary_x": False, "periodic_boundary_y": False},
            "steps": [
                {"type": "duplicate", "name": "plate2", "translation": [0, 0, 30],
                 "absolute": False, "steps": []},
            ],
        }]}
        mw= self._run_open_work_on(cfg)
        self.assertEqual(len(mw.plates), 2)
        self.assertEqual(mw.ui.comboDrawings.items, ["Plate 1", "Plate 2"])

    def test_central_case_duplicate_flat_source_rerolled_after(self):
        cfg= {"plates": [{
            "name": "plate1",
            "create": {"width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
                       "periodic_boundary_x": False, "periodic_boundary_y": False},
            "steps": [
                {"type": "cnt", "vector": [2, 0]},
                {"type": "cnt_restored"},
                {"type": "duplicate", "name": "plate2", "translation": [0, 0, 40],
                 "absolute": False, "steps": []},
                {"type": "cnt", "vector": [1, 1]},
            ],
        }]}
        mw= self._run_open_work_on(cfg)
        plate1, plate2= mw.plates[0], mw.plates[1]
        self.assertTrue(plate1.get_is_CNT())
        self.assertFalse(plate2.get_is_CNT())
        zs= [c[2] for c in plate2.get_carbon_coords()]
        self.assertAlmostEqual(max(zs) - min(zs), 0.0, places=6)

    def test_reopened_duplicate_is_registered_in_recorder(self):
        cfg= {"plates": [{
            "name": "plate1",
            "create": {"width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
                       "periodic_boundary_x": False, "periodic_boundary_y": False},
            "steps": [
                {"type": "duplicate", "name": "plate2", "translation": [0, 0, 30],
                 "absolute": False, "steps": []},
            ],
        }]}
        mw= self._run_open_work_on(cfg)
        plate2_id= mw.plates.id_at(1)
        self.assertTrue(mw.session_recorder.has_plate(plate2_id))


if __name__ == "__main__":
    unittest.main()
