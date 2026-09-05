"""
Etapa 18: Open Work rompía el round-trip de una placa CNT sin restaurar.

open_work reconstruye el recorder tomando una foto del estado final (óxidos,
tipos de carbono). Si la placa terminaba enrollada en CNT, esa foto usaba
plate.get_carbon_coords()/get_oxide_coords() -- posiciones YA ROLLEADAS.
Guardar esa foto y reabrirla reconstruía una placa PLANA desde 'create', y
esas posiciones no matcheaban ningún carbono real ahí (find_carbon_at
explotaba con ValueError). El fix usa plate.backup_not_CNT (que
Graphene.set_is_CNT ya guarda con las posiciones PRE-roll, para poder
restaurar) para la foto, y agrega el step 'cnt' original DESPUÉS -- el orden
de replay queda: crear -> oxidar/tipos (planos) -> enrollar.

Esta lógica vive inline dentro de open_work() en functionalities.py (que
necesita PySide6 para los diálogos, no importable acá) -- se prueba
reproduciendo el mismo cálculo a mano contra core.build_session_from_config,
que es exactamente lo que open_work usa por debajo.
"""
import unittest
from graphenegui.logic import core
from graphenegui.logic.graphene import DEFAULT_CARBON_TYPE
from graphenegui.logic.recorder import SessionRecorder


def _atoms_close(a, b, tol=1e-6):
    """Compara dos tuplas de átomo (carbono u óxido) con tolerancia de punto
    flotante en x,y,z -- exige nombre/tipo iguales. La conversión nm->Å->nm
    que hace el schema (todo se guarda en Å) introduce ruido de punto
    flotante inherente al resto del proyecto, no específico de esta etapa."""
    if a[3] != b[3] or a[6] != b[6]:
        return False
    return all(abs(a[i] - b[i]) < tol for i in (0, 1, 2))


def _snapshot_and_rerecord_like_open_work(plate, plate_cfg, recorder, plate_id):
    """Reproduce la parte relevante de open_work (Etapa 18) para poder
    probarla sin PySide6: toma la foto de óxidos/tipos (desde backup_not_CNT
    si la placa quedó enrollada) y agrega el step 'cnt' si corresponde."""
    is_cnt= plate.get_is_CNT()
    if is_cnt:
        snapshot_carbons, snapshot_oxides, _unused= plate.backup_not_CNT
    else:
        snapshot_carbons, snapshot_oxides= plate.get_carbon_coords(), plate.get_oxide_coords()

    if snapshot_oxides:
        oxide_atoms= [[x * 10, y * 10, z * 10, t] for x, y, z, t, *_ in snapshot_oxides]
        recorder.record_oxidation_hard(plate_id, oxide_atoms)

    non_default= [c for c in snapshot_carbons if c[6] != DEFAULT_CARBON_TYPE]
    by_type= {}
    for c in non_default:
        by_type.setdefault(c[6], []).append(c)
    for ctype, carbons in by_type.items():
        positions= [[c[0] * 10, c[1] * 10, c[2] * 10] for c in carbons]
        recorder.record_carbon_type(plate_id, positions, ctype)

    if is_cnt:
        last_step= plate_cfg.get("steps", [])[-1]
        assert last_step["type"] == "cnt", "garantizado por validate_steps (Etapa 14)"
        recorder.record_cnt(plate_id, last_step["vector"])


class TestOpenWorkCntRoundTrip(unittest.TestCase):
    def test_reopening_a_rolled_plate_and_resaving_reproduces_it_exactly(self):
        create_params= {"width": 30, "height": 20, "factor": 1.0, "center": [0, 0, 0],
                         "periodic_boundary_x": False, "periodic_boundary_y": False}
        probe= core.build_plate_from_create(create_params)
        carbons_for_ctype= [[c[0] * 10, c[1] * 10, c[2] * 10] for c in probe.get_carbon_coords()[:2]]

        cfg_a= {
            "plates": [{
                "name": "a", "create": create_params,
                "steps": [
                    {"type": "oxidation", "mode": "soft", "expression": "", "fraction": 0.3,
                     "prob_oh": 50, "z_mode": 2},
                    {"type": "set_carbon_type", "carbon_type": "ce", "carbons": carbons_for_ctype},
                    {"type": "cnt", "vector": [2, 0]},
                ],
            }],
            "atom_types": [{"name": "ce", "epsilon": 0.3, "sigma": 3.4}],
        }

        plates_by_name_a, _, _, _, _= core.build_session_from_config(cfg_a)
        plate_a= plates_by_name_a["a"]
        self.assertTrue(plate_a.get_is_CNT())

        # Simula lo que hace open_work al "abrir" cfg_a
        r= SessionRecorder()
        plate_cfg= cfg_a["plates"][0]
        plate_id= r.record_plate_created(plate_cfg.get("create", {}), name="a")
        _snapshot_and_rerecord_like_open_work(plate_a, plate_cfg, r, plate_id)
        r.record_atom_type("ce", 0.3, 3.4)

        # El YAML que "Guardar trabajo" produciría justo después de reabrir
        cfg_b= r.to_dict()

        # Reabrir ESE segundo YAML no debería tirar ValueError (que es
        # justamente lo que pasaba antes del fix, al no matchear posiciones)
        plates_by_name_b, _, _, _, _= core.build_session_from_config(cfg_b)
        plate_b= plates_by_name_b["a"]

        self.assertTrue(plate_b.get_is_CNT())

        carbons_a, carbons_b= plate_a.get_carbon_coords(), plate_b.get_carbon_coords()
        oxides_a, oxides_b= plate_a.get_oxide_coords(), plate_b.get_oxide_coords()
        self.assertEqual(len(carbons_a), len(carbons_b))
        self.assertEqual(len(oxides_a), len(oxides_b))
        self.assertTrue(all(_atoms_close(x, y) for x, y in zip(carbons_a, carbons_b)))
        self.assertTrue(all(_atoms_close(x, y) for x, y in zip(oxides_a, oxides_b)))

    def test_non_cnt_plate_snapshot_unaffected(self):
        """La placa SIN CNT sigue tomando la foto directo de get_carbon_coords/
        get_oxide_coords, como ya hacía antes de esta etapa -- no se rompió
        el camino normal (sin CNT) al tocar esto."""
        create_params= {"width": 20, "height": 15, "factor": 1.0, "center": [0, 0, 0],
                         "periodic_boundary_x": False, "periodic_boundary_y": False}
        cfg= {
            "plates": [{
                "name": "a", "create": create_params,
                "steps": [{"type": "oxidation", "mode": "soft", "expression": "", "fraction": 0.5,
                           "prob_oh": 50, "z_mode": 2}],
            }],
        }
        plates_by_name, _, _, _, _= core.build_session_from_config(cfg)
        plate= plates_by_name["a"]
        self.assertFalse(plate.get_is_CNT())

        r= SessionRecorder()
        plate_id= r.record_plate_created(cfg["plates"][0].get("create", {}), name="a")
        _snapshot_and_rerecord_like_open_work(plate, cfg["plates"][0], r, plate_id)

        steps= [s["type"] for s in r._plates["a"]["steps"]]
        self.assertEqual(steps, ["oxidation"])  # sin 'cnt' de más


if __name__ == "__main__":
    unittest.main()
