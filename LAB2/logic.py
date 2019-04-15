import functools


class Labels:
    """
    Labels describing the WumpusWorld
    """
    WUMPUS = 'w'
    TELEPORTER = 't'
    POISON = 'p'
    SAFE = 'o'

    """
    Some sets for simpler checks
    >>> if literal.label in Labels.DEADLY: 
    >>>     # Don't go there!!!
    """
    DEADLY = set([WUMPUS, POISON])
    WTP = set([WUMPUS, POISON, TELEPORTER])

    UNIQUE = set([WUMPUS, POISON, TELEPORTER, SAFE])

    POISON_FUMES = 'b'
    TELEPORTER_GLOW = 'g'
    WUMPUS_STENCH = 's'

    INDICATORS = set([POISON_FUMES, TELEPORTER_GLOW, WUMPUS_STENCH])


def stateWeight(state):
    """
    To ensure consistency in exploring states, they will be sorted 
    according to a simple linear combination. 
    The maps will never be 
    larger than 20x20, and therefore this weighting will be consistent.
    """
    x, y = state
    return 20 * x + y


@functools.total_ordering
class Literal:
    """
    A literal is an atom or its negation
    In this case, a literal represents if a certain state (x,y) is or is not 
    the location of GhostWumpus, or the poisoned pills.
    """

    def __init__(self, label, state, negative=False):
        """
        Set all values. Notice that the state is remembered twice - you
        can use whichever representation suits you better.
        """
        x, y = state

        self.x = x
        self.y = y
        self.state = state

        self.negative = negative
        self.label = label

    def __key(self):
        """
        Return a unique key representing the literal at a given point
        """
        return (self.x, self.y, self.negative, self.label)

    def __hash__(self):
        """
        Return the hash value - this operator overloads the hash(object) function.
        """
        return hash(self.__key())

    def __eq__(first, second):
        """
        Check for equality - this operator overloads '=='
        """
        return first.__key() == second.__key()

    def __lt__(self, other):
        """ 
        Less than check
        by using @functools decorator, this is enough to infer ordering
        """
        return stateWeight(self.state) < stateWeight(other.state)

    def __str__(self):
        """
        Overloading the str() operator - convert the object to a string
        """
        if self.negative:
            return '~' + self.label
        return self.label

    def __repr__(self):
        """
        Object representation, in this case a string
        """
        return self.__str__()

    def copy(self):
        """
        Return a copy of the current literal
        """
        return Literal(self.label, self.state, self.negative)

    def negate(self):
        """
        Return a new Literal containing the negation of the current one
        """
        return Literal(self.label, self.state, not self.negative)

    def isDeadly(self):
        """
        Check if a literal represents a deadly state
        """
        return self.label in Labels.DEADLY

    def isWTP(self):
        """
        Check if a literal represents GhostWumpus, the Teleporter or 
        a poisoned pill
        """
        return self.label in Labels.WTP

    def isSafe(self):
        """
        Check if a literal represents a safe spot
        """
        return self.label == Labels.SAFE

    def isTeleporter(self):
        """
        Check if a literal represents the teleporter
        """
        return self.label == Labels.TELEPORTER


class Clause:
    """ 
    A disjunction of finitely many unique literals. 
    The Clauses have to be in the CNF so that resolution can be applied to them. The code 
    was written assuming that the clauses are in CNF, and will not work otherwise. 

    A sample of instantiating a clause (~B v C): 

    >>> premise = Clause(set([Literal('b', (0, 0), True), Literal('c', (0, 0), False)]))

    or; written more clearly
    >>> LiteralNotB = Literal('b', (0, 0), True)
    >>> LiteralC = Literal('c', (0, 0), False)

    >>> premise = Clause(set(((LiteralNotB, LiteralC))))
    """

    def __init__(self, literals):
        """
        The constructor for a clause. The clause assumes that the data passed 
        is an iterable (e.g., list, set), or a single literal in case of a unit clause. 
        In case of unit clauses, the Literal is wrapped in a list to be safely passed to 
        the set.
        """
        if not type(literals) == set and not type(literals) == list:
            self.literals = set([literals])
        else:
            self.literals = set(literals)

    def isResolveableWith(self, otherClause):
        """
        Check if a literal from the clause is resolveable by another clause - 
        if the other clause contains a negation of one of the literals.
        e.g., (~A) and (A v ~B) are examples of two clauses containing opposite literals 
        """
        for literal in self.literals:
            if literal.negate() in otherClause.literals:
                return True
        return False

    def isRedundant(self, otherClauses):
        """
        Check if a clause is a subset of another clause.
        """
        for clause in otherClauses:
            if self == clause:
                continue
            if clause.literals.issubset(self.literals):
                return True
        return False

    def negateAll(self):
        """
        Negate all the literals in the clause to be used 
        as the supporting set for resolution.
        """
        negations = set()
        for literal in self.literals:
            clause = Clause(literal.negate())
            negations.add(clause)
        return negations

    # Added to make nil polling easier.
    def is_nil(self):
        return len(self.literals) is 0

    def __str__(self):
        """
        Overloading the str() operator - convert the object to a string
        """
        return ' V '.join([str(literal) for literal in self.literals])

    def __repr__(self):
        """
        The representation of the object
        """
        return self.__str__()

    def __key(self):
        """
        Return a unique key representing the literal at a given point
        """
        return tuple(sorted(list(self.literals)))

    def __hash__(self):
        """
        Return the hash value - this operator overloads the hash(object) function.
        """
        return hash(self.__key())

    def __eq__(first, second):
        """
        Check for equality - this operator overloads '=='
        """
        return first.__key() == second.__key()

