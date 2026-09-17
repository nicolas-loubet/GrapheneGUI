import unittest
from graphenegui.logic.recorder import SessionRecorder


class TestCarbonTypeRecording(unittest.TestCase):
    def setUp(self):
        self.recorder= SessionRecorder()
        self.plate_name= self.recorder.record_plate_created({
            "width": 10, "height": 10, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })

    def test_records_step_with_correct_shape(self):
        self.recorder.record_carbon_type(self.plate_name, [[0.0, 0.0, 0.0], [1.23, 4.56, 0.0]], "ce")
        steps= self.recorder._roots[self.plate_name]["steps"]
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0], {
            "type": "set_carbon_type", "carbon_type": "ce",
            "carbons": [[0.0, 0.0, 0.0], [1.23, 4.56, 0.0]],
        })

    def test_reset_is_same_mechanism_with_default_type(self):
        self.recorder.record_carbon_type(self.plate_name, [[0.0, 0.0, 0.0]], "ce")
        self.recorder.record_carbon_type(self.plate_name, [[0.0, 0.0, 0.0]], "ca")
        steps= self.recorder._roots[self.plate_name]["steps"]
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0]["type"], "set_carbon_type")
        self.assertEqual(steps[1]["type"], "set_carbon_type")
        self.assertEqual(steps[1]["carbon_type"], "ca")

    def test_each_application_is_its_own_event(self):
        self.recorder.record_carbon_type(self.plate_name, [[0, 0, 0]], "ce")
        self.recorder.record_carbon_type(self.plate_name, [[1, 1, 1]], "co")
        steps= self.recorder._roots[self.plate_name]["steps"]
        self.assertEqual(len(steps), 2)
        self.assertEqual([s["carbon_type"] for s in steps], ["ce", "co"])

    def test_copies_carbons_defensively(self):
        carbons= [[9, 9, 9]]
        self.recorder.record_carbon_type(self.plate_name, carbons, "co")
        carbons.append([1, 1, 1])
        self.assertEqual(self.recorder._roots[self.plate_name]["steps"][-1]["carbons"], [[9, 9, 9]])

    def test_interleaves_in_order_with_other_step_types(self):
        self.recorder.record_oxidation_hard(self.plate_name, [[0, 0, 1, "OO"]])
        self.recorder.record_reduce_borders(self.plate_name)
        self.recorder.record_carbon_type(self.plate_name, [[5, 5, 5]], "ce")
        self.recorder.record_cnt(self.plate_name, [1, 0])
        steps= self.recorder._roots[self.plate_name]["steps"]
        self.assertEqual([s["type"] for s in steps],
                          ["oxidation", "reduce_borders", "set_carbon_type", "cnt"])

    def test_raises_on_unknown_plate(self):
        with self.assertRaises(ValueError):
            self.recorder.record_carbon_type("no_existe", [[0, 0, 0]], "ce")

    def test_to_yaml_roundtrips(self):
        self.recorder.record_carbon_type(self.plate_name, [[0, 0, 0]], "ce")
        d= self.recorder.to_dict()
        self.assertEqual(d["plates"][0]["steps"][0]["type"], "set_carbon_type")
        y= self.recorder.to_yaml()
        self.assertIn("set_carbon_type", y)


if __name__ == "__main__":
    unittest.main()
