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
        self._plates= {}           # nombre -> {"create": {...}, "steps": [...]}
        self._plate_order= []      # mantiene el orden de creación
        self._duplicates= []       # [{"source":..., "translation":..., "absolute":...}]
        self._atom_types= []       # [{"name":..., "epsilon":..., "sigma":...}]
        self._next_plate_index= 0  # para autogenerar "plateN" si no se da nombre

    # ================================
    # Placas
    # ================================

    def record_plate_created(self, create_params, name=None):
        """create_params: dict con width/height/factor/center/periodic_boundary_x/y
        (Å para width/height/center, igual que el resto del schema). Devuelve el
        nombre asignado a la placa (autogenerado si no se pasó uno)."""
        self._next_plate_index+= 1
        if name is None:
            name= f"plate{self._next_plate_index}"
        if name in self._plates:
            raise ValueError(f"Plate name already recorded: {name!r}")
        self._plates[name]= {"create": dict(create_params), "steps": []}
        self._plate_order.append(name)
        return name

    def remove_plate(self, plate_name):
        """Para cuando la GUI borra una placa (delete_actual_plate): la saca del
        recorder y limpia cualquier duplicado que la referenciara como fuente."""
        if plate_name in self._plates:
            del self._plates[plate_name]
            self._plate_order.remove(plate_name)
        self._duplicates= [d for d in self._duplicates if d["source"] != plate_name]

    def known_plates(self):
        return list(self._plate_order)

    def has_plate(self, name):
        return name in self._plates

    def _steps_for(self, plate_name):
        if plate_name not in self._plates:
            raise ValueError(f"Unknown plate: {plate_name!r} (¿se registró con record_plate_created?)")
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

    # ================================
    # Duplicados
    # ================================

    def record_duplicate(self, source_plate_name, translation, absolute=False):
        if source_plate_name not in self._plates:
            raise ValueError(f"Unknown source plate: {source_plate_name!r}")
        self._duplicates.append({
            "source": source_plate_name,
            "translation": list(translation),
            "absolute": absolute,
        })

    # ================================
    # Tipos de átomo custom
    # ================================

    def record_atom_type(self, name, epsilon, sigma):
        self._atom_types.append({"name": name, "epsilon": epsilon, "sigma": sigma})

    # ================================
    # Salida
    # ================================

    def is_empty(self):
        return not self._plate_order

    def to_dict(self, export_formats=None, output_dir=".", export_name="graphene"):
        """Arma el dict con la misma forma del schema multi-placa de la Etapa 1.
        La Etapa 6 (serializar a YAML de verdad) solo tiene que volcar esto con
        yaml.safe_dump."""
        return {
            "plates": [
                {"name": name, **self._plates[name]}
                for name in self._plate_order
            ],
            "duplicates": list(self._duplicates),
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
            "# Pensado para reproducirse con: graphene-gui-cli -c este_archivo.yaml\n"
            "# (cli.py todavía no lee este schema multi-placa tal cual — ver TODO Etapa 8)\n"
        )
        return header + yaml.safe_dump(data, sort_keys=False, default_flow_style=False, allow_unicode=True)

    def save(self, file_path, export_formats=None, output_dir=".", export_name="graphene"):
        """Escribe to_yaml() en file_path. Devuelve file_path, para poder encadenar
        (ej. mostrarlo en un mensaje de confirmación)."""
        content= self.to_yaml(export_formats=export_formats, output_dir=output_dir, export_name=export_name)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path
