import unittest
import tempfile
import os
from graphenegui.logic.graphene import Graphene
from graphenegui.logic import core


def _mol2_types_by_count(mol2_path, mol2_type):
    with open(mol2_path) as f:
        lines= f.readlines()
    atom_section= False
    count= 0
    for l in lines:
        if l.startswith("@<TRIPOS>ATOM"):
            atom_section= True
            continue
        if l.startswith("@<TRIPOS>BOND"):
            atom_section= False
        if atom_section:
            parts= l.split()
            if len(parts) >= 6 and parts[5] == mol2_type:
                count+= 1
    return count


class TestCustomCarbonTypeReachesMol2(unittest.TestCase):
    def test_custom_type_appears_literally_in_mol2(self):
        plate= Graphene.create_from_params(6, 4, 0, 0, 0, 1.0, False, False)
        core.apply_oxidation(plate, plate.get_carbon_coords(), z_mode=2, prob_oh=50)

        targets= plate.get_carbon_coords()[:3]
        core.apply_carbon_type_explicit(plate, [tuple(c[:3]) for c in targets], "ce2")

        with tempfile.TemporaryDirectory() as tmp:
            out= os.path.join(tmp, "test.mol2")
            core.export_plates(out, [plate], [False, False])
            count= _mol2_types_by_count(out, "ce2")

        self.assertEqual(count, 3)

    def test_default_carbons_still_export_as_ca_or_oxidized_variant(self):
        """Regresión: el fix no debería tocar el comportamiento existente
        para carbonos SIN tipo custom (sigue usando get_oxides_for_carbon
        para decidir ca/c3-CO/cx-CE, como ya hacía)."""
        plate= Graphene.create_from_params(6, 4, 0, 0, 0, 1.0, False, False)
        core.apply_oxidation(plate, plate.get_carbon_coords(), z_mode=2, prob_oh=50)

        with tempfile.TemporaryDirectory() as tmp:
            out= os.path.join(tmp, "test.mol2")
            core.export_plates(out, [plate], [False, False])
            count_ca= _mol2_types_by_count(out, "ca")
            count_c3= _mol2_types_by_count(out, "c3")
            count_cx= _mol2_types_by_count(out, "cx")

        self.assertGreater(count_ca + count_c3 + count_cx, 0)


if __name__ == "__main__":
    unittest.main()
