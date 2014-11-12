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

    def cmp(self, other):
        return cmp(other.log_likelihood(), self.log_likelihood())

    # TODO: Refactor this ugly thing
    def has_match(self, context, index_of_pattern):
        for index, word in enumerate(context):
            if abs(index - index_of_pattern) > 1:
                if word == self.words and self.rule == 2:
                    return True
            elif index == index_of_pattern + 1:
                if word == self.words and self.rule == 0:
                    return True
            elif self.rule == 1:
                if word == self.words and index == index_of_pattern - 1:
                    return True

            if index == index_of_pattern - 2:
                word_pair = (word, context[index_of_pattern - 1])
                if word_pair == self.words and self.rule == 3:
                    return True
            if index == index_of_pattern - 1 and len(context) > index_of_pattern + 1:
                word_pair = (word, context[index_of_pattern + 1])
                if word_pair == self.words and self.rule == 4:
                    return True
            if index == index_of_pattern + 1 and len(context) > index_of_pattern + 2:
                word_pair = (word, context[index_of_pattern + 2])
                if word_pair == self.words and self.rule == 5:
                    return True
        return False

    def __hash__(self):
        return hash((self.words, self.rule))

    def __eq__(self, other):
        return (self.words, self.rule, self.senses) == (other.words, other.rule, self.senses)


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
