"""
Recorder de sesión para "Guardar trabajo": junta en memoria todo lo hecho en
una sesión de la GUI, en una forma que mapea directo al schema YAML
multi-placa diseñado en la Etapa 1 (ver headless_config_multiplate_example.yaml
en la raíz del proyecto).

Etapa 24 (rediseño de fondo): los duplicados YA NO son entradas de nivel
superior en 'plates' con 'duplicate_of'+'translation' separadas de 'steps'.
Ahora son un STEP MÁS, anidado, dentro de los steps de su placa fuente
(type: duplicate), en la posición cronológica EXACTA donde se duplicó de
verdad. Antes, como cada placa era una entrada aparte, el replay
(core.build_session_from_config) siempre completaba TODOS los steps de la
fuente antes de llegar a la entrada del duplicado -- si en la sesión real se
duplicó a mitad de camino y se siguió editando la fuente DESPUÉS, el
duplicado terminaba reflejando el estado FINAL de la fuente, no el que tenía
en el momento real de la duplicación (confirmado con una sesión real en la
Etapa 19: duplicar una placa plana y recién después volver a enrollarla).
Con los duplicados como step anidado, esto se resuelve solo: al llegar a ese
step en el orden real de la lista, se duplica con lo que la placa tenga HASTA
AHÍ, y se sigue procesando el resto de los steps de la fuente sin
interrupción — ni core.py ni recorder.py necesitan reordenar nada.

No sabe nada de Qt ni de main_window — solo junta datos. La Etapa 5 conecta
sus métodos a los puntos reales de la GUI; to_yaml()/save() (Etapa 6) vuelcan
to_dict() a un archivo YAML de verdad.
"""
import yaml


class SessionRecorder:
    def __init__(self):
        # Placas RAÍZ (creadas con 'create', nunca duplicadas) -- lo único
        # que se serializa como entrada de nivel superior en 'plates'.
        self._roots= {}            # nombre de placa raíz -> {"create": {...}, "steps": [...]}
        self._root_order= []       # orden de creación de las raíces

        # Todo nombre de placa conocido (raíz o duplicado) -> la lista de
        # Python EXACTA donde van sus futuros steps. Para una raíz, es
        # self._roots[name]["steps"] (la misma lista, por referencia). Para
        # un duplicado, es la lista "steps" ANIDADA dentro del step
        # {"type":"duplicate", ...} que vive en los steps de SU fuente --
        # apendear ahí, en el lugar exacto donde se creó, es lo que resuelve
        # la Etapa 24 (no hace falta ningún reordenamiento después: como es
        # la MISMA lista por referencia, ya queda en su posición correcta).
        self._step_lists= {}
        self._all_names_order= []  # orden de alta real (raíces Y duplicados mezclados)

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
        if name in self._step_lists:
            raise ValueError(f"Plate name already recorded: {name!r}")
        return name

    def record_plate_created(self, create_params, name=None):
        """create_params: dict con width/height/factor/center/periodic_boundary_x/y
        (Å para width/height/center, igual que el resto del schema). Devuelve el
        nombre asignado a la placa (autogenerado si no se pasó uno)."""
        name= self._register_name(name)
        steps= []
        self._roots[name]= {"create": dict(create_params), "steps": steps}
        self._root_order.append(name)
        self._step_lists[name]= steps
        self._all_names_order.append(name)
        self._mark_modified()
        return name

    def _collect_nested_duplicate_names(self, steps):
        """Nombres de TODOS los duplicados anidados en esta lista de steps,
        recursivo (duplicados de duplicados incluidos) -- usado por
        remove_plate para limpiar el bookkeeping de todo el subárbol que
        se va con la placa borrada."""
        names= []
        for step in steps:
            if step.get("type") == "duplicate":
                names.append(step["name"])
                names.extend(self._collect_nested_duplicate_names(step.get("steps", [])))
        return names

    def remove_plate(self, plate_name):
        """Para cuando la GUI borra una placa (delete_actual_plate): la saca del
        recorder. Si es una RAÍZ, se saca de 'plates' directo. Si es un
        DUPLICADO, se busca y se saca el step 'duplicate' correspondiente de
        la lista de SU fuente (Etapa 24: ya no es una entrada de nivel
        superior). En cualquiera de los dos casos, CUALQUIER duplicado anidado
        dentro de la placa borrada se va con ella -- ya no puede quedar una
        referencia colgando (a diferencia del schema viejo, donde
        duplicate_of apuntaba por nombre y sí podía quedar sin resolver a
        propósito, fallando recién en el replay). Acá el subárbol completo
        se limpia del bookkeeping (known_plates/has_plate) en el momento,
        no solo se vuelve inalcanzable en el próximo to_dict()."""
        if plate_name not in self._step_lists:
            return

        if plate_name in self._roots:
            removed_steps= self._roots[plate_name]["steps"]
            del self._roots[plate_name]
            self._root_order.remove(plate_name)
        else:
            removed_steps= []
            for steps in self._step_lists.values():
                for i, step in enumerate(steps):
                    if step.get("type") == "duplicate" and step.get("name") == plate_name:
                        removed_steps= step.get("steps", [])
                        del steps[i]
                        break
                else:
                    continue
                break

        for name in [plate_name] + self._collect_nested_duplicate_names(removed_steps):
            self._step_lists.pop(name, None)
            if name in self._all_names_order:
                self._all_names_order.remove(name)
        self._mark_modified()

    def known_plates(self):
        return list(self._all_names_order)

    def has_plate(self, name):
        return name in self._step_lists

    def _steps_for(self, plate_name):
        if plate_name not in self._step_lists:
            raise ValueError(f"Unknown plate: {plate_name!r} (¿se registró con record_plate_created o record_duplicate?)")
        self._mark_modified()
        return self._step_lists[plate_name]

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
    # Duplicados (Etapa 24: step anidado, no entrada de nivel superior)
    # ================================

    def record_duplicate(self, source_plate_name, translation, absolute=False, name=None):
        """Etapa 24: el duplicado se registra como un step {"type":"duplicate",...}
        DENTRO de los steps de source_plate_name, en la posición exacta donde se
        llama esto -- no como una entrada aparte de nivel superior. Así el replay
        (core.build_session_from_config) lo procesa exactamente en el punto
        cronológico real, sin importar qué más se le siga haciendo a la fuente
        después. El duplicado tiene su PROPIA lista de steps anidada (puede
        seguir editándose, Etapa 11), y a su vez puede tener sus propios
        duplicados anidados más profundo, recursivamente.
        'source_plate_name' tiene que ser una placa ya registrada (con
        record_plate_created o record_duplicate). Devuelve el nombre asignado
        al duplicado."""
        if source_plate_name not in self._step_lists:
            raise ValueError(f"Unknown source plate: {source_plate_name!r}")
        name= self._register_name(name)
        nested_steps= []
        duplicate_step= {
            "type": "duplicate", "name": name,
            "translation": list(translation), "absolute": absolute,
            "steps": nested_steps,
        }
        self._step_lists[source_plate_name].append(duplicate_step)
        self._step_lists[name]= nested_steps
        self._all_names_order.append(name)
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
        return not self._root_order

    def to_dict(self, export_formats=None, output_dir=".", export_name="graphene"):
        """Arma el dict con el schema multi-placa (Etapa 24: 'plates' solo lleva
        las placas RAÍZ -- cada entrada tiene 'create' + 'steps', y los
        duplicados viven como steps {"type":"duplicate",...} anidados dentro
        de 'steps', en el punto exacto donde se duplicaron de verdad)."""
        return {
            "plates": [
                {"name": name, **self._roots[name]}
                for name in self._root_order
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
