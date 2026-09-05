"""
Recorder de sesión para "Guardar trabajo": junta en memoria todo lo hecho en
una sesión de la GUI, en una forma que mapea directo al schema YAML
multi-placa diseñado en la Etapa 1 (ver headless_config_multiplate_example.yaml
en la raíz del proyecto).

No sabe nada de Qt ni de main_window — solo junta datos. La Etapa 5 conecta
sus métodos a los puntos reales de la GUI; to_yaml()/save() (Etapa 6) vuelcan
to_dict() a un archivo YAML de verdad.
"""
import yaml


class SessionRecorder:
    def __init__(self):
        self._plates= {}           # nombre -> {"create"|"duplicate_of"+"translation"+"absolute", "steps": [...]}
        self._plate_order= []      # mantiene el orden de creación
        self._atom_types= []       # [{"name":..., "epsilon":..., "sigma":...}]
        self._next_plate_index= 0  # para autogenerar "plateN" si no se da nombre
        self._modified= False      # Etapa 16: ¿hay cambios sin guardar?

    def _mark_modified(self):
        self._modified= True

    def is_modified(self):
        return self._modified

    def mark_saved(self):
        """Llamar después de un save() exitoso -- limpia el flag de 'sin
        guardar' (Etapa 16, usado por Open Work para decidir si hace falta
        ofrecer guardar antes de cerrar la sesión actual)."""
        self._modified= False

    # ================================
    # Placas
    # ================================

    def _register_name(self, name):
        self._next_plate_index+= 1
        if name is None:
            name= f"plate{self._next_plate_index}"
        if name in self._plates:
            raise ValueError(f"Plate name already recorded: {name!r}")
        return name

    def record_plate_created(self, create_params, name=None):
        """create_params: dict con width/height/factor/center/periodic_boundary_x/y
        (Å para width/height/center, igual que el resto del schema). Devuelve el
        nombre asignado a la placa (autogenerado si no se pasó uno)."""
        name= self._register_name(name)
        self._plates[name]= {"create": dict(create_params), "steps": []}
        self._plate_order.append(name)
        self._mark_modified()
        return name

    def remove_plate(self, plate_name):
        """Para cuando la GUI borra una placa (delete_actual_plate): la saca del
        recorder. Si otra placa la tenía como duplicate_of, esa referencia queda
        colgante a propósito — el replay (core.build_session_from_config) va a
        fallar con un error claro ("unknown source plate") en vez de fallar
        silenciosamente o inventar datos; no se intenta "reparar" solo."""
        if plate_name in self._plates:
            del self._plates[plate_name]
            self._plate_order.remove(plate_name)
            self._mark_modified()

    def known_plates(self):
        return list(self._plate_order)

    def has_plate(self, name):
        return name in self._plates

    def _steps_for(self, plate_name):
        if plate_name not in self._plates:
            raise ValueError(f"Unknown plate: {plate_name!r} (¿se registró con record_plate_created o record_duplicate?)")
        self._mark_modified()
        return self._plates[plate_name]["steps"]

    # ================================
    # Oxidación
    # ================================

    def record_oxidation_soft(self, plate_name, expression, fraction, prob_oh, z_mode):
        """El modo 'como quedó' (select_atoms_expr + put_oxides de la GUI): guarda los
        parámetros usados, no el resultado. Sirve para documentar qué se hizo, pero
        replayearlo no garantiza el mismo subconjunto exacto de átomos (ver Etapa 2)."""
        self._steps_for(plate_name).append({
            "type": "oxidation", "mode": "soft",
            "expression": expression, "fraction": fraction,
            "prob_oh": prob_oh, "z_mode": z_mode,
        })

    def record_oxidation_hard(self, plate_name, oxide_atoms):
        """oxide_atoms: lista de [x, y, z, type] en Å — los átomos de óxido YA
        RESUELTOS que quedaron agregados. Es la que usa 'Guardar trabajo' para poder
        reproducir la sesión tal cual (ver core.apply_oxidation_explicit, Etapa 2)."""
        self._steps_for(plate_name).append({
            "type": "oxidation", "mode": "hard",
            "oxides": [list(atom) for atom in oxide_atoms],
        })

    def record_oxidation_removed(self, plate_name, oxide_atom):
        """La GUI permite remover un grupo OH/O manualmente. Se guarda como su propio
        evento en el log (no se edita retroactivamente un step anterior), para que
        quien reproduzca (Etapa 8) aplique todo en el mismo orden en que pasó."""
        self._steps_for(plate_name).append({
            "type": "oxidation_removed",
            "oxide": list(oxide_atom),
        })

    def record_oxidation_cleared(self, plate_name):
        """'Reduce All' de la GUI: saca TODOS los óxidos de la placa de una. Un único
        evento compacto en vez de un oxidation_removed por átomo."""
        self._steps_for(plate_name).append({"type": "oxidation_cleared"})

    # ================================
    # reduce_borders y CNT
    # ================================

    def record_reduce_borders(self, plate_name):
        self._steps_for(plate_name).append({"type": "reduce_borders"})

    def record_cnt(self, plate_name, vector):
        self._steps_for(plate_name).append({"type": "cnt", "vector": list(vector)})

    def record_cnt_restored(self, plate_name):
        """Deshacer un CNT (plate.restore_plate() en la GUI, botón CNT
        clickeado de nuevo sobre una placa ya enrollada). No lleva datos
        propios -- el replay (core.apply_step) deshace el 'cnt' que haya
        quedado activo inmediatamente antes en la misma lista de steps.
        Después de esto la placa vuelve a ser editable (puede llevar más
        steps atrás, incluido otro 'cnt' más adelante)."""
        self._steps_for(plate_name).append({"type": "cnt_restored"})

    # ================================
    # Tipo de carbono (Etapa 12)
    # ================================

    def record_carbon_type(self, plate_name, carbons, new_type):
        """La GUI permite asignar un tipo (CE/CO/custom) a un lote de carbonos, o
        resetearlos al tipo default — ambos casos pasan por acá, no hay distinción
        a nivel dato (reset es simplemente new_type=DEFAULT_CARBON_TYPE). Igual que
        con oxidación, se graba siempre por posición YA RESUELTA (no hay modo
        'soft': no existe nada probabilístico en elegir un tipo). Un evento por
        cada aplicación (pintar o resetear), no se pisan entre sí, mismo criterio
        que record_oxidation_removed — así se preserva el orden real en que pasó.
        carbons: lista de [x, y, z] en Å."""
        self._steps_for(plate_name).append({
            "type": "set_carbon_type", "carbon_type": new_type,
            "carbons": [list(c) for c in carbons],
        })

    # ================================
    # Duplicados (Etapa 11: son placas trackeables más, no un caso aparte)
    # ================================

    def record_duplicate(self, source_plate_name, translation, absolute=False, name=None):
        """El duplicado pasa a ser una placa más en _plates, con su propia lista de
        steps — así se puede seguir editando (oxidar, CNT, etc.) y esas ediciones
        SÍ quedan grabadas, a diferencia de como era antes. 'source_plate_name'
        tiene que ser una placa ya registrada (con record_plate_created o
        record_duplicate). Devuelve el nombre asignado al duplicado."""
        if source_plate_name not in self._plates:
            raise ValueError(f"Unknown source plate: {source_plate_name!r}")
        name= self._register_name(name)
        self._plates[name]= {
            "duplicate_of": source_plate_name,
            "translation": list(translation),
            "absolute": absolute,
            "steps": [],
        }
        self._plate_order.append(name)
        self._mark_modified()
        return name

    # ================================
    # Tipos de átomo custom
    # ================================

    def record_atom_type(self, name, epsilon, sigma):
        self._atom_types.append({"name": name, "epsilon": epsilon, "sigma": sigma})
        self._mark_modified()

    # ================================
    # Salida
    # ================================

    def is_empty(self):
        return not self._plate_order

    def to_dict(self, export_formats=None, output_dir=".", export_name="graphene"):
        """Arma el dict con la misma forma del schema multi-placa (Etapa 1, unificado
        en la Etapa 11: 'plates' es la única lista, cada entrada es 'create' o
        'duplicate_of' — ya no hay una sección 'duplicates' aparte)."""
        return {
            "plates": [
                {"name": name, **self._plates[name]}
                for name in self._plate_order
            ],
            "atom_types": list(self._atom_types),
            "export": {
                "formats": export_formats or ["mol2"],
                "output_dir": output_dir,
                "name": export_name,
            },
        }

    def to_yaml(self, export_formats=None, output_dir=".", export_name="graphene"):
        """Arma el YAML completo (mismo schema que to_dict()) como texto, listo para
        guardar en un archivo o mostrar en un preview antes de guardar."""
        data= self.to_dict(export_formats=export_formats, output_dir=output_dir, export_name=export_name)
        header= (
            "# Generado por \"Guardar trabajo\".\n"
            "# Reproducible con: graphene-gui-cli -c este_archivo.yaml\n"
        )
        return header + yaml.safe_dump(data, sort_keys=False, default_flow_style=False, allow_unicode=True)

    def save(self, file_path, export_formats=None, output_dir=".", export_name="graphene"):
        """Escribe to_yaml() en file_path. Devuelve file_path, para poder encadenar
        (ej. mostrarlo en un mensaje de confirmación)."""
        content= self.to_yaml(export_formats=export_formats, output_dir=output_dir, export_name=export_name)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path
