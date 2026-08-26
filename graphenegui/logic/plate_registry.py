"""
PlateRegistry: única fuente de verdad para "qué placas hay" (reemplaza
main_window.plates, una lista plana) y su proveniencia (si una es duplicado
de otra, y con qué traslación — reemplaza main_window.plates_corresponding_to_duplicates,
el bookkeeping paralelo por posición que fue la fuente de varios bugs).

Dos decisiones de diseño:

1. Las placas se identifican por un ID ESTABLE asignado al crearse (nunca se
   reusa, no cambia si se borran o reordenan otras placas). 'duplicate_of'
   referencia ese ID, no una posición — borrar una placa no necesita NINGUNA
   lógica de corrimiento de índices (la causa raíz del bug que arreglamos en
   core.manage_duplicates_for_deletion).

2. "¿Sigue esta placa siendo una copia idéntica de su fuente?" no se trackea
   con un flag que hay que invalidar a mano en cada punto de la GUI donde se
   edita una placa (esa invalidación manual, repartida en varios handlers
   distintos, era la fuente real de los bugs — nos olvidamos de 3 call sites
   de 7). En cambio, se DERIVA comparando los átomos reales al momento de
   exportar (resolve_duplicate_groups) — no hay nada que invalidar porque no
   hay estado que pueda quedar desincronizado.

Es "list-like" a propósito (soporta [], len(), iteración) para poder
reemplazar main_window.plates como un drop-in — Renderer, update_drawing_area,
etc. siguen funcionando sin cambios.
"""


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
        """Registra una placa nueva y devuelve su id estable."""
        self._next_id+= 1
        id= f"plate{self._next_id}"
        self._entries[id]= PlateEntry(id, plate, duplicate_of, translation)
        self._order.append(id)
        return id

    def remove_at(self, position):
        """Saca la placa en esa posición. Ningún corrimiento de índices hace falta:
        las referencias duplicate_of de las demás placas son por id, no por
        posición, así que siguen siendo válidas solas."""
        id= self._order[position]
        del self._entries[id]
        self._order.remove(id)

    # ================================
    # Acceso tipo lista (drop-in para main_window.plates)
    # ================================

    def __len__(self):
        return len(self._order)

    def __getitem__(self, position):
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
        """Compara cada placa marcada como duplicado contra su(s) fuente(s) —
        siguiendo la cadena completa si es un duplicado de un duplicado — y arma
        [[índices_duplicado],[índices_root]], el mismo formato 1-indexado que ya
        esperaba writeTOP. Se calcula fresco cada vez que se llama: si una placa
        se editó desde que se duplicó (ya no coincide con la fuente trasladada),
        queda afuera sola, sin que nadie tenga que avisarle a esta función."""
        duplicates, roots= [], []
        for id in self._order:
            root_id, cumulative_translation= self._resolve_chain_root(id, atol)
            if cumulative_translation is None: continue  # no es duplicado de nadie (o dejó de coincidir)
            duplicates.append(self.position_of(id) + 1)
            roots.append(self.position_of(root_id) + 1)
        return [duplicates, roots]

    def _resolve_chain_root(self, id, atol):
        """Sigue duplicate_of hacia atrás mientras cada eslabón siga coincidiendo
        con su padre (traducción acumulada incluida). Devuelve (root_id,
        traslación_acumulada) o (id, None) si esta placa no es -o dejó de ser-
        duplicado de nadie."""
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
