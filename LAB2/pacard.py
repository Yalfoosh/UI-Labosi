"""
In search.py, you will implement generic search algorithms which are called by
Pacman agents (in searchAgents.py).
"""

import util
from logic import *


class SearchProblem:
    """
    This class outlines the structure of a search problem, but doesn't implement
    any of the methods (in object-oriented terminology: an abstract class).

    You do not need to change anything in this class, ever.
    """

    def getStartState(self):
        """
        Returns the start state for the search problem.
        """
        util.raiseNotDefined()

    def isGoalState(self, state):
        """
          state: Search state

        Returns True if and only if the state is a valid goal state.
        """
        util.raiseNotDefined()

    def getSuccessors(self, state):
        """
        state: Search state

        For a given state, this should return a list of triples, (successor,
        action, stepCost), where 'successor' is a successor to the current
        state, 'action' is the action required to get there, and 'stepCost' is
        the incremental cost of expanding to that successor.
        """
        util.raiseNotDefined()

    def getCostOfActions(self, actions):
        """
        actions: A list of actions to take

        This method returns the total cost of a particular sequence of actions.
        The sequence must be composed of legal moves.
        """
        util.raiseNotDefined()


def miniWumpusSearch(problem):
    """
    A sample pass through the miniWumpus layout. Your solution will not contain 
    just three steps! Optimality is not the concern here.
    """
    from game import Directions
    e = Directions.EAST
    n = Directions.NORTH
    return [e, n, n]


