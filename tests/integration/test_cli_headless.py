import os
import tempfile
import unittest

from graphenegui.logic import cli
from graphenegui.logic import core as core_module
from graphenegui.logic import import_formats as inf
from graphenegui.logic.graphene import Graphene


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


class TestMultiPlateSchema(unittest.TestCase):
    def _write_config(self, tmp, plates_yaml, extra_yaml=""):
        config_path= os.path.join(tmp, "config.yaml")
        output_dir= os.path.join(tmp, "out")
        with open(config_path, "w") as f:
            f.write(f"""
{plates_yaml}
{extra_yaml}
export:
  formats: [gro]
  output_dir: {output_dir}
  name: multi
""")
        return config_path, output_dir

    def test_two_independent_plates_export_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, output_dir= self._write_config(tmp, """
plates:
  - name: a
    create:
      width: 30
      height: 30
  - name: b
    create:
      width: 20
      height: 20
""")
            cli.main(["-c", config_path])
            plates_read= inf.readGRO(os.path.join(output_dir, "multi.gro"))
            self.assertEqual(len(plates_read), 2)

    def test_soft_oxidation_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, output_dir= self._write_config(tmp, """
plates:
  - name: a
    create:
      width: 30
      height: 30
    steps:
      - type: oxidation
        mode: soft
        expression: ""
        fraction: 1.0
        prob_oh: 100
        z_mode: "+z"
""")
            cli.main(["-c", config_path])
            plates_read= inf.readGRO(os.path.join(output_dir, "multi.gro"))
            self.assertGreater(plates_read[0].get_oxide_count(), 0)

    def test_hard_oxidation_step_with_real_coordinates(self):
        # Coordenadas de un carbono REAL de esta placa (no inventadas) — si no,
        # get_nearest_carbons_to_oxide no encuentra ningún carbono cerca (mismo bug
        # preexistente de distance_2D que documentamos con el ejemplo CNT).
        n_x, n_y= core_module.compute_plate_grid(30, 30, 1.0)
        probe= Graphene.create_from_params(n_x, n_y, 0, 0, 0, 1.0, False)
        cx, cy, cz= probe.get_carbon_coords()[0][:3]
        oo= [cx*10, cy*10, (cz+0.149)*10, "OO"]
        ho= [(cx+0.093)*10, cy*10, (cz+0.181)*10, "HO"]

        with tempfile.TemporaryDirectory() as tmp:
            config_path, output_dir= self._write_config(tmp, f"""
plates:
  - name: a
    create:
      width: 30
      height: 30
    steps:
      - type: oxidation
        mode: hard
        oxides:
          - {oo}
          - {ho}
""")
            cli.main(["-c", config_path])
            plates_read= inf.readGRO(os.path.join(output_dir, "multi.gro"))
            self.assertEqual(plates_read[0].get_oxide_count(), 1)

    def test_cnt_step_must_be_last(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, _= self._write_config(tmp, """
plates:
  - name: a
    create:
      width: 30
      height: 30
    steps:
      - type: cnt
        vector: [10, 0]
      - type: reduce_borders
""")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])

    def test_reduce_borders_and_cnt_same_plate_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, _= self._write_config(tmp, """
plates:
  - name: a
    create:
      width: 30
      height: 30
    steps:
      - type: reduce_borders
      - type: cnt
        vector: [10, 0]
""")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])

    def test_missing_plate_name_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, _= self._write_config(tmp, """
plates:
  - create:
      width: 30
      height: 30
""")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])

    def test_duplicate_plate_name_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, _= self._write_config(tmp, """
plates:
  - name: a
    create:
      width: 30
      height: 30
  - name: a
    create:
      width: 20
      height: 20
""")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])

    def test_duplicates_reference_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, output_dir= self._write_config(tmp, """
plates:
  - name: a
    create:
      width: 30
      height: 30
  - name: b
    create:
      width: 20
      height: 20
    steps:
      - type: duplicate
        name: b_dup
        translation: [0, 0, 34]
        absolute: false
        steps: []
""")
            cli.main(["-c", config_path])
            plates_read= inf.readGRO(os.path.join(output_dir, "multi.gro"))
            self.assertEqual(len(plates_read), 3)  # a, b, duplicado de b

    def test_duplicate_can_have_its_own_steps(self):
        n_x, n_y= core_module.compute_plate_grid(20, 20, 1.0)
        probe= Graphene.create_from_params(n_x, n_y, 0, 0, 34/10, 1.0, False)  # ya trasladada en z
        cx, cy, cz= probe.get_carbon_coords()[0][:3]
        oo= [cx*10, cy*10, (cz+0.149)*10, "OO"]
        ho= [(cx+0.093)*10, cy*10, (cz+0.181)*10, "HO"]

        with tempfile.TemporaryDirectory() as tmp:
            config_path, output_dir= self._write_config(tmp, f"""
plates:
  - name: b
    create:
      width: 20
      height: 20
    steps:
      - type: duplicate
        name: b_dup
        translation: [0, 0, 34]
        absolute: false
        steps:
          - type: oxidation
            mode: hard
            oxides:
              - {oo}
              - {ho}
""")
            cli.main(["-c", config_path])
            plates_read= inf.readGRO(os.path.join(output_dir, "multi.gro"))
            self.assertEqual(plates_read[0].get_oxide_count(), 0)   # b, sin tocar
            self.assertEqual(plates_read[1].get_oxide_count(), 1)   # b_dup, con su propio óxido

    def test_duplicate_name_collision_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, _= self._write_config(tmp, """
plates:
  - name: a
    create:
      width: 30
      height: 30
    steps:
      - type: duplicate
        name: a
        translation: [0, 0, 34]
        absolute: false
        steps: []
""")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])

    def test_duplicate_step_missing_name_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, _= self._write_config(tmp, """
plates:
  - name: a
    create:
      width: 30
      height: 30
    steps:
      - type: duplicate
        translation: [0, 0, 34]
        absolute: false
        steps: []
""")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])

    def test_top_level_duplicate_of_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, _= self._write_config(tmp, """
plates:
  - name: a
    create:
      width: 30
      height: 30
  - name: a_dup
    duplicate_of: a
    translation: [0, 0, 34]
""")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])

    def test_empty_plates_list_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path, _= self._write_config(tmp, "plates: []")
            with self.assertRaises(SystemExit):
                cli.main(["-c", config_path])

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

    def test_reduce_borders_adds_hydrogens_to_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir= os.path.join(tmp, "out")
            cli.main([
                "--set", "plate.width=40",
                "--set", "plate.height=40",
                "--set", "reduce_borders=true",
                "--set", f"export.output_dir={output_dir}",
                "--set", "export.name=borders",
                "--set", "export.formats=[gro]",
            ])
            plates_read= inf.readGRO(os.path.join(output_dir, "borders.gro"))
            self.assertGreater(len(plates_read[0].get_hydrogens_coords()), 0)

    def test_reduce_borders_and_cnt_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            cli.main([
                "--set", "plate.width=40",
                "--set", "plate.height=40",
                "--set", "reduce_borders=true",
                "--set", "cnt.enabled=true",
                "--set", "cnt.vector=[10, 0]",
            ])


if __name__ == "__main__":
    unittest.main()
