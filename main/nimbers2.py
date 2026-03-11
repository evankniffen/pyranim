"""
nimbers2.py

Another attempt to compute the (correct) nimbers 
"""
import numpy as np
from dyckPaths import (
    board_to_dyck_word,
    dyck_word_to_parentheses,
    dyck_word_to_UD,
)

# Global parameter on whether moves should be checked for size, legality
# each time they are initialized
CHECK = (True, True)
# Global parameter on pyramid size (tested at 3)
N_TIERS = 3


def bitmap_to_dyck_word(bitmap):
    """
    Convert a legal pyramid bitmap (numpy bool array of shape (n,n))
    into a Dyck word as a list of 1/0, using the same convention as
    board_to_dyck_word:
        1 = U
        0 = D

    The output has length 2*(n+1).
    """
    bitmap = np.asarray(bitmap, dtype=bool)

    if bitmap.ndim != 2 or bitmap.shape[0] != bitmap.shape[1]:
        raise ValueError("bitmap must be a square numpy array of shape (n_tiers, n_tiers)")

    n = bitmap.shape[0]
    if n == 0:
        return []

    chips = {}
    for row in range(n):
        for col in range(n - row):
            chips[(row, col)] = {
                "row": row,
                "col": col,
                "present": bool(bitmap[row, col]),
            }

    return board_to_dyck_word(chips, n)

class state:
    # TODO: revise bitmap to grow an envelope to avoid if else statements
    #       that may be significantly slowing down computation
    """
    A class to describe the state in an n-tier game as a bitmap

    Parameters
    ------------
    n_tier: int
        number of pyramid tiers in the game in which this state resides
    bitmap: numpy bool array (n_tier, n_tier)
        the state's bitmap as a numpy array
        row (i): pyramid row, bottom to up
        column (j): pyramid column, left to right
    check: (bool, bool)
        decides whether to check for size and legality respectively

        
    Attributes
    ------------
    UD: string
        the state's dyck word as U/D size 2*(n_tier + 1)
    n_chips: int
        the number of chips this state has
    next: list (of bitmap)
        list of all possible next states as bitmaps
    next_UD: list (of strings)
        list of all possible next states as Dyck words U/D
    nimber: unsigned int
        computed nimber

    """

    def __init__(self, bitmap, n_tiers=N_TIERS, check=CHECK):
        self.n_tiers = n_tiers
        self.bitmap = bitmap
        self.dyck = dyck_word_to_UD(bitmap_to_dyck_word(bitmap))
        self.n_chips = np.sum(bitmap)
        self.next = []
        self.next_UD = []

        if CHECK[0]:
            if not self.check():
                raise TypeError("Wrong syntax state initialized in state.__init__")
        if CHECK[1]:
            if not self.is_legal():
                raise TypeError("Illegal state initialized in state.__init__")
        


    def check(self) -> bool:
        """
        Returns whether bitmap matches size
        (note: DOES NOT check whether the state is legal)
        """
        if self.bitmap.shape != (self.n_tiers, self.n_tiers):
            return False
        if (self.bitmap.dtype != np.bool_):
            return False
        
        
        for row in range(1, self.n_tiers):
            for col in range(self.n_tiers - row, self.n_tiers):
                #print(row, col, self.bitmap[row][col])
                if (self.bitmap[row][col]):
                    return False
        
        # (passing the vibe check)
        return True

    def is_legal(self) -> bool:
        """ Checks the legality of this state """

        for row in range(self.n_tiers):
            for col in range(self.n_tiers - row):
                if (self.num_above(row, col) > 0) & (not self.bitmap[row][col]):
                    return False

        # (yup, she's legal)
        return True
        

    def print(self):
        """
        Prints the state, why not lmao
        TODO: make it also print the nim
        """

        print(self.dyck)

        print('*' * (2* self.n_tiers + 3))

        for i in range(self.n_tiers):
            row = self.n_tiers - i - 1
            print('* ', end='')
            print(' '*row, end='')
            for col in range(self.n_tiers - row):
                if (self.bitmap[row][col]):
                    print('0', end=' ')
                else:
                    print('-', end=' ')
            print(' '*row, end='*\n')

        print('*' * (2* self.n_tiers + 3))


    def above(self, row, col):
        """ Returns indices (row, col) of above given stone as a tuple"""
        if (row == self.n_tiers - 1):
            return np.array((), ndmin=1)
        if (col == 0):
            return np.array((self.bitmap[row+1][col]), ndmin=1)
        return np.array((self.bitmap[row+1][col], self.bitmap[row+1][col-1]), ndmin=1)
    
    def num_above(self, row, col):
        """ Returns number of stones above given stone """
        return np.sum(self.above(row, col))
    

    def remove(self, row, col, bitmap):
        """
        Attempts to remove the stone for the bitmap given
        Throws an IndexError for illegal removals
        This algorithm works recursively and needs the original bitmap
        """
        above = self.above(row, col)
        num_above = np.sum(above)

        if (num_above == 2) | (not bitmap[row][col]): # stop that chud
            error = "Illegal removal at ("+str(row)+","+str(col)+")"
            raise IndexError(error)

        # otherwise
        bitmap_copy = np.copy(bitmap)

        r = row
        c = col
        while r < self.n_tiers:
            bitmap_copy[r][c] = False
            r += 1
        
        r = row + 1
        c = col - 1
        while (r < self.n_tiers) & (c >= 0):
            #print(r, c)
            bitmap_copy[r][c] = False
            r += 1
            c -= 1

        return bitmap_copy
        
    
    def find_next(self):
        """
        Gives a list of all possible next states, as bitmaps
        """

        self.next = []

        for row in range(self.n_tiers):
            for col in range(self.n_tiers - row):
                try: # Can I remove it?
                    removed = self.remove(row, col, self.bitmap)
                    self.next.append(removed)
                except: # can't (womp womp)
                    continue

        self.next_UD = [dyck_word_to_UD(bitmap_to_dyck_word(bitmap)) for bitmap in self.next]
    
    def print_next(self):
        print("-"*10)
        print(len(self.next), "found next")
        print("-"*10)

        for bitmap in self.next:
            newstate = state(bitmap, n_tiers=self.n_tiers)
            newstate.print()


    def find_nimber(self) -> int:
        # TODO: finish nimber computation functionality
        self.nimber = 0
        return self.nimber


