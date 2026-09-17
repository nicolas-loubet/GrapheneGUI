import os
import tempfile
import unittest

import yaml

from graphenegui.logic.recorder import SessionRecorder


class TestPlateRegistration(unittest.TestCase):
    def test_record_plate_created_autonames(self):
        rec= SessionRecorder()
        name1= rec.record_plate_created({"width": 40, "height": 40})
        name2= rec.record_plate_created({"width": 30, "height": 30})
        self.assertEqual([name1, name2], ["plate1", "plate2"])
        self.assertEqual(rec.known_plates(), ["plate1", "plate2"])

    def test_has_plate(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 40, "height": 40}, name="base")
        self.assertTrue(rec.has_plate("base"))
        self.assertFalse(rec.has_plate("nope"))

    def test_record_plate_created_explicit_name(self):
        rec= SessionRecorder()
        name= rec.record_plate_created({"width": 40, "height": 40}, name="base")
        self.assertEqual(name, "base")

    def test_duplicate_name_raises(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 40, "height": 40}, name="base")
        with self.assertRaises(ValueError):
            rec.record_plate_created({"width": 30, "height": 30}, name="base")

    def test_step_on_unknown_plate_raises(self):
        rec= SessionRecorder()
        with self.assertRaises(ValueError):
            rec.record_reduce_borders("nope")

    def test_removing_a_plate_cascades_to_its_nested_duplicates(self):
        """Etapa 24: los duplicados viven ANIDADOS dentro de los steps de su
        fuente (ya no son una entrada aparte referenciada por nombre) -- borrar
        la fuente se lleva puesto a cualquier duplicado anidado en ella. Ya no
        puede quedar una referencia colgando a propósito como pasaba con el
        schema viejo (duplicate_of apuntando a un nombre que ya no existe):
        acá el duplicado directamente desaparece con su padre."""
        rec= SessionRecorder()
        rec.record_plate_created({"width": 40, "height": 40}, name="base")
        rec.record_duplicate("base", [0, 0, 34], name="dup")

        rec.remove_plate("base")

        self.assertEqual(rec.known_plates(), [])
        self.assertFalse(rec.has_plate("dup"))

    def test_removing_a_duplicate_leaves_its_source_untouched(self):
        """Al revés: borrar el DUPLICADO (no la fuente) solo saca su propio
        step anidado -- la fuente sigue intacta y editable."""
        rec= SessionRecorder()
        rec.record_plate_created({"width": 40, "height": 40}, name="base")
        rec.record_duplicate("base", [0, 0, 34], name="dup")

        rec.remove_plate("dup")

        self.assertEqual(rec.known_plates(), ["base"])
        self.assertFalse(rec.has_plate("dup"))
        self.assertEqual(rec.to_dict()["plates"][0]["steps"], [])


class TestOxidationRecording(unittest.TestCase):
    def setUp(self):
        self.rec= SessionRecorder()
        self.rec.record_plate_created({"width": 40, "height": 40}, name="base")

    def test_soft_step_records_parameters(self):
        self.rec.record_oxidation_soft("base", "x > 10", 0.7, 70, "random")
        steps= self.rec.to_dict()["plates"][0]["steps"]
        self.assertEqual(steps, [{
            "type": "oxidation", "mode": "soft",
            "expression": "x > 10", "fraction": 0.7,
            "prob_oh": 70, "z_mode": "random",
        }])

    def test_hard_step_records_exact_oxides(self):
        oxides= [[0.0, 7.1, 1.49, "OO"], [0.93, 7.1, 1.81, "HO"]]
        self.rec.record_oxidation_hard("base", oxides)
        steps= self.rec.to_dict()["plates"][0]["steps"]
        self.assertEqual(steps, [{"type": "oxidation", "mode": "hard", "oxides": oxides}])

    def test_hard_step_copies_input_defensively(self):
        oxides= [[0.0, 7.1, 1.49, "OO"]]
        self.rec.record_oxidation_hard("base", oxides)
        oxides.append([1.0, 1.0, 1.0, "OE"])  # mutar la lista original después
        steps= self.rec.to_dict()["plates"][0]["steps"]
        self.assertEqual(len(steps[0]["oxides"]), 1)  # el recorder no vio el segundo

    def test_removal_is_its_own_ordered_event(self):
        self.rec.record_oxidation_hard("base", [[0.0, 7.1, 1.49, "OO"]])
        self.rec.record_oxidation_removed("base", [0.0, 7.1, 1.49, "OO"])
        steps= self.rec.to_dict()["plates"][0]["steps"]
        self.assertEqual([s["type"] for s in steps], ["oxidation", "oxidation_removed"])


class TestOtherSteps(unittest.TestCase):
    def setUp(self):
        self.rec= SessionRecorder()
        self.rec.record_plate_created({"width": 40, "height": 40}, name="base")

    def test_reduce_borders_step(self):
        self.rec.record_reduce_borders("base")
        self.assertEqual(self.rec.to_dict()["plates"][0]["steps"], [{"type": "reduce_borders"}])

    def test_cnt_step(self):
        self.rec.record_cnt("base", [10, 0])
        self.assertEqual(self.rec.to_dict()["plates"][0]["steps"], [{"type": "cnt", "vector": [10, 0]}])

    def test_oxidation_cleared_step(self):
        self.rec.record_oxidation_cleared("base")
        self.assertEqual(self.rec.to_dict()["plates"][0]["steps"], [{"type": "oxidation_cleared"}])

    def test_steps_keep_insertion_order(self):
        self.rec.record_oxidation_soft("base", "", 1.0, 100, "+z")
        self.rec.record_reduce_borders("base")
        steps= self.rec.to_dict()["plates"][0]["steps"]
        self.assertEqual([s["type"] for s in steps], ["oxidation", "reduce_borders"])


