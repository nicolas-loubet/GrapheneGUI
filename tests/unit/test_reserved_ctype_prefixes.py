"""
Etapa 15: core.build_atom_types rechaza nombres de tipo de carbono custom
que colisionen con los prefijos de 2 caracteres reservados por el
exportador (ATOM_PARAMS_TOP en export_formats.py: "CE", "CO", "OE", "OO",
"HO") -- write_atoms_top busca por type_atom[:2] en ese diccionario, así que
un tipo custom cuyo nombre EMPIECE con cualquiera de esos prefijos exporta
en silencio con la carga/masa de otro elemento (ej. un tipo "OO1" para
carbono terminaría exportado como si fuera un óxido "oh").

Etapa 20: además de esos 5 prefijos, write_atoms_top tiene un chequeo APARTE
para hidrógenos autogenerados con nombre "H1"/"H2".../"H999"
(generatePatterns("H") en graphene.py) -- un tipo custom llamado "H" + solo
dígitos (ej. "H2", "H10") cae en ESE chequeo y exporta con los parámetros de
HIDRÓGENO en vez de los del usuario. "H2O" (no es solo dígitos después de la
H) NO debería rechazarse -- ver test_allows_h_names_that_are_not_pure_digits.
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

    def test_rejects_h_plus_digits_reserved_for_hydrogen_naming(self):
        """Etapa 20: 'H' + solo dígitos choca con el chequeo aparte que
        write_atoms_top usa para hidrógenos autogenerados."""
        for bad in ["H2", "H10", "H999", "H0"]:
            with self.assertRaises(ValueError):
                core.build_atom_types({"atom_types": [{"name": bad, "epsilon": 0.1, "sigma": 3.0}]})

    def test_allows_h_names_that_are_not_pure_digits(self):
        """Etapa 20: 'H2O', 'Halo', 'Hx' NO son 'H'+solo-dígitos -- no deberían
        rechazarse (caso límite que separa el chequeo nuevo del anterior)."""
        for ok_name in ["H2O", "Halo", "Hx"]:
            result= core.build_atom_types({"atom_types": [{"name": ok_name, "epsilon": 0.1, "sigma": 3.0}]})
            self.assertIn(ok_name, result)

    def test_allows_normal_names(self):
        for ok_name in ["ce", "co", "ca", "myType", "X1"]:
            result= core.build_atom_types({"atom_types": [{"name": ok_name, "epsilon": 0.1, "sigma": 3.0}]})
            self.assertIn(ok_name, result)

    def test_empty_atom_types_is_fine(self):
        self.assertEqual(core.build_atom_types({}), {})


if __name__ == "__main__":
    unittest.main()
