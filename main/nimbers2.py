"""
nimbers2.py

Another attempt to compute the (correct) nimbers 
"""
import numpy as np

# Global parameter on whether moves should be checked for size, legality
# each time they are initialized
CHECK = (True, True)

class state:
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
    next: list (of bitmap)
        list of all possible next states as bitmaps
    nimber: unsigned int
        computed nimber
    complete: bool
        value assigned whether nimber was already computed or not

    """

    def __init__(self, bitmap, n_tiers=3, check=CHECK):
        self.n_tiers = n_tiers
        self.bitmap = bitmap

        if CHECK[0]:
            if not self.check():
                raise ValueError("Wrong syntax state initialized in state.__init__")
        if CHECK[1]:
            if not self.is_legal():
                raise ValueError("Illegal state initialized in state.__init__")
        


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
        """

        print('*' * (2* self.n_tiers + 3))

        for i in range(self.n_tiers):
            row = self.n_tiers - i - 1
            print('* ', end='')
            print(' '*row, end='')
            for col in range(self.n_tiers - row):
                if (self.bitmap[row][col]):
                    print('0', end=' ')
                else:
                    print('X', end=' ')
            print(' '*row, end='*\n')

        print('*' * (2* self.n_tiers + 3))


    def above(self, row, col):
        """ Returns indices (row, col) of above given stone as a tuple"""
        if (row == self.n_tiers - 1):
            return ()
        if (col == 0):
            return (self.bitmap[row+1][col])
        return (self.bitmap[row+1][col], self.bitmap[row+1][col-1])
    
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

        if num_above == 2 | (not bitmap[row][col]): # stop that chud
            raise IndexError("Illegal removal at ("+row+","+col+") using state.remove")
        
        elif num_above == 1: # try to remove the one right above
            if above[0]: # <--kill left
                bitmap[row][col] = False
                return self.remove(row+1, col, bitmap)
            else:        # <--kill right
                return self.remove(row+1, col-1, bitmap)
            
        else: # no more at the top. Remove this one
            bitmap[row][col] = False
            return bitmap
        

        
        
        



##############################################################################
# Testing

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