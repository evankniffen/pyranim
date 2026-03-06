# dyckPaths.py
#
# Dyck path helpers and the board -> Dyck word mapping
# using the bijection:
#   Φ: (r, p) ↦ (i = p, j = p + n - r + 1)
#
# where:
#   - n = number of tiers
#   - r = row index from TOP (1..n)
#   - p = position in that row (1..r)
#
# In the GUI, rows are indexed from the BOTTOM:
#   row = 0 (bottom), ..., n-1 (top)
#   col = 0..(n-row-1)
#
# Conversion:
#   r = n - row
#   p = col + 1
#   i = p
#   j = p + n - r + 1 = row + col + 2
#
# Then we shift to 0-based cell coords:
#   x = i - 1
#   y = j - 1
#
# Chips map to cells (x, y) with 0 <= x < y <= n.
# The filled region R is:
#   - all cells with y <= x (on or below diagonal),
#   - plus the chip cells (x, y) in T above diagonal.
# We take the upper-right outer boundary of R from (0,0) to (n+1, n+1).


def dyck_word_to_parentheses(dw):
    """
    Convert a Dyck word [1,1,0,0,...] to parentheses string like '(())'.
    1 = U (up), 0 = D (right).
    """
    return "".join("(" if step == 1 else ")" for step in dw)


def dyck_word_to_UD(dw):
    """
    Convert a Dyck word [1,1,0,0,...] to 'U'/'D' string like 'UUDDUD'.
    1 = U (north), 0 = D (east).
    """
    return "".join("U" if step == 1 else "D" for step in dw)


def board_to_dyck_word(chips, n_tiers):
    """
    Given the current board state (chips dict from game.py) and number of tiers,
    return a Dyck word as a list of 1s and 0s (1 = U, 0 = D) of length 2*(n+1),
    using the (n+1)x(n+1) square and the Φ bijection.

    chips: dict[(row, col)] -> {
        "row": int,    # 0 (bottom) .. n_tiers-1 (top)
        "col": int,    # 0..(n_tiers-row-1)
        "x": float,
        "y": float,
        "id": canvas_item_id,
        "present": bool,
    }

    Algorithm:
      1) Map each PRESENT chip (row, col) to a cell (x, y) in {0..n}^2:
           r = n - row
           p = col + 1
           i = p
           j = p + n - r + 1 = row + col + 2
           x = i - 1
           y = j - 1
         Keep only x < y (which always holds for valid chips).

      2) Define the filled region R via:
           is_filled(x, y) = (y <= x) OR ((x, y) in T)

      3) For each x in {0, ..., n}, compute the "height" H[x] as:
           H[x] = max_y + 1 over all filled cells (x, y) in this column,
                  then forced to be at least x to stay above the diagonal.

         Then append H[n+1] = n+1 to force the endpoint (n+1, n+1).

      4) Build a monotone path (Dyck path) from (0,0) to (n+1, n+1) that
         passes through these heights by greedily moving:
           - Up (U = 1) until hitting H[k],
           - Then Right (D = 0) to the next column.

         Finally ensure we end exactly at (n+1, n+1).
    """
    n = n_tiers
    if n <= 0:
        return []

    # 1) Collect present chips and map them to (x, y) cells in 0..n
    T = set()
    for (row, col), chip in chips.items():
        if not chip.get("present", False):
            continue

        # Convert GUI coords (bottom-based) to (r, p)
        r = n - row        # row index from TOP, 1..n
        p = col + 1        # position in row, 1..r

        i = p
        j = p + n - r + 1  # = row + col + 2

        x = i - 1          # 0..n
        y = j - 1          # 0..n

        # Should always have x < y for valid chips
        if 0 <= x <= n and 0 <= y <= n and x < y:
            T.add((x, y))

    # 2) Define filled region R
    def is_filled_cell(x, y):
        # base triangle: at or below diagonal
        if y <= x:
            return True
        # chip cells above diagonal
        return (x, y) in T

    # 3) Compute heights H[x] for x = 0..n, then append H[n+1] = n+1
    H = []
    for x in range(n + 1):
        max_y = -1
        for y in range(0, n + 1):
            if is_filled_cell(x, y):
                max_y = max(max_y, y + 1)  # top edge of the cell
        # make sure we stay at or above the diagonal y = x
        if max_y < x:
            max_y = x
        H.append(max_y)

    # Force the endpoint at (n+1, n+1)
    H.append(n + 1)

    # 4) Build the Dyck path from H
    dw = []
    x = 0
    y = 0

    # For each column 0..n: move up to H[k], then right to next column
    for k in range(n + 1):
        targetH = H[k]
        # move up
        while y < targetH:
            dw.append(1)  # U
            y += 1
        # move right to the next column
        if k < n + 1:
            dw.append(0)  # D
            x += 1

    # After processing columns, ensure we reach (n+1, n+1)
    while y < n + 1:
        dw.append(1)
        y += 1
    while x < n + 1:
        dw.append(0)
        x += 1

    return dw