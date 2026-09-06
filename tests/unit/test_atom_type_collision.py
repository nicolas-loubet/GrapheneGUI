"""
Etapa 21: "Agregar al Work actual" (Open Work, Etapa 16) podía pisar en
silencio un tipo de carbono ya existente en la sesión con otros
epsilon/sigma, y además duplicar la entrada en comboCType (addItem no
chequeaba si ya estaba). _resolve_atom_type_collision decide qué hacer.

Solo se pueden probar acá los 2 caminos que NO abren un QMessageBox (nombre
nuevo, y colisión con los MISMOS valores) -- el camino con valores distintos
sí abre un diálogo (Keep/Overwrite) y no se puede probar sin PySide6.
"""
import unittest


def _load_resolve_atom_type_collision():
    import importlib.util
    spec= importlib.util.find_spec("graphenegui.logic.functionalities")
    with open(spec.origin) as f:
        src= f.read()
    start= src.index("def _resolve_atom_type_collision")
    end= src.index("def open_work(main_window):")
    ns= {}
    exec(src[start:end], ns)
    return ns["_resolve_atom_type_collision"]


class FakeMainWindow:
    def __init__(self, atom_types):
        self.atom_types= atom_types


class TestResolveAtomTypeCollision(unittest.TestCase):
    def setUp(self):
        self.resolve= _load_resolve_atom_type_collision()

    def test_new_name_returns_true_without_prompting(self):
        mw= FakeMainWindow({"ca": {"epsilon": 0.1, "sigma": 3.0}})
        result= self.resolve(mw, "ce", {"epsilon": 0.3, "sigma": 3.4})
        self.assertTrue(result)

    def test_same_values_returns_false_without_prompting(self):
        """No hay colisión real -- son los mismos valores, no hace falta
        preguntar nada ni volver a grabar."""
        mw= FakeMainWindow({"ce": {"epsilon": 0.3, "sigma": 3.4}})
        result= self.resolve(mw, "ce", {"epsilon": 0.3, "sigma": 3.4})
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
