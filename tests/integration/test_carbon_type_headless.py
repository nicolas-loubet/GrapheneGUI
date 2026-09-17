import os
import tempfile
import unittest

from graphenegui.logic import core


class TestCarbonTypeHeadless(unittest.TestCase):
    def test_set_carbon_type_step_reaches_top_export(self):
        create_params= {
            "width": 30, "height": 20, "factor": 1.0,
            "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        }
        probe= core.build_plate_from_create(create_params)
        c0= probe.get_carbon_coords()[0]
        x_ang, y_ang, z_ang= [v * 10 for v in c0[:3]]

        cfg= {
            "plates": [
                {
                    "name": "a",
                    "create": create_params,
                    "steps": [
                        {"type": "set_carbon_type", "carbon_type": "ce",
                         "carbons": [[x_ang, y_ang, z_ang]]},
                    ],
                },
            ],
            "atom_types": [{"name": "ce", "epsilon": 0.3, "sigma": 3.4}],
            "export": {"formats": ["top"], "output_dir": ".", "name": "carbon_type_test"},
        }

        plates_by_name, plates, duplicates_list, atom_types, periodicity= core.build_session_from_config(cfg)
        plate= plates_by_name["a"]

        self.assertEqual(plate.get_carbon_coords()[0][6], "ce")

        with tempfile.TemporaryDirectory() as tmp:
            out_file= os.path.join(tmp, "carbon_type_test.top")
            core.export_plates(out_file, plates, periodicity,
                                atom_types=atom_types, duplicates_list=duplicates_list)
            with open(out_file) as f:
                content= f.read()
            self.assertIn("ce", content)


if __name__ == "__main__":
    unittest.main()