class TestDuplicatesAndAtomTypes(unittest.TestCase):
    def test_duplicate_needs_known_source(self):
        rec= SessionRecorder()
        with self.assertRaises(ValueError):
            rec.record_duplicate("nope", [0, 0, 34])

    def test_duplicate_recorded_as_a_trackable_plate(self):
        """Etapa 24 (antes Etapa 11): el duplicado es un step {"type":"duplicate",...}
        anidado dentro de los steps de SU FUENTE (ya no una entrada aparte de
        'plates' con duplicate_of/translation/absolute a nivel superior), con su
        propia lista de steps vacía lista para usarse."""
        rec= SessionRecorder()
        rec.record_plate_created({"width": 40, "height": 40}, name="base")
        dup_name= rec.record_duplicate("base", [0, 0, 34], absolute=True)

        self.assertEqual(dup_name, "plate2")  # autogenerado, sigue el mismo contador
        plates= rec.to_dict()["plates"]
        self.assertEqual(len(plates), 1)  # solo la RAÍZ es entrada de nivel superior
        self.assertEqual(plates[0]["steps"], [{
            "type": "duplicate", "name": "plate2",
            "translation": [0, 0, 34], "absolute": True, "steps": [],
        }])

    def test_duplicate_can_have_its_own_steps(self):
        """El punto central de la Etapa 11 (con el schema de la Etapa 24): se
        puede seguir editando un duplicado y esas ediciones SÍ quedan grabadas
        -- dentro de la lista "steps" anidada de SU PROPIO step "duplicate"."""
        rec= SessionRecorder()
        rec.record_plate_created({"width": 40, "height": 40}, name="base")
        dup_name= rec.record_duplicate("base", [0, 0, 34], name="dup")

        self.assertTrue(rec.has_plate(dup_name))
        rec.record_cnt(dup_name, [10, 0])

        duplicate_step= rec.to_dict()["plates"][0]["steps"][0]
        self.assertEqual(duplicate_step["name"], dup_name)
        self.assertEqual(duplicate_step["steps"], [{"type": "cnt", "vector": [10, 0]}])

    def test_atom_type_recorded(self):
        rec= SessionRecorder()
        rec.record_atom_type("ca2", 0.3, 3.2)
        self.assertEqual(rec.to_dict()["atom_types"], [{"name": "ca2", "epsilon": 0.3, "sigma": 3.2}])


class TestToDict(unittest.TestCase):
    def test_is_empty(self):
        rec= SessionRecorder()
        self.assertTrue(rec.is_empty())
        rec.record_plate_created({"width": 40, "height": 40})
        self.assertFalse(rec.is_empty())

    def test_export_defaults(self):
        rec= SessionRecorder()
        d= rec.to_dict()
        self.assertEqual(d["export"], {"formats": ["mol2"], "output_dir": ".", "name": "graphene"})

    def test_export_overrides(self):
        rec= SessionRecorder()
        d= rec.to_dict(export_formats=["mol2", "top"], output_dir="./out", export_name="mysession")
        self.assertEqual(d["export"], {"formats": ["mol2", "top"], "output_dir": "./out", "name": "mysession"})

    def test_multiple_plates_keep_creation_order(self):
        rec= SessionRecorder()
        rec.record_plate_created({"width": 40, "height": 40}, name="a")
        rec.record_plate_created({"width": 30, "height": 30}, name="b")
        names= [p["name"] for p in rec.to_dict()["plates"]]
        self.assertEqual(names, ["a", "b"])


class TestYamlSerialization(unittest.TestCase):
    def setUp(self):
        self.rec= SessionRecorder()
        self.rec.record_plate_created({"width": 40, "height": 40}, name="base")
        self.rec.record_oxidation_hard("base", [[0.0, 7.1, 1.49, "OO"], [0.93, 7.1, 1.81, "HO"]])
        self.rec.record_duplicate("base", [0, 0, 34], absolute=False)
        self.rec.record_atom_type("ca2", 0.3, 3.2)

    def test_to_yaml_roundtrips_to_same_dict(self):
        text= self.rec.to_yaml(export_formats=["mol2", "top"], output_dir="./out", export_name="session")
        loaded= yaml.safe_load(text)
        self.assertEqual(loaded, self.rec.to_dict(export_formats=["mol2", "top"], output_dir="./out", export_name="session"))

    def test_to_yaml_has_explanatory_header(self):
        text= self.rec.to_yaml()
        self.assertIn("graphene-gui-cli", text)

    def test_save_writes_file_matching_to_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "session.yaml")
            returned= self.rec.save(path, export_name="session")
            self.assertEqual(returned, path)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                content= f.read()
            self.assertEqual(content, self.rec.to_yaml(export_name="session"))

    def test_save_empty_recorder_still_produces_valid_yaml(self):
        empty= SessionRecorder()
        with tempfile.TemporaryDirectory() as tmp:
            path= os.path.join(tmp, "empty.yaml")
            empty.save(path)
            with open(path) as f:
                loaded= yaml.safe_load(f)
            self.assertEqual(loaded["plates"], [])


if __name__ == "__main__":
    unittest.main()
