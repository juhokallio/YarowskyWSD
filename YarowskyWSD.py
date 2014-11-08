#coding: utf8

import unittest
import math


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
        if sense in self.senses:
            self.senses[sense] += 1
        else:
            self.senses[sense] = 1
        self.count += 1
        return self

    def get_sense_count(self, sense):
        return self.senses[sense]

    def __hash__(self):
        return hash((self.words, self.rule))

    def __eq__(self, other):
        return (self.words, self.rule) == (other.words, other.rule)


def init_context_list(contexts, seeds):
    def classify(context):
        for index, seed in enumerate(seeds):
            if seed in context:
                # Sense is the index of the fitting seed
                return context, index
        # Unknown sense
        return context, -1

    return map(classify, contexts)


def build_collocations(contexts_with_senses, pattern, k, sense_count):
    # 0: Word immediately to the right
    # 1:
    #
    collocations = {}

    def add_collocation(words, rule, sense):
        if (words, rule) not in collocations:
            collocations[(words, rule)] = Collocation(words, rule, sense_count)
        collocations[(words, rule)].plus(sense)

    for context_with_sense in contexts_with_senses:
        context = context_with_sense[0]
        sense = context_with_sense[1]
        if sense == -1:
            continue
        index = index_of_pattern(context, pattern, k)
        for word_index, word in enumerate(context):
            if abs(word_index - index) > 1:
                add_collocation(word, 2, sense)
            elif word_index == index + 1:
                add_collocation(word, 0, sense)
            elif word_index == index - 1:
                add_collocation(word, 1, sense)

            if word_index == index - 2:
                word_pair = (word, context[word_index + 1])
                add_collocation(word_pair, 3, sense)
    return collocations


# TODO: optimize with rbtree or something more sensible
def build_collocation_likelihoods(collocations):
     epsilon = 0.1
   #  for collocation in collocations:




# Currently doesn't take account repeating patterns in the end or beginning of corpus.
# Flag based approach should fix this, but gains are minimal.
def index_of_pattern(context, pattern, k):
    for index, value in enumerate(context):
        if value == pattern:
            if len(context) - index - 1 == k or index == k:
                return index


def extract_context_list(text, pattern, k):
    words = text.split()
    contexts = []
    for index, word in enumerate(words):
        if word == pattern:
            begin = max(index - k, 0)
            end = min(index + k + 1, len(words))
            contexts.append(words[begin:end])
    return contexts


class TextExtractionTest(unittest.TestCase):
    TEXT = "Erikoistumislinja kouluttaa bioinformatiikan ammattilaisia, jotka kykenevät ymmärtämään biologisia kysymyksenasetteluja laskennallisina haasteina.  Erikoistumislinjan opiskelijana tulet tutustumaan tämän hetken kuumimpiin tutkimusongelmiin molekyylibiologiassa ja opit yleisiä periaatteita ja menetelmiä laskennallisten ongelmien mallintamiseen ja ratkaisuun. Algoritmien ja koneoppimisen perusteiden lisäksi, tutkintoon kuuluu biologiselle datalle räätälöityjä laskennallisia menetelmiä, sekä valinnaisten opintojen kautta tutkinto antaa mahdollisuuden sisällyttää opintoihin varsinaisia molekyylibiologian ja muiden lähialojen kursseja."

    def test_extract_context_list(self):
        k = 10
        context_list = extract_context_list(self.TEXT, "biologisia", k)
        print context_list[0]
        self.assertEqual(len(context_list), 1)
        context_list = extract_context_list(self.TEXT, "molekyylibiologian", k)
        self.assertEqual(context_list[0][-1], "kursseja.")
        context_list = extract_context_list(self.TEXT, "koneoppimisen", k)
        self.assertEqual(len(context_list[0]), 2 * k + 1)
        context_list = extract_context_list(self.TEXT, "ammattilaisia,", 2)
        self.assertEqual(context_list[0][-1], "kykenevät")
        self.assertEqual(context_list[0][0], "kouluttaa")

    def test_init_context_list(self):
        k = 3
        context_list = extract_context_list(self.TEXT, "ammattilaisia,", k)
        self.assertEqual(len(context_list[0]), 2 * k + 1)
        context_list = init_context_list(context_list, ["kissa", "kouluttaa"])
        self.assertEqual(len(context_list[0][0]), 2 * k + 1)
        self.assertEqual(context_list[0][1], 1)

    def test_index_of_pattern(self):
        pattern = "ja"
        context = ["a", pattern, "b"]
        self.assertEqual(index_of_pattern(context, pattern, 1), 1)
        context = [pattern, "b"]
        self.assertEqual(index_of_pattern(context, pattern, 1), 0)
        context = ["a", pattern, pattern, "b", "c"]
        self.assertEqual(index_of_pattern(context, pattern, 2), 2)

    def test_build_collocations(self):
        k = 5
        pattern = "ja"
        context_list = extract_context_list(self.TEXT, pattern, k)
        self.assertEqual(context_list[0].count(pattern), 2)
        senses = ["yleisiä"]
        context_list = init_context_list(context_list, senses)
        collocations = build_collocations(context_list, pattern, k, len(senses))
        self.assertEqual(collocations["opit", 0].get_sense_count(0), 1)
        self.assertEqual(collocations["menetelmiä", 0].get_sense_count(0), 1)
        self.assertEqual(collocations["tämän", 2].get_sense_count(0), 1)
        self.assertEqual(collocations["hetken", 2].get_sense_count(0), 1)
        self.assertTrue(("tutustumaan", 2) not in collocations)
        self.assertTrue(("tämän", 1) not in collocations)
        self.assertEqual(collocations[(("tutkimusongelmiin", "molekyylibiologiassa"), 3)].get_sense_count(0), 1)

    def test_p(self):
        collocation = Collocation("a", 0, 3)
        collocation.plus(0)
        self.assertAlmostEqual(collocation.p(0), 0.84, delta=0.01)
        self.assertAlmostEqual(collocation.p(1), 0.08, delta=0.01)
        collocation.plus(0).plus(1).plus(2)
        self.assertAlmostEqual(collocation.p(0), 0.48, delta=0.01)

    def test_log_likelihood(self):
        collocation = Collocation("a", 0, 2)
        collocation.plus(0)
        self.assertEqual(collocation.log_likelihood(0), 0)