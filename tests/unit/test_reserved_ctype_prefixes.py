"""
Etapa 15: core.build_atom_types rechaza nombres de tipo de carbono custom
que colisionen con los prefijos de 2 caracteres reservados por el
exportador (ATOM_PARAMS_TOP en export_formats.py: "CE", "CO", "OE", "OO",
"HO") -- write_atoms_top busca por type_atom[:2] en ese diccionario, así que
un tipo custom cuyo nombre EMPIECE con cualquiera de esos prefijos exporta
en silencio con la carga/masa de otro elemento (ej. un tipo "OO1" para
carbono terminaría exportado como si fuera un óxido "oh").
"""
import unittest
from graphenegui.logic import core


class TestBuildAtomTypesRejectsReservedPrefixes(unittest.TestCase):
    def test_rejects_exact_reserved_names(self):
        for bad in ["CE", "CO", "OE", "OO", "HO"]:
            with self.assertRaises(ValueError):
                core.build_atom_types({"atom_types": [{"name": bad, "epsilon": 0.1, "sigma": 3.0}]})

    def test_rejects_names_starting_with_reserved_prefix(self):
        """No hace falta que el nombre sea EXACTAMENTE 'CE'/'CO'/etc -- alcanza
        con que empiece así, porque write_atoms_top mira solo type_atom[:2]."""
        for bad in ["CE2", "COx", "OE1", "OOxide", "HO99"]:
            with self.assertRaises(ValueError):
                core.build_atom_types({"atom_types": [{"name": bad, "epsilon": 0.1, "sigma": 3.0}]})

    def test_allows_normal_names(self):
        for ok_name in ["ce", "co", "ca", "myType", "X1"]:
            result= core.build_atom_types({"atom_types": [{"name": ok_name, "epsilon": 0.1, "sigma": 3.0}]})
            self.assertIn(ok_name, result)

    def test_empty_atom_types_is_fine(self):
        self.assertEqual(core.build_atom_types({}), {})


if __name__ == "__main__":
    unittest.main()
