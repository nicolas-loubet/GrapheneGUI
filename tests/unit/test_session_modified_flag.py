import unittest
from graphenegui.logic.recorder import SessionRecorder


class TestModifiedFlag(unittest.TestCase):
    def setUp(self):
        self.recorder= SessionRecorder()

    def test_starts_unmodified(self):
        self.assertFalse(self.recorder.is_modified())

    def test_creating_a_plate_marks_modified(self):
        self.recorder.record_plate_created({
            "width": 10, "height": 10, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        self.assertTrue(self.recorder.is_modified())

    def test_mark_saved_clears_the_flag(self):
        name= self.recorder.record_plate_created({
            "width": 10, "height": 10, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        self.recorder.mark_saved()
        self.assertFalse(self.recorder.is_modified())

    def test_every_mutation_kind_marks_modified_again_after_a_save(self):
        name= self.recorder.record_plate_created({
            "width": 10, "height": 10, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        self.recorder.mark_saved()

        self.recorder.record_oxidation_hard(name, [[0, 0, 1, "OO"]])
        self.assertTrue(self.recorder.is_modified())
        self.recorder.mark_saved()

        dup_name= self.recorder.record_duplicate(name, [0, 0, 10])
        self.assertTrue(self.recorder.is_modified())
        self.recorder.mark_saved()

        self.recorder.record_atom_type("ce", 0.1, 3.0)
        self.assertTrue(self.recorder.is_modified())
        self.recorder.mark_saved()

        self.recorder.remove_plate(dup_name)
        self.assertTrue(self.recorder.is_modified())

    def test_reading_steps_does_not_mark_modified(self):
        name= self.recorder.record_plate_created({
            "width": 10, "height": 10, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        self.recorder.mark_saved()
        self.recorder.to_dict()
        self.recorder.to_yaml()
        self.assertFalse(self.recorder.is_modified())


if __name__ == "__main__":
    unittest.main()