# region My implementations
def logicBasedSearch(problem):
    visited_states = list()
    starting_state = problem.getStartState()
    visited_states.append(starting_state)

    knowledge = dict()

    safe_states = set()
    unsafe_states = set()
    uncertain_states = set()
    current_state = starting_state

    # Technically we don't need this, but for the sake of completeness...
    wumpus_coordinates = None

    while True:
        # If we've reached our goal, just reconstruct the path we'd taken.
        if problem.isGoalState(current_state):
            return problem.reconstructPath(visited_states)

        wumpus_close = problem.isWumpusClose(current_state)
        poison_close = problem.isPoisonCapsuleClose(current_state)
        teleporter_close = problem.isTeleporterClose(current_state)

        # We need to update the values instead of overriding them since we're only updating a subset of the data.
        if current_state not in knowledge:
            knowledge[current_state] = dict()

        knowledge[current_state].update({"S": wumpus_close, "C": poison_close, "G": teleporter_close, "O": True})

        # We could do without memorizing the successor states, but this is more efficient.
        successor_states = [hypothetical_state[0] for hypothetical_state in problem.getSuccessors(current_state)]

        # We need to try and infer something from every of our neighbours.
        for successor_state in successor_states:
            # We only want to visit states we already haven't and that we know are not unsafe.
            if successor_state not in visited_states and successor_state not in unsafe_states:
                # We will be doing this a lot because Python doesn't automatically initialize shit.
                if successor_state not in knowledge:
                    knowledge[successor_state] = dict()

                # First we get some premises for our neighbours.
                premises = get_premises(successor_states, current_state, knowledge, wumpus_coordinates)

                # We're interested in teleporters, safe spaces, wumpus' and poison.
                for label in ["T", "O", "W", "P"]:
                    # For each category, we try to conclude something.
                    knowledge[successor_state][label] = get_conclusions(knowledge[successor_state],
                                                                        premises,
                                                                        successor_state,
                                                                        label)

                # Well, if our neighbour is a teleporter, we just want to go there, no questions asked.
                if knowledge[successor_state]["T"]:
                    visited_states.append(current_state)

                    return problem.reconstructPath(visited_states)
                # If our neighbour is a safe space, we need to update our uncertain states and add the field to a
                # our set of safe states.
                elif knowledge[successor_state]["O"]:
                    if successor_state not in safe_states:
                        if successor_state in uncertain_states:
                            uncertain_states.remove(successor_state)

                        safe_states.add(successor_state)
                # If our neighbour is a wumpus, we need to update our uncertain sattates and add it to unsafe states.
                elif knowledge[successor_state]["W"]:
                    if successor_state in uncertain_states:
                        uncertain_states.remove(successor_state)

                    unsafe_states.add(successor_state)

                    # If we detect a new wumpus, something went wrong. Normally this never passes.
                    if wumpus_coordinates is not None and wumpus_coordinates != successor_state:
                        print("WTF 2 Shens")

                    # Since we've found our wumpus, we assign our successor state to wumpus coordinates.
                    wumpus_coordinates = successor_state
                # If our neighbour is a poison pill, we do the same thing like with wumpus, but without memorizing
                # its coordinates.
                elif knowledge[successor_state]["P"]:
                    if successor_state in uncertain_states:
                        uncertain_states.remove(successor_state)

                    unsafe_states.add(successor_state)
                # Since we cannot infer what the hell we're next to, just add it to uncertain states.
                else:
                    uncertain_states.add(successor_state)

        # If we have safe states to choose from, we'll take the least heavy one and go there.
        if len(safe_states) is not 0:
            current_state = get_lowest_state_weight(safe_states)

            safe_states.remove(current_state)
        # Since we don't have any safe spaces to choose from, we need to compromise with uncertain states.
        elif len(uncertain_states) is not 0:
            found_acceptable_spot = False
            inconclusives = set()

            # While we have states to choose from and until we find and acceptable spot, we'll look at our options.
            while uncertain_states and not found_acceptable_spot:
                # We're prioritizing the lightest states.
                successor_state = get_lowest_state_weight(uncertain_states)
                # For now we're removing that state from uncertain states, but we'll add it later if it's no use.
                uncertain_states.remove(successor_state)

                if successor_state not in knowledge:
                    knowledge[successor_state] = dict()

                # I wish Python returned None by default when accessing stuff by index.
                currently_safe_spot = knowledge[successor_state].get("O", None)
                currently_wumpus = knowledge[successor_state].get("W", None)
                currently_poison = knowledge[successor_state].get("P", None)

                # If the state is a wumpus or a poison, it's no use to us. Maybe we'd also want to add the states to
                # unsafe states, but ehhhh
                if currently_wumpus or currently_poison:
                    continue
                # If the state is a safe spot, well, gib it.
                elif currently_safe_spot:
                    found_acceptable_spot = True
                # Now we have to think:
                else:
                    if not (currently_wumpus or currently_poison):
                        if currently_wumpus is None or currently_poison is None:
                            inconclusives.add(successor_state)
                        else:
                            found_acceptable_spot = True
                    # If we can say what they are, and if they're neither a wumpus or poison, we've found our place.

            # Here, we return all inconclusives that were of no use to us to the original set.
            uncertain_states = uncertain_states | inconclusives

            # If we've found an acceptable spot, we go to it.
            if found_acceptable_spot:
                current_state = successor_state         # Python is being stupid, successor state is always inited.
            # If not, oh well, take the least heavy uncertain state and hope for the best.
            elif len(uncertain_states) is not 0:
                current_state = get_lowest_state_weight(uncertain_states)
                uncertain_states.remove(current_state)
            # If we have nothing to choose from, game over, sit and wait.
            else:
                return problem.reconstructPath(visited_states)
        # If there are no safe or uncertain spaces available, then we just need to chill and wait for help.
        else:
            return problem.reconstructPath(visited_states)

        # After every iteration, we visit the last state.
        visited_states.append(current_state)


