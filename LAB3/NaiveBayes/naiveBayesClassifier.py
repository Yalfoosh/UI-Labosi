import util
import math


class NaiveBayesClassifier(object):
    """
    See the project description for the specifications of the Naive Bayes classifier.

    Note that the variable 'datum' in this code refers to a counter of features
    (not to a raw samples.Datum).
    """
    def __init__(self, legalLabels, smoothing=0, logTransform=False, featureValues=util.Counter()):
        self.legalLabels = legalLabels
        self.type = "naivebayes"
        self.k = int(smoothing) # this is the smoothing parameter, ** use it in your train method **
        self.logTransform = logTransform
        self.featureValues = featureValues # empty if there is no smoothing

    def fit(self, trainingData, trainingLabels):
        """
        Trains the classifier by collecting counts over the training data, and
        stores the smoothed estimates so that they can be used to classify.
        
        trainingData is a list of feature dictionaries.  The corresponding
        label lists contain the correct label for each instance.

        To get the list of all possible features or labels, use self.features and self.legalLabels.
        """

        self.features = trainingData[0].keys() # the names of the features in the dataset

        self.prior = util.Counter() # probability over labels
        self.conditionalProb = util.Counter() # Conditional probability of feature feat for a given class having value v
                                      # HINT: could be indexed by (feat, label, value)

        values = set()

        for instance, label in zip(trainingData, trainingLabels):
            self.prior[label] += 1

            for feature in self.features:
                value = instance[feature]
                values.add(value)

                self.conditionalProb[(feature, label, value)] += 1

        for feature in self.features:
            for label in self.legalLabels:
                label_count = self.prior[label]
                value_sum = 0

                for value in values:
                    key = (feature, label, value)

                    self.conditionalProb[key] = float(self.conditionalProb[key] + self.k) /\
                                                float(label_count + self.k * len(self.features))
                    value_sum += self.conditionalProb[key]

                if value_sum is not 0:
                    for value in values:
                        self.conditionalProb[(feature, label, value)] /= float(value_sum)

        for legal_label in self.legalLabels:
            self.prior[legal_label] = float(self.prior[legal_label] + self.k) /\
                                      float(len(trainingLabels) + self.k * len(self.legalLabels))

        self.prior.normalize()

    def predict(self, testData):
        """
        Classify the data based on the posterior distribution over labels.
        """
        guesses = []
        self.posteriors = []  # posterior probabilities are stored for later data analysis.
        
        for instance in testData:
            if self.logTransform:
                posterior = self.calculateLogJointProbabilities(instance)
            else:
                posterior = self.calculateJointProbabilities(instance)
            guesses.append(posterior.argMax())
            self.posteriors.append(posterior)
        return guesses

    def calculateJointProbabilities(self, instance):
        """
        Returns the joint distribution over legal labels and the instance.
        Each probability should be stored in the joint counter, e.g.
        Joint[3] = <Estimate of ( P(Label = 3, instance) )>

        To get the list of all possible features or labels, use self.features and
        self.legalLabels.
        """
        joint = util.Counter()

        for legal_label in self.legalLabels:
            posterior_probability = 1.0

            for feature in self.features:
                posterior_probability *= self.conditionalProb[(feature, legal_label, instance[feature])]

            joint[legal_label] = posterior_probability * self.prior[legal_label]

        return joint

    def calculateLogJointProbabilities(self, instance):
        """
        Returns the log-joint distribution over legal labels and the instance.
        Each log-probability should be stored in the log-joint counter, e.g.
        logJoint[3] = <Estimate of log( P(Label = 3, instance) )>
        """
        log_joint = util.Counter()

        for label in self.legalLabels:
            posterior_probability = 0  # log(p_1) = log(1) = 0

            for feature in self.features:
                posterior_probability += math.log(self.conditionalProb[(feature, label, instance[feature])])

            log_joint[label] = posterior_probability + math.log(self.prior[label])

        return log_joint
