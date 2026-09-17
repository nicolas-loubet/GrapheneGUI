class PlateEntry:
    __slots__= ("id", "plate", "duplicate_of", "translation")

    def __init__(self, id, plate, duplicate_of=None, translation=None):
        self.id= id
        self.plate= plate
        self.duplicate_of= duplicate_of  # id de la placa fuente, o None si no es duplicado
        self.translation= translation    # [dx,dy,dz] en nm, ya resuelta (ver core.compute_duplicate_translation)


class PlateRegistry:
    def __init__(self):
        self._entries= {}   # id -> PlateEntry
        self._order= []     # ids en el orden visible (coincide con main_window.ui.comboDrawings)
        self._next_id= 0

    # ================================
    # Alta / baja
    # ================================

    def add(self, plate, duplicate_of=None, translation=None):
        self._next_id+= 1
        id= f"plate{self._next_id}"
        self._entries[id]= PlateEntry(id, plate, duplicate_of, translation)
        self._order.append(id)
        return id

    def remove_at(self, position):
        id= self._order[position]
        del self._entries[id]
        self._order.remove(id)

    # ================================
    # Acceso tipo lista (drop-in para main_window.plates)
    # ================================

    def __len__(self):
        return len(self._order)

    def __getitem__(self, position):
        if isinstance(position, slice):
            return [self._entries[id].plate for id in self._order[position]]
        return self._entries[self._order[position]].plate

    def __iter__(self):
        for id in self._order:
            yield self._entries[id].plate

    # ================================
    # Identidad / proveniencia
    # ================================

    def id_at(self, position):
        return self._order[position]

    def position_of(self, id):
        return self._order.index(id)

    def entry_at(self, position):
        return self._entries[self._order[position]]

    # ================================
    # Duplicados: se deriva, no se trackea
    # ================================

    def resolve_duplicate_groups(self, atol=1e-6):
        duplicates, roots= [], []
        for id in self._order:
            root_id, cumulative_translation= self._resolve_chain_root(id, atol)
            if cumulative_translation is None: continue  # no es duplicado de nadie (o dejó de coincidir)
            duplicates.append(self.position_of(id) + 1)
            roots.append(self.position_of(root_id) + 1)
        return [duplicates, roots]

    def _resolve_chain_root(self, id, atol):
        entry= self._entries[id]
        if entry.duplicate_of is None:
            return id, None
        parent_entry= self._entries.get(entry.duplicate_of)
        if parent_entry is None:
            return id, None  # la fuente ya no existe
        if not self._match_modulo_translation(parent_entry.plate, entry.plate, entry.translation, atol):
            return id, None

        grand_root, grand_translation= self._resolve_chain_root(entry.duplicate_of, atol)
        if grand_translation is None:
            return grand_root, entry.translation
        cumulative= [entry.translation[i] + grand_translation[i] for i in range(3)]
        return grand_root, cumulative

    @staticmethod
    def _match_modulo_translation(source, candidate, translation, atol):
        dx, dy, dz= translation
        for getter in ("get_carbon_coords", "get_oxide_coords", "get_hydrogens_coords"):
            a, b= getattr(source, getter)(), getattr(candidate, getter)()
            if len(a) != len(b): return False
            for atom_a, atom_b in zip(a, b):
                if atom_a[3] != atom_b[3] or atom_a[6] != atom_b[6]: return False
                if abs((atom_a[0]+dx) - atom_b[0]) > atol: return False
                if abs((atom_a[1]+dy) - atom_b[1]) > atol: return False
                if abs((atom_a[2]+dz) - atom_b[2]) > atol: return False
        return True