##############################################################################
# Testing initializations
"""
example1 = np.array(((True, True, True), (True, False, False), (False, False, False)))
example2 = np.array(((True, False, True), (False, True, False), (True, False, False)))
example3 = np.array(((True, True, True), (True, True, True), (True, True, True)))
example4 = example1

state1 = state(example1)
state1.print()
#state2 = state(example2)
#state2.print()
# (will throw an illegal state error)
#state3 = state(example3)
# (will throw an improper state error)
#state4 = state(example4, n_tiers=2)
# (will throw a size error)
"""

# Testing removals
"""
big = np.array(((True, True, True), (True, True, False), (True, False, False)))
mystate = state(big)
mystate.print()
cut = mystate.remove(1, 0, mystate.bitmap)
cutstate = state(cut)
cutstate.print()
cut2 = cutstate.remove(0, 1, cutstate.bitmap)
cutstate2 = state(cut2)
cutstate2.print()
#bad = mystate.remove(0, 1, mystate.bitmap)
#mystate.print()
# throws an error for illegal removal (tried to remove an inner)
womp = mystate.remove(0, 2, mystate.bitmap)
#print(womp)
wompstate = state(womp)
wompstate.print()
"""

# Testing next
"""
big = np.array(((True, True, True), (True, True, False), (True, False, False)))
bigstate = state(big)
bigstate.find_next()
bigstate.print_next()

medium = np.array(((True, True, True), (True, False, False), (False, False, False)))
mediumstate = state(medium)
mediumstate.find_next()
mediumstate.print_next()

small = np.array(((False, True, False), (False, False, False), (False, False, False)))
smallstate = state(small)
smallstate.find_next()
smallstate.print_next()

big = np.array(((True, True, True, True), (True, True, True, False), (True, True, False, False), (True, False, False, False)))
bigstate = state(big, n_tiers=4)
bigstate.find_next()
bigstate.print_next()
print(bigstate.next_UD)
"""
##############################################################################


class game:
    """
    A class to describe the state in an n-tier game as a bitmap

    Parameters
    ------------
    n_tier: int
        number of pyramid tiers in the game
        
    Attributes
    ------------
    states: dict (of dicts)
        key: ndarray
            dyck word
        value: dict
            "state": (state)
                state object of bitmap
            "next?": (bool)
                does this state have the next values found?
            "nim?": (bool)
                does this state have its nim value found?
            "n_chips": (int)
                number of chips in this state, used for ranking

    """

    def __init__(self, n_tiers=N_TIERS):
        self.n_tiers = n_tiers
        self.states = {}
    
    def load(self, default_load=True, bitmap=np.empty(shape=(1, 1), dtype=bool)):
        """
        Loads the dictionary with its first, maximum-element state.
        If left on default, will go with P_n, the n-pyramid.
        If not left on default, must provide a proper n-game bitmap.
        """
        if default_load:
            bitmap=np.empty(shape=(self.n_tiers, self.n_tiers), dtype=bool)

            for row in range(self.n_tiers):
                for col in range(self.n_tiers - row):
                    bitmap[row][col] = True
                for col in range(self.n_tiers - row, self.n_tiers):
                    bitmap[row][col] = False
            
        if dyck_word_to_UD(bitmap_to_dyck_word(bitmap)) in self.states.keys(): # already loaded this state
            return

        self.states[dyck_word_to_UD(bitmap_to_dyck_word(bitmap))] = {"state": state(bitmap, n_tiers=self.n_tiers), "next?": False, "nim?": False, "n_chips": np.sum(bitmap)}

    def print(self):
        """
        Shows the contents currently produced in the game
        """
        for value in self.states.values():
            print('-'*10)
            value["state"].print()
            print(value["state"].next_UD)
            print(value["next?"], value["nim?"], value["n_chips"])


    def update_next(self, UD):
        """
        Updates the selected states to find every possible next state
        and appends those new states to the dictionary.
        """
        if self.states[UD]["next?"]: # already updated
            return
        self.states[UD]["state"].find_next()

        for i in range(len(self.states[UD]["state"].next)):
            if self.states[UD]["state"].next_UD[i] not in self.states.keys():
                self.states[self.states[UD]["state"].next_UD[i]] = {"state": state(self.states[UD]["state"].next[i], n_tiers=self.n_tiers), "next?": False, "nim?": False}
                self.states[self.states[UD]["state"].next_UD[i]]["n_chips"] = self.states[self.states[UD]["state"].next_UD[i]]["state"].n_chips

        self.states[UD]["next?"] = True


##############################################################################
# Testing initializations

five_game = game(5)
five_game.load()
five_game.print()
print("\n\n\n\n\n\n")
five_game.update_next("UUUUUUDDDDDD")
five_game.print()

print("\n\n\n\n\n\n")
four_game = game(4)
first = np.array(((True, True, True, True), (False, True, False, False), (False, False, False, False), (False, False, False, False)))
four_game.load(default_load=False, bitmap=first)
four_game.print()
print("\n\n\n\n\n\n")
four_game.update_next("UUDUUDDUDD")
four_game.print()
print("\n\n\n\n\n\n")
#print(tuple(first))
