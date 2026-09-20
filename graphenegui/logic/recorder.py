import copy
from contextlib import contextmanager

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

        self._undo_stack= []
        self._redo_stack= []
        self._batch_depth= 0
        self._batch_has_checkpoint= False

    def _mark_modified(self):
        self._modified= True

    def is_modified(self):
        return self._modified

    def mark_saved(self):
        self._modified= False

    # ================================
    # Undo / Redo
    # ================================

    def _capture_snapshot(self):
        return {
            "roots": copy.deepcopy(self._roots),
            "root_order": list(self._root_order),
            "all_names_order": list(self._all_names_order),
            "atom_types": copy.deepcopy(self._atom_types),
            "next_plate_index": self._next_plate_index,
        }

    def _index_step_lists(self):
        index= {}

        def walk(name, steps):
            index[name]= steps
            for step in steps:
                if step.get("type") == "duplicate":
                    walk(step["name"], step["steps"])

        for name, root in self._roots.items():
            walk(name, root["steps"])
        return index

    def _apply_snapshot(self, snapshot):
        self._roots= snapshot["roots"]
        self._root_order= snapshot["root_order"]
        self._all_names_order= snapshot["all_names_order"]
        self._atom_types= snapshot["atom_types"]
        self._next_plate_index= snapshot["next_plate_index"]
        self._step_lists= self._index_step_lists()

    def _checkpoint(self):
        if self._batch_depth > 0:
            if self._batch_has_checkpoint:
                return
            self._batch_has_checkpoint= True
        self._undo_stack.append(self._capture_snapshot())
        self._redo_stack.clear()

    def begin_action(self):
        self._batch_depth+= 1

    def end_action(self):
        self._batch_depth= max(0, self._batch_depth - 1)
        if self._batch_depth == 0:
            self._batch_has_checkpoint= False

    @contextmanager
    def batch_action(self):
        self.begin_action()
        try:
            yield
        finally:
            self.end_action()

    def can_undo(self):
        return bool(self._undo_stack)

    def can_redo(self):
        return bool(self._redo_stack)

    def undo(self):
        if not self._undo_stack:
            return False
        self._redo_stack.append(self._capture_snapshot())
        self._apply_snapshot(self._undo_stack.pop())
        self._mark_modified()
        return True

    def redo(self):
        if not self._redo_stack:
            return False
        self._undo_stack.append(self._capture_snapshot())
        self._apply_snapshot(self._redo_stack.pop())
        self._mark_modified()
        return True

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
        self._checkpoint()  # Etapa 27: antes de _register_name, que ya muta _next_plate_index
        name= self._register_name(name)
        steps= []
        self._roots[name]= {"create": dict(create_params), "steps": steps}
        self._root_order.append(name)
        self._step_lists[name]= steps
        self._all_names_order.append(name)
        self._mark_modified()
        return name

    def _collect_nested_duplicate_names(self, steps):
        names= []
        for step in steps:
            if step.get("type") == "duplicate":
                names.append(step["name"])
                names.extend(self._collect_nested_duplicate_names(step.get("steps", [])))
        return names

    def remove_plate(self, plate_name):
        if plate_name not in self._step_lists:
            return
        self._checkpoint()

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

    def rename_plate(self, old_name, new_name):
        if old_name == new_name:
            return
        if old_name not in self._step_lists:
            raise ValueError(f"Unknown plate: {old_name!r}")

        if old_name in self._roots:
            self._roots[new_name]= self._roots.pop(old_name)
            self._root_order[self._root_order.index(old_name)]= new_name
        else:
            for steps in self._step_lists.values():
                for step in steps:
                    if step.get("type") == "duplicate" and step.get("name") == old_name:
                        step["name"]= new_name
                        break

        self._step_lists[new_name]= self._step_lists.pop(old_name)
        self._all_names_order[self._all_names_order.index(old_name)]= new_name

    def _steps_for(self, plate_name):
        if plate_name not in self._step_lists:
            raise ValueError(f"Unknown plate: {plate_name!r} (¿se registró con record_plate_created o record_duplicate?)")
        self._checkpoint()
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
        self._steps_for(plate_name).append({"type": "oxidation_cleared"})

    # ================================
    # reduce_borders y CNT
    # ================================

    def record_reduce_borders(self, plate_name):
        self._steps_for(plate_name).append({"type": "reduce_borders"})

    def record_cnt(self, plate_name, vector):
        self._steps_for(plate_name).append({"type": "cnt", "vector": list(vector)})

    def record_cnt_restored(self, plate_name):
        self._steps_for(plate_name).append({"type": "cnt_restored"})

    def record_carbon_type(self, plate_name, carbons, new_type):
        self._steps_for(plate_name).append({
            "type": "set_carbon_type", "carbon_type": new_type,
            "carbons": [list(c) for c in carbons],
        })

    def record_duplicate(self, source_plate_name, translation, absolute=False, name=None):
        if source_plate_name not in self._step_lists:
            raise ValueError(f"Unknown source plate: {source_plate_name!r}")
        self._checkpoint()
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
        self._checkpoint()  # Etapa 27
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
        data= self.to_dict(export_formats=export_formats, output_dir=output_dir, export_name=export_name)
        header= (
            "# Generado por \"Guardar trabajo\".\n"
            "# Reproducible con: graphene-gui-cli -c este_archivo.yaml\n"
        )
        return header + yaml.safe_dump(data, sort_keys=False, default_flow_style=False, allow_unicode=True)

    def save(self, file_path, export_formats=None, output_dir=".", export_name="graphene"):
        content= self.to_yaml(export_formats=export_formats, output_dir=output_dir, export_name=export_name)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path
