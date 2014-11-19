#coding: utf8

import unittest
from models import Collocation, Context
from os import listdir


def init_context_list(contexts, seeds):
    for context in contexts:
        for index, seed in enumerate(seeds):
            if seed in context.text:
                # Sense is the index of the fitting seed
                context.sense = index


def build_collocations(contexts, pattern, k, sense_count):
    collocations = {}
    for context in contexts:
        context.update_collocations(collocations, pattern, k, sense_count)
    return collocations


def build_collocation_likelihoods(collocations):
   # big_enough = [c for c in collocations.values() if c.log_likelihood() > THRESHOLD]
    return sorted(collocations.values(), lambda x,y: x.cmp(y))


def extract_context_list(text, pattern, k):
    words = text.split()
    contexts = []
    for index, word in enumerate(words):
        if word == pattern:
            begin = max(index - k, 0)
            end = min(index + k + 1, len(words))
            contexts.append(Context(words[begin:end]))
    return contexts

def extract_contexts_from_file(file_name):
    txt = open(file_name)
    print txt.read()


def extract_contexts_from_folder(folder, pattern, k):
    contexts = []
    i = 1
    for f in listdir(folder):
        contexts.extend(extract_context_list(open(folder + "/" + f).read(), pattern, k))
        # print "Contexts from the file", f, "extracted"
        if i % 1000 == 0:
            print i
        i += 1
    return contexts


def run():
    pattern = "space"
    k = 30
    folder = "ap-singles"
    collocationsLog = "collocations.log"
    contexts = extract_contexts_from_folder(folder, pattern, k)
    contexts_with_senses = init_context_list(contexts, ["planet", "living"])
    print "senses added"
    collocations = build_collocations(contexts_with_senses, pattern, k, 2)
    print "collocations created"
    collocation_likelihoods = build_collocation_likelihoods(collocations)
    print "collocations sorted, length: ", len(collocation_likelihoods)

    for i in range(0, 1000):
        print i, "iteration"
        for i in range(0, 50):
            print i + 1, collocation_likelihoods[i].log_likelihood(), collocation_likelihoods[i].rule, collocation_likelihoods[i].words, collocation_likelihoods[i].best_sense()
        collocation_likelihoods = build_collocation_likelihoods(collocations)
        print "sense 1", sum(1 for c in contexts_with_senses if c[1] == 0)
        print "sense 2", sum(1 for c in contexts_with_senses if c[1] == 1)

        classified_contexts = []
        for index, context in enumerate(contexts):
            context.classify(collocation_likelihoods, pattern, k)
            if context.has_sense():
                classified_contexts.append(context)

        new_collocations = build_collocations(contexts_with_senses, pattern, k, 2)
        if new_collocations == collocations:
            for co in contexts_with_senses[:200]:
                print co.sense, co.text
            break
        else:
            collocations = new_collocations

    f = open(collocationsLog, "w")
    f.write(collocations)
    f.close()

class TextExtraction(unittest.TestCase):
    longMessage = True
    TEXT = "Erikoistumislinja kouluttaa bioinformatiikan ammattilaisia, jotka kykenevät ymmärtämään biologisia kysymyksenasetteluja laskennallisina haasteina.  Erikoistumislinjan opiskelijana tulet tutustumaan tämän hetken kuumimpiin tutkimusongelmiin molekyylibiologiassa ja opit yleisiä periaatteita ja menetelmiä laskennallisten ongelmien mallintamiseen ja ratkaisuun. Algoritmien ja koneoppimisen perusteiden lisäksi, tutkintoon kuuluu biologiselle datalle räätälöityjä laskennallisia menetelmiä, sekä valinnaisten opintojen kautta tutkinto antaa mahdollisuuden sisällyttää opintoihin varsinaisia molekyylibiologian ja muiden lähialojen kursseja."

    def test_extract_context_list(self):
        k = 10
        context_list = extract_context_list(self.TEXT, "biologisia", k)
        self.assertEqual(len(context_list), 1, msg="Wrong number of matching contexts found")

        context_list = extract_context_list(self.TEXT, "molekyylibiologian", k)
        self.assertEqual(context_list[0].text[-1], "kursseja.")

        context_list = extract_context_list(self.TEXT, "koneoppimisen", k)
        self.assertEqual(len(context_list[0].text), 2 * k + 1)

        context_list = extract_context_list(self.TEXT, "ammattilaisia,", 2)
        self.assertEqual(context_list[0].text[-1], "kykenevät")
        self.assertEqual(context_list[0].text[0], "kouluttaa")

    def test_init_context_list(self):
        k = 3
        context_list = extract_context_list(self.TEXT, "ammattilaisia,", k)
        self.assertEqual(len(context_list[0].text), 2 * k + 1)
        init_context_list(context_list, ["kissa", "kouluttaa"])
        self.assertEqual(len(context_list[0].text), 2 * k + 1)
        self.assertEqual(context_list[0].sense, 1)

    def test_build_collocations(self):
        k = 5
        pattern = "ja"
        context_list = extract_context_list(self.TEXT, pattern, k)
        self.assertEqual(context_list[0].text.count(pattern), 2)
        senses = ["yleisiä"]
        init_context_list(context_list, senses)
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
