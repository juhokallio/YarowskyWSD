__author__ = 'juka'

import math
import unittest
from rules import RULES
from utils import index_of_pattern


# Minimum log likelihood for training contexts
THRESHOLD = 3.5


class Collocation:
    # Epsilon
    E = 0.5

    def __init__(self, words, rule, sense_count):
        self.words = words
        self.rule = rule
        self.senses = [0] * sense_count
        self.count = 0

    # Probability
    def p(self, sense):
        assert sense < len(self.senses), "No such sense"
        p = (self.senses[sense] + self.E) / (self.count + self.E * len(self.senses))
        assert p < 1, "Probability should never be 1"
        assert p > 0, "Probability should never be 0"
        return p

    def log_likelihood(self, sense=None):
        if sense is None:
            sense = self.best_sense()
        p_sense = self.p(sense)
        return abs(math.log(p_sense / (1 - p_sense), 2))

    def best_sense(self):
        m = max(self.senses)
        for index, count in enumerate(self.senses):
            if count == m:
                return index

    def plus(self, sense, amount=1):
        assert sense < len(self.senses), "No such sense"
        self.senses[sense] += amount
        self.count += amount
        return self

    def get_sense_count(self, sense):
        return self.senses[sense]

    def cmp(self, other):
        return cmp(other.log_likelihood(), self.log_likelihood())

    def has_match(self, context, index_of_pattern):
        return RULES[self.rule](context, index_of_pattern, self.words)

    def __hash__(self):
        return hash((self.words, self.rule))

    def __eq__(self, other):
        return (self.words, self.rule, self.senses) == (other.words, other.rule, self.senses)


class Context:

    def __init__(self, text, sense=-1, document=None):
        self.text = text
        self.sense = sense
        self.document = document

    def has_sense(self):
        return self.sense is not -1

    def classify(self, collocations, pattern, k):
        for c in collocations:
            index = index_of_pattern(self.text, pattern, k)
            if c.has_match(self.text, index):
                sense = c.best_sense()
                if c.log_likelihood(sense) > THRESHOLD:
                    self.sense = sense
                else:
                    self.sense = -1
                return
        self.sense = -1

    def update_collocations(self, collocations, pattern, k, sense_count):
        # 0: Word immediately to the right
        # 1:
        #
        if not self.has_sense():
            return

        def add_collocation(words, rule, sense):
            if (words, rule) not in collocations:
                collocations[(words, rule)] = Collocation(words, rule, sense_count)
            collocations[(words, rule)].plus(sense)

        index = index_of_pattern(self.text, pattern, k)
        for word_index, word in enumerate(self.text):
            if abs(word_index - index) > 1:
                add_collocation(word, 2, self.sense)
            elif word_index == index + 1:
                add_collocation(word, 0, self.sense)
            elif word_index == index - 1:
                add_collocation(word, 1, self.sense)

            if word_index == index - 2:
                word_pair = (word, self.text[index - 1])
                add_collocation(word_pair, 3, self.sense)
            if word_index == index - 1 and len(self.text) > index + 1:
                word_pair = (word, self.text[index + 1])
                add_collocation(word_pair, 4, self.sense)
            if word_index == index + 1 and len(self.text) > index + 2:
                word_pair = (word, self.text[index + 2])
                add_collocation(word_pair, 5, self.sense)


class TextCollocation(unittest.TestCase):
    longMessage = True
    def test_p(self):
        collocation = Collocation("a", 0, 3)
        collocation.plus(0)
        self.assertAlmostEqual(collocation.p(0), 0.84, delta=0.01, msg="Wrong probability with collocation with three senses")
        self.assertAlmostEqual(collocation.p(1), 0.08, delta=0.01, msg="Wrong probability with collocation with three senses")
        collocation.plus(0).plus(1).plus(2)
        self.assertAlmostEqual(collocation.p(0), 0.48, delta=0.01, msg="Wrong probability with collocation with three senses")
        collocation = Collocation("a", 0, 2)
        collocation.plus(1, 5).plus(0, 5)
        self.assertEqual(collocation.p(0), 0.5, msg="Wrong probability with collocation with two same counts")

    def test_log_likelihood(self):
        collocation = Collocation("a", 0, 2)
        collocation.plus(0, 31)
        self.assertAlmostEqual(collocation.log_likelihood(0), 8.28, delta=0.01, msg="Wrong log likelihood with collocation with two senses")
        self.assertAlmostEqual(collocation.log_likelihood(), 8.28, delta=0.01, msg="Wrong log likelihood with collocation with two senses")
        self.assertEqual(collocation.count, 31)
        collocation.plus(1)
        self.assertEqual(collocation.count, 32)
        collocation = Collocation("a", 0, 2)
        collocation.plus(1, 5).plus(0, 5)
        self.assertAlmostEqual(collocation.log_likelihood(), 0, delta=0.01, msg="Wrong log likelihood with collocation with two same counts")

    def test_log_likelihood_three_senses(self):
        collocation = Collocation("a", 0, 3)
        collocation.plus(0).plus(1, 3)
        self.assertAlmostEqual(collocation.log_likelihood(1), 1.36, delta=0.01, msg="Wrong log likelihood with collocation with three senses")
        self.assertAlmostEqual(collocation.log_likelihood(), 1.36, delta=0.01, msg="Wrong log likelihood with collocation with three senses")

    def test_best_sense(self):
        collocation = Collocation("a", 0, 3)
        collocation.plus(1)
        self.assertEqual(collocation.best_sense(), 1)
        collocation.plus(0)
        best = collocation.best_sense()
        self.assertTrue(best == 0 or best == 1)
        collocation.plus(0)
        self.assertEqual(collocation.best_sense(), 0)

    def test_has_match(self):
        collocation = Collocation("a", 0, 3)
        self.assertTrue(collocation.has_match(["Test", "context", "is", "a", "nice"], 2))
        collocation = Collocation("a", 1, 3)
        self.assertTrue(collocation.has_match(["Test", "context", "is", "a", "nice"], 4))
        collocation = Collocation("a", 2, 3)
        self.assertTrue(collocation.has_match(["Test", "context", "is", "a", "nice"], 0))
        self.assertTrue(collocation.has_match(["Test", "context", "is", "a", "nice"], 1))
        self.assertFalse(collocation.has_match(["Test", "context", "is", "a", "nice"], 2))
        self.assertFalse(collocation.has_match(["Test", "context", "is", "a", "nice"], 3))
        self.assertFalse(collocation.has_match(["Test", "context", "is", "a", "nice"], 4))
        collocation = Collocation(("context", "is"), 3, 3)
        self.assertTrue(collocation.has_match(["Test", "context", "is", "a", "nice"], 3))
        self.assertFalse(collocation.has_match(["Test", "context", "is", "a", "nice"], 4))
        collocation = Collocation(("is", "nice"), 4, 3)
        self.assertTrue(collocation.has_match(["Test", "context", "is", "a", "nice"], 3))
        self.assertFalse(collocation.has_match(["Test", "context", "is", "a", "nice"], 4))
        collocation = Collocation(("a", "nice"), 5, 3)
        self.assertTrue(collocation.has_match(["Test", "context", "is", "a", "nice"], 2))
        self.assertFalse(collocation.has_match(["Test", "context", "is", "a", "nice"], 1))
