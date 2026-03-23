"""
nimbers2.py

Another attempt to compute the (correct) nimbers 
"""
import numpy as np
import json
import time
import matplotlib.pyplot as plt
from dyckPaths import (
    board_to_dyck_word,
    UD_to_dyck_word,
    dyck_word_to_UD,
)

# Global parameter on whether moves should be checked for size, legality
# each time they are initialized
CHECK = (True, True)
# Global parameter on pyramid size (tested at 3)
N_TIERS = 3


def mex(values):
    """
    Return the minimum excluded nonnegative integer from a list
    of nonnegative integers.

    Runs in O(n) time and O(n) space.
    """
    #vals = list(values)
    n = len(values)
    seen = [False] * (n + 1)

    for x in values:
        if 0 <= x <= n:
            seen[x] = True

    for m, present in enumerate(seen):
        if not present:
            return m


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
            "nim": (int)
                nim value (none if not yet found)
            "n_chips": (int)
                number of chips in this state, used for ranking
    buckets: list of list
        bucket: list, with everything in the list as the same number of stones
            string, contains dyck path keys

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

        self.states[dyck_word_to_UD(bitmap_to_dyck_word(bitmap))] = {"state": state(bitmap, n_tiers=self.n_tiers), "next?": False, "nim": None, "n_chips": np.sum(bitmap)}

    def print(self):
        """
        Shows the contents currently produced in the game
        """
        print("number of states:", len(self.states))
        for value in self.states.values():
            print('-'*10)
            value["state"].print()
            print(value["state"].next_UD)
            print(value["next?"], value["n_chips"], "*"+str(value["nim"]))


    def update_next(self, UD):
        """
        Updates the selected states to find every possible next state
        and appends those new states to the dictionary.
        """
        if self.states[UD]["next?"]: # already updated
            return
        self.states[UD]["state"].find_next() # find the next ones

        for i in range(len(self.states[UD]["state"].next)): # add next ones to dict
            if self.states[UD]["state"].next_UD[i] not in self.states.keys():
                self.states[self.states[UD]["state"].next_UD[i]] = {"state": state(self.states[UD]["state"].next[i], n_tiers=self.n_tiers), "next?": False, "nim": None}
                self.states[self.states[UD]["state"].next_UD[i]]["n_chips"] = self.states[self.states[UD]["state"].next_UD[i]]["state"].n_chips

        self.states[UD]["next?"] = True

    def generate_all(self):
        """
        Updates every state to include all successors, if not already updated
        """
        # why isn't there do while loop here???
        # anyways at each stage we're just gonna update what we can
        # technically this should only take at most however many chips
        # the initial state had
        to_update = []

        for key, value in self.states.items():
            if not value["next?"]:
                to_update.append(key)
        
        for key in to_update:
            self.update_next(key)
        
        while to_update != []:
            to_update = []

            for key, value in self.states.items():
                if not value["next?"]:
                    to_update.append(key)
        
            for key in to_update:
                    self.update_next(key)
  
    def compute_nimber(self, UD):
        """
        Computes the nimber for given state
        """
        if self.states[UD]["nim"] != None: # already computed
            return self.states[UD]["nim"]
        if self.states[UD]["n_chips"] <= 2: # base cases
            self.states[UD]["nim"] = self.states[UD]["n_chips"] % 2
            return self.states[UD]["nim"]
        
        # otherwise, do the mex :sunglasses:

        #print("Doing mex on:")
        #self.states[UD]["state"].print()
        #print(self.states[UD]["state"].print_next())
        possibilities = [self.states[key]["nim"] for key in self.states[UD]["state"].next_UD]
        #print(possibilities)
        self.states[UD]["nim"] = mex(possibilities)
        return self.states[UD]["nim"]

    
    def compute_nimbers(self):
        """
        Computes every nimber
        """
        self.generate_all()

        # we'll partition our states into categories of the same number of chips
        self.buckets = {}
        for n_chips in range(0, self.n_tiers*(self.n_tiers + 1)//2 + 1):
            self.buckets[n_chips] = []
        for key, value in self.states.items():
            self.buckets[value["n_chips"]].append(key)
        
        #print(self.buckets)

        # compute for each category starting from the (literal) bottom
        for n_chips in range(0, self.n_tiers*(self.n_tiers + 1)//2 + 1):
            for key in self.buckets[n_chips]:
                self.compute_nimber(key)
            #self.print()
    
    def print_strategy(self, UD):
        """
        Prints the best strategy given a state
        """
        print("Current state:")
        self.states[UD]["state"].print()
        print(self.states[UD]["state"].next_UD)
        print(["*"+str(self.states[key]["nim"]) for key in self.states[UD]["state"].next_UD])

        print()

        if self.states[UD]["nim"] > 0: # you can win by moving to a *0
            print("First move WIN. Possible winning moves are:")
            for key in self.states[UD]["state"].next_UD:
                if self.states[key]["nim"] == 0:
                    self.states[key]["state"].print()
        else: # You can't win, but I'll recommend a maximal nim move
            maxnim = max([self.states[key]["nim"] for key in self.states[UD]["state"].next_UD])
            print("First move LOSE. I would recommend a maximum nim (*" + str(maxnim) + ") move:")
            for key in self.states[UD]["state"].next_UD:
                if self.states[key]["nim"] == maxnim:
                    self.states[key]["state"].print()

    def compute_isomorphism_types(self):
        """
        Computes an isomorphism-type label for every state.
        Two states are isomorphic iff they get the same iso label.
        """
        #self.generate_all()

        """
        max_chips = self.n_tiers * (self.n_tiers + 1) // 2
        self.buckets = {k: [] for k in range(max_chips + 1)}
        for key, value in self.states.items():
            self.buckets[value["n_chips"]].append(key)
        """

        # canonical tuple of child iso-labels -> canonical integer id
        self.iso_dict = {}
        next_iso_id = 0

        for n_chips in range(self.n_tiers * (self.n_tiers + 1) // 2 + 1):
            for key in self.buckets[n_chips]:
                children = self.states[key]["state"].next_UD

                # terminal state: empty tuple
                child_types = tuple(sorted(self.states[c]["iso"] for c in children)) if children else ()

                if child_types not in self.iso_dict:
                    self.iso_dict[child_types] = next_iso_id
                    next_iso_id += 1

                self.states[key]["iso"] = self.iso_dict[child_types]

    def print_isomorphisms(self, picture=True):
        """
        Returns a list indexed by the number of chips, of the number of isomorphic states
        and prints a graph of that 
        """
        # make the list
        isomorphism_by_n_chips = []
        for n_chips in range(self.n_tiers * (self.n_tiers + 1) // 2 + 1):
            classes = [self.states[key]["iso"] for key in self.buckets[n_chips]]
            isomorphism_by_n_chips.append(int(np.size(np.unique(classes))))
        
        if picture:
            # make a histogram of the list
            

            xs = list(range(self.n_tiers * (self.n_tiers + 1) // 2 + 1))
            plt.figure(figsize=(8, 5))
            plt.bar(xs, isomorphism_by_n_chips, width=0.8)
            plt.xlabel("Number of chips")
            plt.ylabel("Number of isomorphism classes")
            plt.title(f"Isomorphism classes by chip count (n_tiers={self.n_tiers})")
            plt.xticks(xs)
            plt.tight_layout()
            #plt.show()
            filename = f"{self.n_tiers}_isomorphisms.png"
            plt.savefig(filename, dpi=200)
            plt.close()

        return isomorphism_by_n_chips
    
    def export_to_json(self, filename="game_states.json"):
        """
        Prints all useful info to be able to reconstruct the dictionary in a different format
        for the actual game. In game runtime, gives the nim and n_chips value; if asked for best strategy,
        will instead use the bit map to make relevant state objects.
        Output looks like
        dict:
            key: (int)
                dyck word as int
            value: (int) 
                the nimber of this state
                
        """

        # copy relevant info
        copydict = {}
        for key, value in self.states.items():
            #copydict[key] = int(value["nim"])
            # Removed (too much storage)
            #   |
            #   v
            #copydict[key]["bitmap"] = value["state"].bitmap.astype(int).tolist()
            #copydict[key]["nim"] = int(value["nim"])
            #copydict[key]["n_chips"] = int(value["n_chips"])

            # THIS CODE BREAKS AT n_tiers=15
            # (and probably so will your computer's hard drive storage, no matter what I'll do, I'm pretty sure)

            newkey = 0
            dyck_word = UD_to_dyck_word(key)
            for i in range(len(dyck_word)):
                newkey += dyck_word[i] * (2**i)
            copydict[newkey] = int(value["nim"])
        
        # export
        with open(filename, "w") as f:
            json.dump(copydict, f, indent=2)

        return copydict
    
    def export_to_json_big(self, filename="game_states.json"):
        """
        Prints all useful info to be able to reconstruct the dictionary in a different format
        for the actual game. In game runtime, gives the nim and n_chips value; if asked for best strategy,
        will instead use the bit map to make relevant state objects.
        Output looks like
        dict:
            key: (string)
                dyck word, U/D
            value: (dict)
                key: (string) "bitmap"
                value: (ndarray) the bitmap as 0s and 1s

                key: (string) "nim"
                value: (int) the nimber of this state

                key: (string) "n_chips"
                value: (int) the number of chips in this state
                
        """

        # copy relevant info
        copydict = {}
        for key, value in self.states.items():
            copydict[key] = {}
            # Removed (too much storage)
            #   |
            #   v
            copydict[key]["bitmap"] = value["state"].bitmap.astype(int).tolist()
            copydict[key]["nim"] = int(value["nim"])
            copydict[key]["n_chips"] = int(value["n_chips"])

        
        # export
        with open(filename, "w") as f:
            json.dump(copydict, f, indent=2)

        return copydict
    
    def export_to_json_iso(self, filename="game_states_iso.json"):
        """
        Prints all useful info to be able to reconstruct the iso dictionary in a different format
        for the actual game. In game runtime, gives the isomorphism class.
        Output looks like
        dict:
            key: (int)
                dyck word as int
            value: (int) 
                the isomorphism class of this state
                
        """

        # copy relevant info
        copydict = {}
        for key, value in self.states.items():
            #copydict[key] = int(value["nim"])
            # Removed (too much storage)
            #   |
            #   v
            #copydict[key]["bitmap"] = value["state"].bitmap.astype(int).tolist()
            #copydict[key]["nim"] = int(value["nim"])
            #copydict[key]["n_chips"] = int(value["n_chips"])

            # THIS CODE BREAKS AT n_tiers=15
            # (and probably so will your computer's hard drive storage, no matter what I'll do, I'm pretty sure)

            newkey = 0
            dyck_word = UD_to_dyck_word(key)
            for i in range(len(dyck_word)):
                newkey += dyck_word[i] * (2**i)
            copydict[newkey] = int(value["iso"])
        
        # export
        with open(filename, "w") as f:
            json.dump(copydict, f, indent=2)

        return copydict

    def export_stats(self, filename="game_statistics.json"):
        """
        Gives info to generate a final txt file with game data per n_tier
        """
        to_export = {}

        biggestdyck = "U"*(n+1) + "D"*(n+1)
        final = mygame.states[biggestdyck]["nim"]
        to_export["nimber:"] = int(final)

        isomorphisms = self.print_isomorphisms(picture=True)
        to_export["K:"] = int(np.sum(isomorphisms))
        to_export["M:"] = int(np.max(isomorphisms))
        to_export["isomorphism_by_n_chips:"] = isomorphisms

        return to_export



##############################################################################
# Testing initializations
"""
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
"""

##############################################################################
# Testing dictionary generation
"""
five_game = game(5)
five_game.load()
five_game.generate_all()
print("done")
print("number of states:", len(five_game.states))

three_game = game(3)
three_game.load()
three_game.generate_all()
three_game.print()
"""

##############################################################################
# Testing nimber computation
"""
three_game = game(3)
three_game.load()
three_game.compute_nimbers()
three_game.print()

five_game = game(5)
five_game.load()
five_game.compute_nimbers()
five_game.print()

print("\n\n\n\n\n\n\n\n")
five_game.print_strategy("UUUUUUDDDDDD")

print("\n\n\n\n\n\n\n\n")
five_game.print_strategy("UUDUDUDDUDUD")

print("\n\n\n\n\n\n\n\n")
five_game.print_strategy("UUUUDDDUDDUD")

print("\n\n\n\n\n\n\n\n")
one_game = game(1)
one_game.load()
one_game.compute_nimbers()
one_game.print()
"""

##############################################################################
# Testing exports
"""
five_game = game(5)
five_game.load()
five_game.compute_nimbers()
five_game.export_to_json(filename="5_game_states.json")

first = np.array(((True, True, True, True), (False, True, False, False), (False, False, False, False), (False, False, False, False)))
print(first.astype(int).tolist())
print(type(np.array(first.astype(int).tolist()).astype(bool)))
print(np.array(first.astype(int).tolist()).astype(bool))
"""

##############################################################################
# Exporting final data
time_taken = []
time_taken_iso = []

games = {}

for n in range(1,11): # n is the number of tiers!
    start = time.time() # Timing each one

    mygame = game(n)
    mygame.load()
    mygame.compute_nimbers()

    end = time.time() # stop time before export

    biggestdyck = "U"*(n+1) + "D"*(n+1)
    final = mygame.states[biggestdyck]["nim"]
    mygame.export_to_json(filename=str(n)+"_game_states.json")
    #mygame.export_to_json_big(filename=str(n)+"_game_states_big.json")

    time_taken.append(end-start)
    print(str(n)+"-game (*"+ str(final) +") took", end-start, "seconds to compute")

    start = time.time() # Timing the isomorphism computation

    mygame.compute_isomorphism_types()
    K = len(mygame.iso_dict)

    end = time.time()

    mygame.export_to_json_iso(filename=str(n)+"_game_states_iso.json")

    time_taken_iso.append(end-start)
    print(str(n)+"-game (K_"+str(n)+"="+str(K)+") took", end-start, "seconds to compute")

    stats = mygame.export_stats()
    stats["time_nim:"] = time_taken[-1]
    stats["time_iso:"] = time_taken_iso[-1]

    games[int(n)] = stats

print(time_taken, sep=',')
print(time_taken_iso, sep=',')

with open("games.json", "w") as f:
    json.dump(games, f, indent=2)

# print K and M on the y-axis in the same graph, with n_chips as the x-axis
ns = sorted(games.keys())
K_vals = [games[n]["K:"] for n in ns]
M_vals = [games[n]["M:"] for n in ns]

fig, ax1 = plt.subplots(figsize=(8, 5))

color1 = "tab:blue"
ax1.plot(ns, K_vals, marker="o", color=color1, linewidth=2)
ax1.set_xlabel("Number of tiers n")
ax1.set_ylabel("K", color=color1)
ax1.tick_params(axis="y", labelcolor=color1)

ax2 = ax1.twinx()
color2 = "tab:red"
ax2.plot(ns, M_vals, marker="s", color=color2, linewidth=2)
ax2.set_ylabel("M", color=color2)
ax2.tick_params(axis="y", labelcolor=color2)

ax1.set_xticks(ns)
plt.title("K and M by number of tiers")
fig.tight_layout()
plt.savefig("K_and_M.png", dpi=200)
plt.close()