import unittest
from graphenegui.logic.recorder import SessionRecorder
from graphenegui.logic import core


class TestDuplicateAsNestedStep(unittest.TestCase):
    def test_recorder_nests_duplicate_step_inside_source(self):
        r= SessionRecorder()
        name= r.record_plate_created({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        r.record_cnt(name, [2.0, 0.0])
        r.record_cnt_restored(name)
        dup= r.record_duplicate(name, [0.0, 0.0, 40.0])
        r.record_cnt(name, [1.0, 1.0])

        steps= r._roots[name]["steps"]
        types= [s["type"] for s in steps]
        self.assertEqual(types, ["cnt", "cnt_restored", "duplicate", "cnt"])
        self.assertEqual(steps[2]["name"], dup)
        self.assertEqual(steps[2]["steps"], [])  # el duplicado no tuvo ediciones propias

    def test_duplicate_reflects_source_state_at_duplication_point_not_final_state(self):
        """El caso central de la etapa: duplicar mientras la fuente está
        PLANA, y recién después volver a enrollarla -- el duplicado tiene
        que quedar plano, no enrollado."""
        r= SessionRecorder()
        name= r.record_plate_created({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        r.record_cnt(name, [2.0, 0.0])
        r.record_cnt_restored(name)   # vuelve a estar plana
        dup= r.record_duplicate(name, [0.0, 0.0, 40.0])   # duplicar ACÁ, plana
        r.record_cnt(name, [1.0, 1.0])   # y recién ahora se re-enrolla la FUENTE

        cfg= r.to_dict()
        plates_by_name, _, _, _, _= core.build_session_from_config(cfg)
        source_plate= plates_by_name[name]
        dup_plate= plates_by_name[dup]

        self.assertTrue(source_plate.get_is_CNT())
        self.assertFalse(dup_plate.get_is_CNT())
        zs= [c[2] for c in dup_plate.get_carbon_coords()]
        self.assertAlmostEqual(max(zs) - min(zs), 0.0, places=6)

    def test_simple_duplicate_without_further_source_edits_still_works(self):
        """Regresión: el caso más común y simple (duplicar y no tocar más
        la fuente) tiene que seguir andando igual que siempre."""
        r= SessionRecorder()
        name= r.record_plate_created({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        r.record_duplicate(name, [0, 0, 30])
        cfg= r.to_dict()
        plates_by_name, _, _, _, _= core.build_session_from_config(cfg)
        self.assertEqual(len(plates_by_name), 2)

    def test_duplicate_can_still_have_its_own_steps(self):
        r= SessionRecorder()
        name= r.record_plate_created({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        dup= r.record_duplicate(name, [0, 0, 30])
        r.record_oxidation_hard(dup, [[0, 0, 1, "OO"]])
        cfg= r.to_dict()
        plates_by_name, _, _, _, _= core.build_session_from_config(cfg)
        self.assertGreaterEqual(len(plates_by_name[dup].get_oxide_coords()), 1)

    def test_nested_duplicate_of_a_duplicate(self):
        """Un duplicado de un duplicado (2 niveles de anidamiento)."""
        r= SessionRecorder()
        n1= r.record_plate_created({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        n2= r.record_duplicate(n1, [0, 0, 30])
        n3= r.record_duplicate(n2, [0, 0, 60])
        cfg= r.to_dict()
        plates_by_name, _, _, _, _= core.build_session_from_config(cfg)
        self.assertEqual(len(plates_by_name), 3)
        self.assertIn(n3, plates_by_name)

    def test_top_level_entry_without_create_is_rejected(self):
        cfg= {
            "plates": [
                {"name": "a", "create": {"width": 10, "height": 10, "factor": 1.0,
                                          "center": [0, 0, 0], "periodic_boundary_x": False,
                                          "periodic_boundary_y": False}},
                {"name": "b", "duplicate_of": "a", "translation": [0, 0, 10]},
            ],
        }
        with self.assertRaises(ValueError):
            core.build_session_from_config(cfg)

    def test_validate_steps_ignores_duplicate_for_cnt_sequencing(self):
        """Un 'duplicate' no cuenta como edición de la placa actual -- no
        rompe la regla de 'cnt debe seguir de cnt_restored o ser el último'."""
        core.validate_steps("p", [
            {"type": "cnt", "vector": [1, 0]},
            {"type": "duplicate", "name": "d", "translation": [0, 0, 10], "steps": []},
        ])  # no debería levantar -- el duplicate no "sigue" al cnt en el sentido de editarlo

    def test_validate_steps_recurses_into_duplicate_steps(self):
        """Los steps propios del duplicado también se validan -- acá el
        duplicado tiene un cnt sin restaurar seguido de otro step, inválido."""
        with self.assertRaises(ValueError):
            core.validate_steps("p", [
                {"type": "duplicate", "name": "d", "translation": [0, 0, 10], "steps": [
                    {"type": "cnt", "vector": [1, 0]},
                    {"type": "oxidation", "mode": "hard", "oxides": []},
                ]},
            ])

    def test_remove_plate_removes_nested_duplicate_step(self):
        r= SessionRecorder()
        name= r.record_plate_created({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        dup= r.record_duplicate(name, [0, 0, 30])
        r.remove_plate(dup)
        self.assertFalse(r.has_plate(dup))
        self.assertEqual(r._roots[name]["steps"], [])  # el step 'duplicate' se sacó de ahí

    def test_remove_plate_cascades_to_grandchildren(self):
        """Fix propio encontrado al actualizar los tests: borrar una placa
        con un duplicado de un duplicado anidado (2 niveles) tenía que
        limpiar TODO el subárbol del bookkeeping (has_plate/known_plates),
        no solo desaparecer del YAML -- antes el nieto quedaba huérfano
        en el registro interno aunque ya fuera inalcanzable en to_dict()."""
        r= SessionRecorder()
        n1= r.record_plate_created({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        n2= r.record_duplicate(n1, [0, 0, 30])
        n3= r.record_duplicate(n2, [0, 0, 60])  # nieto de n1

        r.remove_plate(n1)

        self.assertEqual(r.known_plates(), [])
        self.assertFalse(r.has_plate(n2))
        self.assertFalse(r.has_plate(n3))

    def test_yaml_roundtrip_preserves_nesting(self):
        r= SessionRecorder()
        name= r.record_plate_created({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        r.record_duplicate(name, [0, 0, 30])
        y= r.to_yaml()
        self.assertIn("type: duplicate", y)
        # No debería quedar ningún rastro del schema viejo
        self.assertNotIn("duplicate_of:", y)


class TestIterPlateBuildOrder(unittest.TestCase):
    """core.iter_plate_build_order: usado por open_work (functionalities.py,
    no importable acá por PySide6) para reconstruir main_window.plates
    (un PlateRegistry) con la relación padre/hijo correcta -- ya no puede
    asumir 'duplicate_of' de nivel superior."""

    def test_simple_root_no_duplicates(self):
        cfg= {"plates": [{"name": "a", "create": {}, "steps": []}]}
        order= core.iter_plate_build_order(cfg)
        self.assertEqual(order, [("a", None, None, None, None)])

    def test_root_ending_rolled_reports_cnt_vector(self):
        cfg= {"plates": [{"name": "a", "create": {}, "steps": [
            {"type": "oxidation", "mode": "hard", "oxides": []},
            {"type": "cnt", "vector": [1, 1]},
        ]}]}
        order= core.iter_plate_build_order(cfg)
        self.assertEqual(order, [("a", None, None, None, [1, 1])])

    def test_root_restored_reports_no_cnt_vector(self):
        cfg= {"plates": [{"name": "a", "create": {}, "steps": [
            {"type": "cnt", "vector": [1, 1]},
            {"type": "cnt_restored"},
        ]}]}
        order= core.iter_plate_build_order(cfg)
        self.assertEqual(order, [("a", None, None, None, None)])

    def test_the_central_case_duplicate_flat_then_reroll_source(self):
        cfg= {"plates": [{"name": "a", "create": {}, "steps": [
            {"type": "cnt", "vector": [2, 0]},
            {"type": "cnt_restored"},
            {"type": "duplicate", "name": "b", "translation": [0, 0, 40],
             "absolute": False, "steps": []},
            {"type": "cnt", "vector": [1, 1]},
        ]}]}
        order= core.iter_plate_build_order(cfg)
        self.assertEqual(order, [
            ("a", None, None, None, [1, 1]),
            ("b", "a", [0, 0, 40], False, None),
        ])

    def test_nested_duplicate_of_a_duplicate_order(self):
        cfg= {"plates": [{"name": "a", "create": {}, "steps": [
            {"type": "duplicate", "name": "b", "translation": [0, 0, 10], "absolute": False, "steps": [
                {"type": "duplicate", "name": "c", "translation": [0, 0, 20], "absolute": False, "steps": []},
            ]},
        ]}]}
        order= core.iter_plate_build_order(cfg)
        names_and_parents= [(n, p) for n, p, *_ in order]
        self.assertEqual(names_and_parents, [("a", None), ("b", "a"), ("c", "b")])


if __name__ == "__main__":
    unittest.main()
