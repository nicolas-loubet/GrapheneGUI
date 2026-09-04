"""
Etapa 12: test de integración end-to-end para el step 'set_carbon_type' en el
modo headless -- config multi-placa (dict) -> build_session_from_config ->
export .top -> el tipo custom llega al archivo exportado.

Mismo espíritu que test_custom_atom_types_reach_top_export en
tests/integration/test_cli_headless.py (misma advertencia: no tengo a la
vista el cuerpo completo de writeTOP -- si el assert de contenido falla,
puede ser que el tipo se escriba en otra columna/formato del que asumo acá,
no necesariamente que el step esté mal).

NO pude correrlo acá (sandbox sin plate_registry.py/import_formats.py/
export_formats.py) -- va listo para correr con run_tests.py junto al resto.
"""
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
        # Construyo la MISMA placa que va a construir build_session_from_config
        # (mismos create_params) para conocer de antemano la posición real (Å)
        # de un carbono existente -- building con otro grid (ej. una 'probe'
        # aparte con distinto width/height) da coordenadas que no matchean con
        # ningún átomo real de la placa final, y el step falla con un
        # ValueError legítimo (no es un bug del código, es de tener el target
        # mal calculado -- justo lo que pasó en el primer intento de este test).
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

        # El step ya se aplicó adentro de build_session_from_config -- si esto
        # falla, el problema está en apply_step/apply_carbon_type_step, antes
        # de llegar siquiera a exportar.
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
