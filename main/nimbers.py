# nimbers.py
#
# Nimber arithmetic and Sprague–Grundy values for the Pyranim game.
#
# The game:
#   - n-tier chip pyramid, rows indexed from bottom: row = 0,...,n-1,
#     with row r having (n - r) chips at columns col = 0,...,n-r-1.
#   - A move: choose a "visible" chip (bird's-eye view) and remove it
#     along with all chips "above" it (anything that depends on it via
#     support). Remaining chips form the new position. Last move wins.
#
# This file provides:
#   - nim arithmetic: nimsum, nimprod
#   - class PyramidNimberCalculator(n_tiers) with methods:
#       * grundy(state): Sprague–Grundy number for bitmask state
#       * full_state(): bitmask for full n-tier pyramid
#       * grundy_full(): nimber of the full starting position
#       * state_from_gui_chips(chips_dict): convert game.py's chips dict to state
#       * nimber_from_gui_chips(chips_dict): convenience wrapper


# ==============================
#      NIM ARITHMETIC
# ==============================

# https://rosettacode.org/wiki/Nimber_arithmetic#Python

# Highest power of two that divides a given number.
def hpo2(n):
    return n & (-n)


# Base 2 logarithm of the highest power of 2 dividing a given number.
def lhpo2(n):
    q = 0
    m = hpo2(n)
    while m % 2 == 0:
        m = m >> 1
        q += 1
    return q


def nimsum(x, y):
    """Nim-sum (xor)."""
    return x ^ y


def nimprod(x, y):
    """Nim-product of two nimbers."""
    if x < 2 or y < 2:
        return x * y
    h = hpo2(x)
    if x > h:
        # break x into powers of 2
        return nimprod(h, y) ^ nimprod(x ^ h, y)
    if hpo2(y) < y:
        # break y into powers of 2 by flipping operands
        return nimprod(y, x)
    xp, yp = lhpo2(x), lhpo2(y)
    comp = xp & yp
    if comp == 0:
        # no Fermat power in common
        return x * y
    h = hpo2(comp)
    # a Fermat number square is its sequimultiple
    return nimprod(nimprod(x >> h, y >> h), 3 << (h - 1))


# ==============================
#   PYRAMID GAME NIMBER LOGIC
# ==============================

