import os
import tempfile
import unittest

from graphenegui.logic import cli
from graphenegui.logic import import_formats as inf


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

    def test_cnt_successful_roll(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir= os.path.join(tmp, "out")
            cli.main([
                "--set", "plate.width=60",
                "--set", "plate.height=60",
                "--set", "cnt.enabled=true",
                "--set", "cnt.vector=[2.0, 0]",
                "--set", f"export.output_dir={output_dir}",
                "--set", "export.name=cnt_plate",
                "--set", "export.formats=[mol2]",
            ])
            self.assertTrue(os.path.exists(os.path.join(output_dir, "cnt_plate.mol2")))

    def test_duplicates_produce_multiple_plates_in_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path= os.path.join(tmp, "config.yaml")
            output_dir= os.path.join(tmp, "out")
            with open(config_path, "w") as f:
                f.write(f"""
plate:
  width: 30
  height: 30

duplicates:
  - translation: [0, 0, 34]
  - translation: [0, 0, 68]

export:
  formats: [gro]
  output_dir: {output_dir}
  name: multi
""")
            cli.main(["-c", config_path])
            gro_path= os.path.join(output_dir, "multi.gro")
            self.assertTrue(os.path.exists(gro_path))
            plates_read= inf.readGRO(gro_path)
            self.assertEqual(len(plates_read), 3)  # base + 2 duplicados

    def test_custom_atom_types_reach_top_export(self):
        """No tengo a la vista el cuerpo completo de writeTOP — si esto falla, puede
        ser una señal real de que atom_types no llega adonde yo asumo, no un bug mío
        en el test. Avisar la salida completa si falla."""
        with tempfile.TemporaryDirectory() as tmp:
            config_path= os.path.join(tmp, "config.yaml")
            output_dir= os.path.join(tmp, "out")
            with open(config_path, "w") as f:
                f.write(f"""
plate:
  width: 30
  height: 30

atom_types:
  - name: ca2
    epsilon: 0.3
    sigma: 3.2

export:
  formats: [top]
  output_dir: {output_dir}
  name: customtypes
""")
            cli.main(["-c", config_path])
            top_path= os.path.join(output_dir, "customtypes.top")
            self.assertTrue(os.path.exists(top_path))
            self.assertIn("ca2", open(top_path).read())

    def _hard_replica_config(self, output_dir, name):
        return f"""
plate:
  width: 40
  height: 40
  factor: 1.0

oxidation:
  - mode: hard
    oxides:
      - [0.000, 7.100, 1.49, "OO"]
      - [0.930, 7.100, 1.81, "HO"]
      - [24.500, 0.000, 1.49, "OO"]
      - [25.430, 0.000, 1.81, "HO"]

export:
  formats: [mol2]
  output_dir: {output_dir}
  name: {name}
"""

    def test_hard_replica_is_deterministic_across_runs(self):
        """Correr el mismo config hard replica dos veces tiene que dar exactamente
        el mismo archivo, sin ningún elemento de azar de por medio."""
        with tempfile.TemporaryDirectory() as tmp:
            config_path= os.path.join(tmp, "config.yaml")
            with open(config_path, "w") as f:
                f.write(self._hard_replica_config(os.path.join(tmp, "out1"), "run"))
            cli.main(["-c", config_path])

            with open(config_path, "w") as f:
                f.write(self._hard_replica_config(os.path.join(tmp, "out2"), "run"))
            cli.main(["-c", config_path])

            content1= open(os.path.join(tmp, "out1", "run.mol2")).read()
            content2= open(os.path.join(tmp, "out2", "run.mol2")).read()
            self.assertEqual(content1, content2)

    def test_hard_replica_oxidizes_exact_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path= os.path.join(tmp, "config.yaml")
            output_dir= os.path.join(tmp, "out")
            with open(config_path, "w") as f:
                f.write(self._hard_replica_config(output_dir, "hard"))
            cli.main(["-c", config_path])

            plates_read= inf.readMOL2(os.path.join(output_dir, "hard.mol2"))
            self.assertEqual(plates_read[0].get_oxide_count(), 2)  # 2 sitios OO, no cuenta los HO

    def test_hard_replica_missing_oxides_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path= os.path.join(tmp, "config.yaml")
            with open(config_path, "w") as f:
                f.write(f"""
plate:
  width: 30
  height: 30
oxidation:
  - mode: hard
export:
  formats: [mol2]
  output_dir: {os.path.join(tmp, "out")}
""")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])

    def test_unknown_oxidation_mode_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path= os.path.join(tmp, "config.yaml")
            with open(config_path, "w") as f:
                f.write(f"""
plate:
  width: 30
  height: 30
oxidation:
  - mode: bogus
export:
  formats: [mol2]
  output_dir: {os.path.join(tmp, "out")}
""")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])


if __name__ == "__main__":
    unittest.main()
