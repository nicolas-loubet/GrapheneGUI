import os
import tempfile
import unittest

from graphenegui.logic import cli


class TestCliEndToEnd(unittest.TestCase):
    def test_config_file_builds_and_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path= os.path.join(tmp, "config.yaml")
            output_dir= os.path.join(tmp, "out")
            with open(config_path, "w") as f:
                f.write(f"""
plate:
  width: 40
  height: 40
  factor: 1.0

oxidation:
  - expression: ""
    fraction: 1.0
    prob_oh: 100
    z_mode: random

export:
  formats: [mol2, gro]
  output_dir: {output_dir}
  name: test_plate
""")
            cli.main(["-c", config_path])

            self.assertTrue(os.path.exists(os.path.join(output_dir, "test_plate.mol2")))
            self.assertTrue(os.path.exists(os.path.join(output_dir, "test_plate.gro")))

    def test_set_overrides_without_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir= os.path.join(tmp, "out")
            cli.main([
                "--set", "plate.width=30",
                "--set", "plate.height=30",
                "--set", f"export.output_dir={output_dir}",
                "--set", "export.name=noconfig",
                "--set", "export.formats=[xyz]",
            ])
            self.assertTrue(os.path.exists(os.path.join(output_dir, "noconfig.xyz")))

    def test_cnt_zero_vector_exits(self):
        with self.assertRaises(SystemExit):
            cli.main([
                "--set", "plate.width=30",
                "--set", "plate.height=30",
                "--set", "cnt.enabled=true",
                "--set", "cnt.vector=[0, 0]",
            ])

    def test_no_args_exits(self):
        with self.assertRaises(SystemExit):
            cli.main([])


if __name__ == "__main__":
    unittest.main()
