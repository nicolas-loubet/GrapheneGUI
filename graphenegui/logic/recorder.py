import yaml


class SessionRecorder:
    def __init__(self):
        self._roots= {}            # nombre de placa raíz -> {"create": {...}, "steps": [...]}
        self._root_order= []       # orden de creación de las raíces

        self._step_lists= {}
        self._all_names_order= []  # orden de alta real (raíces Y duplicados mezclados)

        self._atom_types= []       # [{"name":..., "epsilon":..., "sigma":...}]
        self._next_plate_index= 0  # para autogenerar "plateN" si no se da nombre
        self._modified= False      # ¿hay cambios sin guardar?

    def _mark_modified(self):
        self._modified= True

    def is_modified(self):
        return self._modified

    def mark_saved(self):
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
        self._steps_for(plate_name).append({
            "type": "oxidation", "mode": "soft",
            "expression": expression, "fraction": fraction,
            "prob_oh": prob_oh, "z_mode": z_mode,
        })

    def record_oxidation_hard(self, plate_name, oxide_atoms):
        self._steps_for(plate_name).append({
            "type": "oxidation", "mode": "hard",
            "oxides": [list(atom) for atom in oxide_atoms],
        })

    def record_oxidation_removed(self, plate_name, oxide_atom):
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

    def record_carbon_type(self, plate_name, carbons, new_type):
        self._steps_for(plate_name).append({
            "type": "set_carbon_type", "carbon_type": new_type,
            "carbons": [list(c) for c in carbons],
        })

    def record_duplicate(self, source_plate_name, translation, absolute=False, name=None):
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
