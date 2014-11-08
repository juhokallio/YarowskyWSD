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

    def log_likelihood(self, sense):
        p_sense = self.p(sense)
        return math.log(p_sense / (1 - p_sense), 2)

    def plus(self, sense):
        assert sense < len(self.senses), "No such sense"
        self.senses[sense] += 1
        self.count += 1
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
        collocation.plus(0)
        self.assertEqual(collocation.log_likelihood(0), 0, msg="Wrong log likelihood with collocation with two senses")