class PyramidNimberCalculator:
    """
    Compute Sprague–Grundy numbers (nimbers) for the n-tier Pyranim game.

    Representation:
      - Each chip is assigned an integer ID 0..(num_chips-1).
      - A game state is an integer bitmask: bit i = 1 iff chip i is present.
      - We precompute:
          * the "above" relation (which chips a given chip supports),
          * for each chip i, the "cone" of chips that get removed if we play i
            (itself and all chips reachable above it),
          * the "x_index" used for the bird's-eye visibility rule:
                x_index = 2*col + row,
            so chips sharing x_index lie in the same vertical column when viewed
            from above; visible chips are those with maximal row for each x_index.
    """

    def __init__(self, n_tiers: int):
        if n_tiers <= 0:
            raise ValueError("Number of tiers must be positive.")
        self.n = n_tiers
        self.num_chips = self.n * (self.n + 1) // 2

        # Map (row, col) -> id
        # Row 0 = bottom, row n-1 = top
        self.id_of = []
        self.chips = []  # list of (row, col, x_index) per chip id
        idx = 0
        for row in range(self.n):
            row_len = self.n - row
            row_ids = []
            for col in range(row_len):
                row_ids.append(idx)
                x_index = 2 * col + row  # combinatorial version of horizontal position
                self.chips.append((row, col, x_index))
                idx += 1
            self.id_of.append(row_ids)

        # above[i] = list of chip IDs directly above chip i (supported by i)
        self.above = [[] for _ in range(self.num_chips)]
        self._build_above_relations()

        # cone_mask[i] = bitmask of chip i and all chips above it (its upper cone)
        self.cone_mask = [0] * self.num_chips
        self._build_cone_masks()

        # Memoization for Grundy numbers
        self._grundy_cache = {0: 0}  # empty position has nimber 0

    # ---------- structure building ----------

    def _build_above_relations(self):
        """
        For each chip at (row, col), we find chips "above" it.
        From the GUI support logic:

          A chip at (row, col) with row > 0 is supported by
            (row-1, col) and (row-1, col+1), if those exist.

        Inverting this: a chip at (row, col) supports chips at
          (row+1, col) and (row+1, col-1), when those exist
          within the triangular shape.
        """
        for row in range(self.n):
            row_len = self.n - row
            for col in range(row_len):
                i = self.id_of[row][col]
                row_above = row + 1
                if row_above >= self.n:
                    continue
                # candidates above: (row+1, col) and (row+1, col-1)
                for col_above in (col, col - 1):
                    if 0 <= col_above < (self.n - row_above):
                        j = self.id_of[row_above][col_above]
                        self.above[i].append(j)

    def _build_cone_masks(self):
        """
        Precompute, for each chip i, the bitmask of i + all chips reachable
        above it (its "upper cone" in the support DAG). When we play chip i
        in a given state, the chips actually removed are:
            removed = state & cone_mask[i]
        """
        for i in range(self.num_chips):
            mask = 0
            stack = [i]
            visited = set()
            while stack:
                k = stack.pop()
                if k in visited:
                    continue
                visited.add(k)
                mask |= (1 << k)
                for j in self.above[k]:
                    stack.append(j)
            self.cone_mask[i] = mask

    # ---------- state helpers ----------

    def full_state(self) -> int:
        """Bitmask representing the full n-tier pyramid (all chips present)."""
        return (1 << self.num_chips) - 1

    def visible_moves(self, state: int):
        """
        Return list of chip IDs that are 'visible' from above in the given state.

        Visibility rule (matches the GUI logic combinatorially):
          - Each chip has an x_index = 2*col + row.
          - For each x_index, the visible chip is the one with maximal row
            among those present in the state.
        """
        best_for_x = {}  # x_index -> (row, chip_id)
        for chip_id in range(self.num_chips):
            if not (state & (1 << chip_id)):
                continue
            row, col, x_index = self.chips[chip_id]
            prev = best_for_x.get(x_index)
            if prev is None or row > prev[0]:
                best_for_x[x_index] = (row, chip_id)

        return [chip_id for (_, chip_id) in best_for_x.values()]

    # ---------- Grundy computation ----------

    def grundy(self, state: int) -> int:
        """
        Compute the Sprague–Grundy number (nimber) of a given state (bitmask),
        using memoized recursion.

        G(state) = mex{ G(next_state) : next_state reachable by one move }.

        A move is: choose a visible chip i, remove it and all chips above it
        (cone), producing:
            next_state = state & ~cone_mask[i]
        """
        if state in self._grundy_cache:
            return self._grundy_cache[state]

        moves = self.visible_moves(state)
        child_grundies = set()

        for chip_id in moves:
            removed_mask = self.cone_mask[chip_id]
            next_state = state & ~removed_mask
            g_next = self.grundy(next_state)
            child_grundies.add(g_next)

        # mex: minimum nonnegative integer not in child_grundies
        g = 0
        while g in child_grundies:
            g += 1

        self._grundy_cache[state] = g
        return g

    def grundy_full(self) -> int:
        """Sprague–Grundy number of the full starting n-tier pyramid."""
        return self.grundy(self.full_state())

    # ---------- GUI integration helpers ----------
    
    def state_from_gui_chips(self, chips_dict) -> int:
        """
        Convert the game.py GUI 'chips' dict to a bitmask state.

        chips_dict is expected to be:
          {(row, col): {"row": row, "col": col, "present": bool, ...}, ...}
        with row, col as in game.py:
          - row: 0 (bottom) .. n-1 (top)
          - col: 0..(n-row-1)
        """
        state = 0
        for (row, col), chip in chips_dict.items():
            if not chip.get("present", False):
                continue
            chip_id = self.id_of[row][col]
            state |= (1 << chip_id)
        return state

    def nimber_from_gui_chips(self, chips_dict) -> int:
        """
        Convenience: directly compute nimber of current GUI position.
        """
        state = self.state_from_gui_chips(chips_dict)
        return self.grundy(state)


if __name__ == "__main__":
    # Small sanity checks / demo
    for n in range(1, 6):
        calc = PyramidNimberCalculator(n)
        g = calc.grundy_full()
        print(f"n = {n} tiers, num_chips = {calc.num_chips}, Grundy(full) = {g}")

    # for f, op in ((nimsum, '+'), (nimprod, '*')):
    #     print(f" {op} |", end='')
    #     for i in range(16):
    #         print(f"{i:3d}", end='')
    #     print("\n--- " + "-"*48)
    #     for i in range(16):
    #         print(f"{i:2d} |", end='')
    #         for j in range(16):
    #             print(f"{f(i,j):3d}", end='')
    #         print()
    #     print()