# permutations.py
#
# Convert Dyck paths to 132-avoiding permutations via the inverse
# of Krattenthaler's bijection Φ between 132-avoiding permutations
# and Dyck paths.  See:
#
#   C. Krattenthaler, "Permutations with Restricted Patterns and Dyck Paths",
#   Adv. Appl. Math. 27 (2001), 510–530.
#
# In that paper, Φ maps a 132-avoiding permutation π = π_1 ... π_n
# to a Dyck path by reading π left-to-right. For each π_j, let
#
#    h_j = # of elements in π_{j+1} ... π_n that are larger than π_j.
#
# Then we append as many up-steps as necessary, followed by a down-step
# from height h_j + 1 to h_j.  This produces a Dyck path from (0,0)
# to (2n,0) with n down-steps.
#
# Here we implement the inverse mapping: given a Dyck word (list of 1/0),
# we recover the 132-avoiding permutation π.


def dyck_word_to_132_avoiding_permutation(dw):
    """
    Given a Dyck word dw as a list of 1's and 0's (1 = up-step, 0 = down-step),
    return the unique 132-avoiding permutation π of {1,...,n} such that
    Krattenthaler's Φ(π) = Dyck path(dw).

    Parameters
    ----------
    dw : list[int]
        Dyck word, e.g. [1,1,0,1,0,0] for U U D U D D.

    Returns
    -------
    list[int]
        A permutation of [1, 2, ..., n] that is 132-avoiding.

    Raises
    ------
    ValueError
        If dw is not a valid Dyck word (height goes negative or does not end at 0),
        or if the derived code cannot be decoded to a permutation (which should
        not happen for a genuine Φ-image Dyck path).
    """

    if not dw:
        raise ValueError("Dyck word is empty; cannot construct a permutation.")

    # Basic Dyck path validity check: never go below 0, end at 0, #U == #D.
    height = 0
    ups = 0
    downs = 0
    for step in dw:
        if step == 1:
            height += 1
            ups += 1
        elif step == 0:
            height -= 1
            downs += 1
            if height < 0:
                raise ValueError("Invalid Dyck word: path goes below the x-axis.")
        else:
            raise ValueError("Dyck word must contain only 1 (U) and 0 (D).")

    if height != 0 or ups != downs:
        raise ValueError("Invalid Dyck word: path does not return to x-axis or #U != #D.")

    n = downs  # number of down-steps = length of permutation

    # Step 1: record the starting heights of each down-step
    # c_j = height just BEFORE the j-th down-step (this is h_j + 1 in the paper).
    c = []
    h = 0
    for step in dw:
        if step == 1:
            h += 1
        else:
            # down-step starting at height h, ending at h-1
            c.append(h)
            h -= 1

    if len(c) != n:
        raise ValueError("Internal inconsistency: number of down-steps mismatch.")

    # Step 2: convert heights c_j into Krattenthaler's h_j (# larger elements to the right)
    # and from there into a Lehmer code (numbers of smaller elements to the right).
    #
    # Recall:
    #   c_j = h_j + 1   (starting height of down-step)
    #   h_j = number of elements in π_{j+1}...π_n that are LARGER than π_j.
    #
    # For position j (0-based), there are n-1-j elements to the right.
    # Let ℓ_j = #smaller to the right. Then
    #
    #   h_j + ℓ_j = n - 1 - j
    #   ℓ_j = (n - 1 - j) - h_j = (n - 1 - j) - (c_j - 1) = n - j - c_j.
    #
    # The Lehmer code ℓ_j must satisfy 0 <= ℓ_j <= n-1-j.
    lehmer = []
    for j, cj in enumerate(c):
        h_j = cj - 1  # #larger to the right
        l_j = (n - 1 - j) - h_j  # #smaller to the right
        if l_j < 0 or l_j > (n - 1 - j):
            raise ValueError(
                f"Invalid Dyck path for Krattenthaler's bijection: "
                f"derived Lehmer code out of range at position {j}: {l_j}"
            )
        lehmer.append(l_j)

    # Step 3: decode Lehmer code to permutation
    #
    # Standard decoding: start with available = [1,2,...,n].
    # At position j, pick the (ℓ_j + 1)-th smallest remaining element.
    available = list(range(1, n + 1))
    permutation = []
    for j, code in enumerate(lehmer):
        if code < 0 or code >= len(available):
            raise ValueError(
                f"Invalid Lehmer code at position {j}: {code} (len(available)={len(available)})"
            )
        permutation.append(available.pop(code))

    return permutation


def format_permutation(perm):
    """
    Convenience formatter: turns [3,1,2] into '3 1 2'.
    """
    return " ".join(str(x) for x in perm)