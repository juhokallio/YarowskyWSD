__author__ = 'juka'

import math
import unittest


class Collocation:
    # Epsilon
    E = 0.1

    def __init__(self, words, rule, sense_count):
        self.words = words
        self.rule = rule
        self.senses = [0] * sense_count
        self.count = 0

    # Probability
    def p(self, sense):
        assert sense < len(self.senses), "No such sense"
        return (self.senses[sense] + self.E) / (self.count + self.E * len(self.senses))

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

    def __hash__(self):
        return hash((self.words, self.rule))

    def __eq__(self, other):
        return (self.words, self.rule) == (other.words, other.rule)


class TextCollocation(unittest.TestCase):
    longMessage = True
    def test_p(self):
        collocation = Collocation("a", 0, 3)
        collocation.plus(0)
        self.assertAlmostEqual(collocation.p(0), 0.84, delta=0.01, msg="Wrong probability with collocation with three senses")
        self.assertAlmostEqual(collocation.p(1), 0.08, delta=0.01, msg="Wrong probability with collocation with three senses")
        collocation.plus(0).plus(1).plus(2)
        self.assertAlmostEqual(collocation.p(0), 0.48, delta=0.01, msg="Wrong probability with collocation with three senses")

    def test_log_likelihood(self):
        collocation = Collocation("a", 0, 2)
        collocation.plus(0, 31)
        self.assertAlmostEqual(collocation.log_likelihood(0), 8.28, delta=0.01, msg="Wrong log likelihood with collocation with two senses")
        self.assertAlmostEqual(collocation.log_likelihood(), 8.28, delta=0.01, msg="Wrong log likelihood with collocation with two senses")
        self.assertEqual(collocation.count, 31)
        collocation.plus(1)
        self.assertEqual(collocation.count, 32)

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
