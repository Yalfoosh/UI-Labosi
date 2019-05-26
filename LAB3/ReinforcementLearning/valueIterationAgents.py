# valueIterationAgents.py
# -----------------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


import mdp, util

from learningAgents import ValueEstimationAgent


class ValueIterationAgent(ValueEstimationAgent):
    """
        * Please read learningAgents.py before reading this.*

        A ValueIterationAgent takes a Markov decision process
        (see mdp.py) on initialization and runs value iteration
        for a given number of iterations using the supplied
        discount factor.
    """

    def __init__(self, mdp, discount=0.9, iterations=100):
        """
          Your value iteration agent should take an mdp on
          construction, run the indicated number of iterations
          and then act according to the resulting policy.

          Some useful mdp methods you will use:
              mdp.getStates()
              mdp.getPossibleActions(state)
              mdp.getTransitionStatesAndProbs(state, action)
              mdp.getReward(state, action, nextState)
              mdp.isTerminal(state)
        """
        self.mdp = mdp
        self.discount = discount
        self.iterations = iterations
        self.values = util.Counter()

        for k in range(0, iterations):
            current_values = util.Counter()

            for state in mdp.getStates():
                actions = self.mdp.getPossibleActions(state)

                if actions is not None and len(actions) is not 0:
                    max_q_value = self.getQValue(state, actions[0])

                    for action in actions:
                        q_value = self.getQValue(state, action)

                        if q_value > max_q_value:
                            max_q_value = q_value

                    current_values[state] = max_q_value

            self.values = current_values

    def getValue(self, state):
        """
          Return the value of the state (computed in __init__).
        """
        return self.values[state]

    def computeQValueFromValues(self, state, action):
        """
          Compute the Q-value of action in state from the
          value function stored in self.values.
        """
        state_probability_tuples = self.mdp.getTransitionStatesAndProbs(state, action)
        q_value = 0

        for n_state, probability in state_probability_tuples:
            reward = self.mdp.getReward(state, action, n_state)
            current_value = self.getValue(n_state)
            q_value += probability * (reward + self.discount * current_value)

        return q_value

    def computeActionFromValues(self, state):
        """
          The policy is the best action in the given state
          according to the values currently stored in self.values.

          You may break ties any way you see fit.  Note that if
          there are no legal actions, which is the case at the
          terminal state, you should return None.
        """
        if not self.mdp.isTerminal(state):
            possible_actions = self.mdp.getPossibleActions(state)
            max_q_value = self.getQValue(state, possible_actions[0])
            max_action = possible_actions[0]

            for possible_action in possible_actions:
                q_value = self.getQValue(state, possible_action)

                if q_value > max_q_value:
                    max_q_value = q_value
                    max_action = possible_action

            return max_action

        return None

    def getPolicy(self, state):
        return self.computeActionFromValues(state)

    def getAction(self, state):
        "Returns the policy at the state (no exploration)."
        return self.computeActionFromValues(state)

    def getQValue(self, state, action):
        return self.computeQValueFromValues(state, action)