def get_premises(successor_states, current_state, knowledge, wumpus_coordinates):
    clauses = set()

    if current_state not in knowledge:
        current_state[knowledge] = dict()

    wumpus_close = knowledge[current_state].get("S", None)
    poison_close = knowledge[current_state].get("C", None)
    teleporter_close = knowledge[current_state].get("G", None)

    # region Teleporter is close
    if teleporter_close:
        literal_set = set()

        # We assume that if we knew about a teleporter beforehand, we'd go to it immediately. Since we don't, it
        # could be on a neighbouring block, but it's not a certainty, unless our algorithm sucks.
        for state in successor_states:
            literal_set.add(Literal("T", state))

        clauses.add(Clause(literal_set))
    else:
        for state in successor_states:
            if state not in knowledge:
                knowledge[state] = dict()

            # No teleporter light seen, no teleporter nearby!
            clauses.add(Clause({Literal('T', state, True)}))
            knowledge[state]["T"] = False
    # endregion

    # region Wumpus is close
    if wumpus_close:
        literal_set = set()

        for state in successor_states:
            if state not in knowledge:
                knowledge[state] = dict()

            # If we've found the assumption in our database, well then, add the whole clause to clauses.
            if "W" in knowledge[state]:
                clauses.add(Clause({Literal('W', state, not knowledge[state]["W"])}))
            # If not, this neighbour is just one of many who CAN contain a wumpus, but doesn't necessarily.
            else:
                if wumpus_coordinates is not None:
                    clauses.add(Clause({Literal('W', state, not (state == wumpus_coordinates))}))
                else:
                    literal_set.add(Literal('W', state))

        clauses.add(Clause(literal_set))
    else:
        for state in successor_states:
            if state not in knowledge:
                knowledge[state] = dict()

            # Since we haven't smelled wumpus, he is 100% on a neighbouring block.
            clauses.add(Clause({Literal('W', state, True)}))
            knowledge[state]["W"] = False
    # endregion

    # region Poison pill is close
    if poison_close:
        literal_set = set()

        for state in successor_states:
            if state not in knowledge:
                knowledge[state] = dict()

            # If we have found a pill in our database, add it to our clauses.
            if "P" in knowledge[state]:
                clauses.add(Clause({Literal('P', state, not knowledge[state]["P"])}))
            # If not, it's on one of the neighbouring blocks, so add it to the set of literals.
            else:
                literal_set.add(Literal('P', state))

        clauses.add(Clause(literal_set))
    else:
        for state in successor_states:
            if state not in knowledge:
                knowledge[state] = dict()

            # Since we haven't smelled some delicious poison, it's 100% not on a neighbouring block.
            clauses.add(Clause({Literal("P", state, True)}))
            knowledge[state]["P"] = False
    #endregion

    # region Current block is safe
    # If we do not smell poison or wumpus, all our neighbouring blocks are safe.
    if not (wumpus_close or poison_close):
        for state in successor_states:
            if state not in knowledge:
                knowledge[state] = dict()

            clauses.add(Clause({Literal("O", state)}))
            knowledge[state]["O"] = True

    for state in successor_states:
        if state not in knowledge:
            knowledge[state] = dict()

        # Let's check if we know if some of our neighbouring blocks contain a wumpus or a poison pill.
        currently_wumpus = knowledge[state].get("W", None)
        currently_poison = knowledge[state].get("P", None)

        # If either do, then we conclude they're obviously not safe states.
        if currently_wumpus or currently_poison:
            clauses.add(Clause({Literal("O", state, True)}))
            knowledge[state]["O"] = False
        # If they're not unknown, and they don't containg a wumpus or a poison pill, then we're certain they're safe.
        elif not (currently_wumpus is None or currently_poison is None) and not (currently_wumpus or currently_poison):
            clauses.add(Clause({Literal("O", state)}))
            knowledge[state]["O"] = True
    # endregion

    return clauses


def get_conclusions(state_knowledge, clauses, state, label):
    # If we have already concluded something about the label, gib it.
    if label in state_knowledge:
        return state_knowledge[label]
    # If not, we need to think.
    else:
        # Check if our assumption is true through resolution.
        assumption_is_true = resolution(clauses, Clause(Literal(label, state)))

        # If it isn't,
        if not assumption_is_true:
            # Check if its negation grants us a different result. If yes, we have proved it by contradiction.
            if assumption_is_true != resolution(clauses, Clause(Literal(label, state, True))):
                return assumption_is_true
            # If not, something is wrong, we can't conclude anything as we likely have a contradiction somewhere.
            else:
                return None

        # Well, if we haven't proven ourselves otherwise, return the initial result.
        return assumption_is_true


def get_lowest_state_weight(states):
    # I sure hope our argument is an iterable object.
    states = list(states)

    # We're assuming the first state is the lightest one.
    lowest_state, lowest_weight = states[0], stateWeight(states[0])

    for state in states[1:]:
        if stateWeight(state) < lowest_weight:
            lowest_state = state
            lowest_weight = stateWeight(state)

    return lowest_state
# endregion


# Abbreviations
lbs = logicBasedSearch
