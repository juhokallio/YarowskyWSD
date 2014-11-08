#coding: utf8

import unittest
from models import Collocation
from os import listdir


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
                word_pair = (word, context[index - 1])
                add_collocation(word_pair, 3, sense)
            if word_index == index - 1 and len(context) >= index + 1:
                word_pair = (word, context[index + 1])
                add_collocation(word_pair, 4, sense)
            if word_index == index + 1 and len(context) >= index + 2:
                word_pair = (word, context[index + 2])
                add_collocation(word_pair, 5, sense)
    return collocations


def build_collocation_likelihoods(collocations):
    return sorted(collocations.values(), lambda x,y: x.cmp(y))


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

def extract_contexts_from_file(file_name):
    txt = open(file_name)
    print txt.read()


def extract_contexts_from_folder(folder, pattern, k):
    contexts = []
    for f in listdir(folder):
        contexts.extend(extract_context_list(open(folder + "/" + f).read(), pattern, k))
        print "Contexts from the file", f, "extracted"
    return contexts


pattern = "plant"
k = 10
folder = "data"
contexts = extract_contexts_from_folder(folder, pattern, k)
contexts_with_senses = init_context_list(contexts, ["life", "manufacturing"])
print "senses added"
collocations = build_collocations(contexts_with_senses, pattern, k, 2)
print "collocations created"
collocation_likelihoods = build_collocation_likelihoods(collocations)
print "collocations sorted, length: ", len(collocation_likelihoods)
for i in range(0, 10):
    print i + 1, collocation_likelihoods[i].log_likelihood(), collocation_likelihoods[i].rule, collocation_likelihoods[i].words, collocation_likelihoods[i].best_sense()


class TextExtraction(unittest.TestCase):
    longMessage = True
    TEXT = "Erikoistumislinja kouluttaa bioinformatiikan ammattilaisia, jotka kykenevät ymmärtämään biologisia kysymyksenasetteluja laskennallisina haasteina.  Erikoistumislinjan opiskelijana tulet tutustumaan tämän hetken kuumimpiin tutkimusongelmiin molekyylibiologiassa ja opit yleisiä periaatteita ja menetelmiä laskennallisten ongelmien mallintamiseen ja ratkaisuun. Algoritmien ja koneoppimisen perusteiden lisäksi, tutkintoon kuuluu biologiselle datalle räätälöityjä laskennallisia menetelmiä, sekä valinnaisten opintojen kautta tutkinto antaa mahdollisuuden sisällyttää opintoihin varsinaisia molekyylibiologian ja muiden lähialojen kursseja."

    def test_extract_context_list(self):
        k = 10
        context_list = extract_context_list(self.TEXT, "biologisia", k)
        self.assertEqual(len(context_list), 1, msg="Wrong number of matching contexts found")
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
        self.assertEqual(collocations[(("molekyylibiologiassa", "opit"), 4)].get_sense_count(0), 1)
        self.assertEqual(collocations[(("opit", "yleisiä"), 5)].get_sense_count(0), 1)

    def test_build_collocation_likelihoods(self):
        collocations = {
            ("ei niin hyva", 0): Collocation("ei niin hyva", 0, 2).plus(0, 2),
            ("paras", 0): Collocation("paras", 0, 2).plus(0, 40),
            ("huonoin", 0): Collocation("huonoin", 0, 2),
            ("jotain", 1): Collocation("jotain", 0, 2).plus(0),
            ("foo", 2): Collocation("foo", 0, 2).plus(1, 20),
            (("bar", "bar2"), 3): Collocation(("bar", "bar2"), 0, 2).plus(1, 10),
        }
        collocation_likelihoods = build_collocation_likelihoods(collocations)
        self.assertEqual(collocation_likelihoods[0].words, "paras")
        self.assertEqual(collocation_likelihoods[1].words, "foo")
        self.assertEqual(collocation_likelihoods[2].words, ("bar", "bar2"))
        self.assertEqual(collocation_likelihoods[3].words, "ei niin hyva")
        self.assertEqual(collocation_likelihoods[4].words, "jotain")
        self.assertEqual(collocation_likelihoods[5].words, "huonoin")
