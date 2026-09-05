"""
Etapa 14: tests de SessionRecorder.record_cnt_restored.
"""
import unittest
from graphenegui.logic.recorder import SessionRecorder


class TestCntRestoreRecording(unittest.TestCase):
    def setUp(self):
        self.recorder= SessionRecorder()
        self.plate_name= self.recorder.record_plate_created({
            "width": 10, "height": 10, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })

    def test_records_bare_step_no_data(self):
        self.recorder.record_cnt(self.plate_name, [1, 0])
        self.recorder.record_cnt_restored(self.plate_name)
        steps= self.recorder._plates[self.plate_name]["steps"]
        self.assertEqual(steps, [
            {"type": "cnt", "vector": [1, 0]},
            {"type": "cnt_restored"},
        ])

    def test_allows_further_editing_and_rerolling_afterwards(self):
        self.recorder.record_cnt(self.plate_name, [1, 0])
        self.recorder.record_cnt_restored(self.plate_name)
        self.recorder.record_oxidation_hard(self.plate_name, [[0, 0, 1, "OO"]])
        self.recorder.record_cnt(self.plate_name, [2, 0])
        types= [s["type"] for s in self.recorder._plates[self.plate_name]["steps"]]
        self.assertEqual(types, ["cnt", "cnt_restored", "oxidation", "cnt"])

    def test_raises_on_unknown_plate(self):
        with self.assertRaises(ValueError):
            self.recorder.record_cnt_restored("no_existe")

    def test_to_yaml_roundtrips(self):
        self.recorder.record_cnt(self.plate_name, [1, 0])
        self.recorder.record_cnt_restored(self.plate_name)
        y= self.recorder.to_yaml()
        self.assertIn("cnt_restored", y)


if __name__ == "__main__":
    unittest.main()
