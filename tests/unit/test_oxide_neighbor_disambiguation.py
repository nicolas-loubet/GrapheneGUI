import unittest
from graphenegui.logic.graphene import Graphene
from graphenegui.logic import core


class TestGetNearestCarbonsToOxideKClosest(unittest.TestCase):
    def test_oe_always_finds_exactly_two_neighbors_even_after_cnt(self):
        """El caso real que disparó el bug: muchos OE en una placa 30x20
        enrollada en CNT [2,0] encontraban 3 o 4 vecinos en vez de 2."""
        plate= core.build_plate_from_create({
            "width": 30, "height": 20, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        core.apply_oxidation(plate, plate.get_carbon_coords(), z_mode=2, prob_oh=0)
        core.apply_cnt(plate, [2.0, 0.0])

        oe_oxides= [ox for ox in plate.get_oxide_coords() if ox[3] == "OE"]
        self.assertGreater(len(oe_oxides), 0)
        for ox in oe_oxides:
            neighbors= plate.get_nearest_carbons_to_oxide(ox)
            self.assertEqual(len(neighbors), 2, f"OE en {ox[:3]} encontró {len(neighbors)} vecinos, no 2")

    def test_oo_finds_exactly_one_neighbor(self):
        plate= core.build_plate_from_create({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        core.apply_oxidation(plate, plate.get_carbon_coords(), z_mode=2, prob_oh=100)
        oo_oxides= [ox for ox in plate.get_oxide_coords() if ox[3] == "OO"]
        self.assertGreater(len(oo_oxides), 0)
        for ox in oo_oxides:
            neighbors= plate.get_nearest_carbons_to_oxide(ox)
            self.assertEqual(len(neighbors), 1)

    def test_neighbors_are_sorted_closest_first_on_flat_plate(self):
        """Regresión: en una placa plana (sin ambigüedad), el resultado sigue
        siendo el/los carbono(s) real(es), igual que con el mecanismo viejo."""
        plate= core.build_plate_from_create({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        core.apply_oxidation(plate, plate.get_carbon_coords(), z_mode=2, prob_oh=0)
        oe_oxides= [ox for ox in plate.get_oxide_coords() if ox[3] == "OE"]
        for ox in oe_oxides:
            neighbors= plate.get_nearest_carbons_to_oxide(ox)
            self.assertEqual(len(neighbors), 2)
            d0= plate.distance_3D(ox[0], ox[1], ox[2], *neighbors[0][:3])
            d1= plate.distance_3D(ox[0], ox[1], ox[2], *neighbors[1][:3])
            self.assertLessEqual(d0, d1)  # ordenados por distancia

    def test_mol2_export_has_balanced_ce_cf_after_cnt_with_epoxides(self):
        """Regresión end-to-end: en el .mol2/.gro exportado, la cantidad de
        átomos 'CE' y 'CF' tiene que coincidir siempre (uno por cada OE)."""
        import tempfile, os
        plate= core.build_plate_from_create({
            "width": 30, "height": 20, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        core.apply_oxidation(plate, plate.get_carbon_coords(), z_mode=2, prob_oh=0)
        core.apply_cnt(plate, [2.0, 0.0])

        with tempfile.TemporaryDirectory() as tmp:
            out= os.path.join(tmp, "test.gro")
            core.export_plates(out, [plate], [False, False])
            with open(out) as f:
                lines= f.readlines()

        n= int(lines[1].strip())
        ce_count= cf_count= 0
        for line in lines[2:2 + n]:
            name= line[10:15].strip()
            letters= "".join(c for c in name if not c.isdigit())
            if letters == "CE": ce_count+= 1
            if letters == "CF": cf_count+= 1
        self.assertEqual(ce_count, cf_count)
        self.assertGreater(ce_count, 0)


class TestExactBondTracking(unittest.TestCase):
    """El fix de fondo (a pedido, no solo el K-más-cercano ni el greedy
    global -- ninguno de los dos alcanzaba): el carbono real unido a cada
    óxido se graba por atom_index EN EL MOMENTO de oxidar (mientras la
    placa está siempre plana), en Graphene.oxide_bonds -- no se re-deriva
    por geometría después de enrollar. Confirmado en vivo: ni siquiera el
    greedy global (que sí evitaba que un carbono fuera compartido) alcanzaba
    -- podía "robarle" el carbono correcto a un óxido para dárselo a otro
    más cercano por error (9 de 122 OE se quedaban con 1 solo carbono, 1
    con ninguno, aun sin ningún carbono compartido)."""

    def test_soft_oxidation_records_the_real_bond(self):
        plate= core.build_plate_from_create({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        core.apply_oxidation(plate, plate.get_carbon_coords(), z_mode=2, prob_oh=0)
        oe= [ox for ox in plate.get_oxide_coords() if ox[3] == "OE"][0]
        self.assertIn(oe[4], plate.oxide_bonds)
        self.assertEqual(len(plate.oxide_bonds[oe[4]]), 2)

    def test_bond_survives_cnt_roll_exactly(self):
        """El caso central: enlace grabado ANTES de enrollar, la placa se
        enrolla, y la resolución sigue siendo exacta -- ya no por
        geometría post-roll (que es lo que fallaba con curvatura fuerte)."""
        plate= core.build_plate_from_create({
            "width": 30, "height": 20, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        core.apply_oxidation(plate, plate.get_carbon_coords(), z_mode=2, prob_oh=0)
        oe_oxides= [ox for ox in plate.get_oxide_coords() if ox[3] == "OE"]
        # Guardo qué carbonos correspondían ANTES de enrollar
        expected= {ox[4]: plate.oxide_bonds[ox[4]] for ox in oe_oxides}

        core.apply_cnt(plate, [2.0, 0.0])

        for ox in oe_oxides:
            bonded= plate.get_bonded_carbons_for_oxide(ox)
            self.assertEqual(len(bonded), 2)
            self.assertEqual(tuple(sorted(c[4] for c in bonded)), tuple(sorted(expected[ox[4]])))

    def test_bond_survives_duplicate(self):
        plate= core.build_plate_from_create({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        core.apply_oxidation(plate, plate.get_carbon_coords(), z_mode=2, prob_oh=0)
        dup= plate.duplicate([0, 0, 30])
        self.assertEqual(dup.oxide_bonds, plate.oxide_bonds)

    def test_hard_replica_replay_also_records_the_bond(self):
        """apply_oxidation_explicit (modo hard, usado por el replay headless)
        también tiene que derivar y grabar el enlace -- ahí no se conoce el
        carbono de antemano (solo posiciones), así que se deriva por
        geometría UNA VEZ, mientras la placa recién construida sigue plana."""
        plate= core.build_plate_from_create({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        c0= plate.get_carbon_coords()[0]
        c1= plate.carbons_adjacent(c0)[0]  # vecino real, para armar un epóxido de verdad
        x_mid= (c0[0] + c1[0]) / 2
        y_mid= (c0[1] + c1[1]) / 2
        z_mid= (c0[2] + c1[2]) / 2 + 0.126
        # apply_oxidation_explicit espera nm (sin *10) -- la conversión desde
        # Å la hace la capa de arriba (apply_oxidation_step, para el step del
        # YAML), no esta función.
        core.apply_oxidation_explicit(plate, [(x_mid, y_mid, z_mid, "OE")])

        oe= plate.get_oxide_coords()[0]
        self.assertIn(oe[4], plate.oxide_bonds)
        self.assertEqual(len(plate.oxide_bonds[oe[4]]), 2)

    def test_imported_oxide_without_bond_falls_back_to_geometry(self):
        """Un óxido sin bond grabado (importado de un archivo, por ejemplo)
        sigue funcionando -- cae al mecanismo geométrico de siempre."""
        plate= core.build_plate_from_create({
            "width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
            "periodic_boundary_x": False, "periodic_boundary_y": False,
        })
        c0= plate.get_carbon_coords()[0]
        # Agrego un óxido a mano, SIN pasar bonded_carbon_indices (como
        # haría un import_formats.readGRO/readMOL2/etc.)
        plate.add_oxide(c0[0], c0[1], c0[2] + 0.149, "OO", 9999)
        ox= plate.get_oxide_coords()[-1]
        self.assertNotIn(ox[4], plate.oxide_bonds)
        bonded= plate.get_bonded_carbons_for_oxide(ox)
        self.assertEqual(len(bonded), 1)
        self.assertEqual(bonded[0][4], c0[4])


if __name__ == "__main__":
    unittest.main()