# region My implementations
def resolution(clauses, goal):
    """
    Implement refutation resolution.

    The pseudocode for the algorithm of refutation resolution can be found
    in the slides. The implementation here assumes you will use set of support
    and simplification strategies. We urge you to go through the slides and
    carefully design the code before implementing.
    """
    resolved = set()
    support_set = goal.negateAll()

    # Technically we should run this until all conclusions have been reached, but the algorithm will stop before that.
    while True:
        # First we need to filter our data not to have redundancy and valid formulae.
        remove_redundant(clauses, support_set)
        remove_valid_expressions(clauses, support_set)

        # We fetch all the pairs we can resolve.
        clause_pairs = select_clauses(clauses, support_set, resolved)

        # If there are no pairs to resolve, we cannot conclude anything, so we return False.
        if len(clause_pairs) is 0:
            return False

        new = set()

        # We iterate through each pair as we will conclude from them
        for pair in clause_pairs:
            resolvents = resolve_pair(*pair)
            # Each par we resolve, we mark in resolved.
            resolved.add(pair)

            # Since resolvents are a set, we need to check if any of them are nil. If yes, then we have proven our
            # assumption to be true, and we return True.
            for resolvent in resolvents:
                if resolvent.is_nil():
                    return True

            # We add all the newly concluded resolvents to new.
            new.update(resolvents)

        # Since we've completed our deductions, we will iterate through each member of the clause pairs.
        for clause_1, clause_2 in clause_pairs:
            # We define a set of clauses that we'll remove from clauses and the support set,
            set_to_be_removed = {clause_1, clause_2}

            # and we remove them from both since there is nothing new we'll be able to conclude from them.
            clauses -= set_to_be_removed
            support_set -= set_to_be_removed

        # If new is a subset of all the clauses, that means we cannot infer anything new,
        # so our assumption must be false.
        if new.issubset(clauses | support_set):
            return False

        # We add all the new conclusions to the set of support.
        support_set = support_set | new


def remove_valid_expressions(clauses, support_set):
    to_remove = set()
    all_clauses = clauses | support_set

    # We run through all the clauses we have.
    for clause in all_clauses:
        # If the clause is resolvable with itself (contains a literal and it negated), then it's a valid formula.
        if clause.isResolveableWith(clause):
            to_remove.add(clause)

    for clause in to_remove:
        if clause in clauses:
            clauses.remove(clause)
        elif clause in support_set:
            support_set.remove(clause)


def remove_redundant(clauses, support_set):
    """
    Remove redundant clauses (clauses that are subsets of other clauses)
    from the aforementioned sets.
    Be careful not to do the operation in-place as you will modify the
    original sets. (why?)
    """
    to_remove = set()
    all_clauses = clauses | support_set

    # Self explanatory.
    for clause in all_clauses:
        if clause.isRedundant(all_clauses):
            to_remove.add(clause)

    for clause in to_remove:
        if clause in clauses:
            clauses.remove(clause)
        elif clause in support_set:
            support_set.remove(clause)


def resolve_pair(first_clause, second_clause):
    """
    Resolve a pair of clauses.
    """
    to_remove = set()

    # Go through the literals of the first clause.
    for literal in first_clause.literals:
        # If you find it negated in the second clause's literals, att it to the removal list.
        if literal.negate() in second_clause.literals:
            to_remove.add(literal)

    # If we haven't found and literals to remove, that means the pair cannot be resolved.
    if len(to_remove) is 0:
        raise RuntimeError("Pair is not resolvable.")

    to_return = set()

    # We have to add a newly resolved clause for every literal we're able to eliminate from the clauses.
    for sign_to_remove in to_remove:
        temp = set(filter(lambda x: x != sign_to_remove, first_clause.literals))
        temp.update(set(filter(lambda x: x != sign_to_remove.negate(), second_clause.literals)))
        to_return.add(Clause(temp))

    return to_return


def select_clauses(clauses, support_set, resolved):
    """
    Select pairs of clauses to resolve.
    """
    selected = set()
    all_clauses = clauses | support_set

    # First parent is from set of support, second is from either set.
    for support in support_set:
        for clause in all_clauses:
            # Make sure we're not checking duplicate clauses, and if they're not resolved already and resolvable,
            # add them to the clauses we can select.
            if clause != support and clause.isResolveableWith(support) and (clause, support) not in resolved:
                selected.add((clause, support))

    return selected


def testResolution():
    """
    A sample of a resolution problem that should return True.
    You should come up with your own tests in order to validate your code.
    """
    premise1 = Clause(set([Literal('a', (0, 0), True), Literal('b', (0, 0), False)]))
    premise2 = Clause(set([Literal('b', (0, 0), True), Literal('c', (0, 0), False)]))
    premise3 = Clause(Literal('a', (0, 0)))

    goal = Clause(Literal('c', (0, 0)))
    print resolution(set((premise1, premise2, premise3)), goal)

    premise = Clause({Literal("W", (1, 3)), Literal("W", (2, 2)), Literal("W", (1, 1))})
    goal = Clause(Literal("W", (1, 3)))

    print(resolution({premise}, goal))
# endregion


if __name__ == '__main__':
    """
    The main function - if you run logic.py from the command line by 
    >>> python logic.py 

    this is the starting point of the code which will run. 
    """
    testResolution()
