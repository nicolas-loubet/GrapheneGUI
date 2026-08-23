import filecmp
import os
import tempfile
import unittest

from graphenegui.logic import cli

GOLDEN_DIR= os.path.dirname(__file__)
CONFIG_PATH= os.path.join(GOLDEN_DIR, "basic_plate.yaml")


class TestGoldenFiles(unittest.TestCase):
    """Compara la salida real del headless contra archivos de referencia ya
    generados (basic_plate.mol2/.gro en esta misma carpeta). El config es
    determinístico (prob_oh=100, fraction=1.0, z_mode fijo — no depende de la
    semilla del random), así que la salida tiene que ser byte a byte idéntica
    en cada corrida. Si este test falla después de tocar graphene.py,
    export_formats.py o core.py, es una señal real de que algo cambió el
    resultado — no lo arregles regenerando el golden file sin revisar antes
    qué cambió y por qué."""

    def _run_and_compare(self, filename):
        with tempfile.TemporaryDirectory() as tmp:
            cli.main([
                "-c", CONFIG_PATH,
                "--set", f"export.output_dir={tmp}",
                "--set", "export.formats=[mol2, gro]",
            ])
            generated= os.path.join(tmp, filename)
            reference= os.path.join(GOLDEN_DIR, filename)
            self.assertTrue(os.path.exists(generated), f"No se generó {filename}")
            self.assertTrue(
                filecmp.cmp(generated, reference, shallow=False),
                f"{filename} generado no coincide byte a byte con el golden file de referencia",
            )

    def test_mol2_matches_reference(self):
        self._run_and_compare("basic_plate.mol2")

    def test_gro_matches_reference(self):
        self._run_and_compare("basic_plate.gro")


if __name__ == "__main__":
    unittest.main()
