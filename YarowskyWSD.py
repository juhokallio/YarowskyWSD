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


BEGIN = "<TEXT>"
END = "</TEXT>"


def split_to_articles(text):
    words = text.split()
    articles = []
    article = []
    for word in words:
        if word == BEGIN:
            article = []
        elif word == END:
            articles.append(article)
        else:
            article.append(word)
    print len(articles), "articles collected"
    return articles


def extract_context_list(article, pattern, k):
    contexts = []
    for index, word in enumerate(article):

        if word == pattern:
            begin = max(index - k, 0)
            end = min(index + k + 1, len(article))
            contexts.append(Context(article[begin:end]))
    return contexts


def extract_contexts_from_folder(folder, pattern, k):
    contexts = []
    for f in listdir(folder):
        articles = split_to_articles(open(folder + "/" + f).read())
        for article in articles:
            contexts.extend(extract_context_list(article, pattern, k))
        print len(contexts), "contexts from the file", f, "extracted"
    return contexts


def run(pattern, seeds, k):
    folder = "data"
    collocations_log = "collocations.log"
    contexts = extract_contexts_from_folder(folder, pattern, k)
    print "contexts collected", len(contexts)
    init_context_list(contexts, seeds)
    print "senses added"
    collocations = build_collocations(contexts, pattern, k, 2)
    print "collocations created"
    collocation_likelihoods = build_collocation_likelihoods(collocations)
    print "collocations sorted, length: ", len(collocation_likelihoods)

    for i in range(0, 1000):
        print i, "iteration"
        for i in range(0, 50):
            print i + 1, collocation_likelihoods[i].log_likelihood(), collocation_likelihoods[i].rule, collocation_likelihoods[i].words, collocation_likelihoods[i].best_sense()
        collocation_likelihoods = build_collocation_likelihoods(collocations)
        print "sense 1", sum(1 for c in contexts if c.sense == 0)
        print "sense 2", sum(1 for c in contexts if c.sense == 1)

        classified_contexts = []
        for index, context in enumerate(contexts):
            context.classify(collocation_likelihoods, pattern, k)
            if context.has_sense():
                classified_contexts.append(context)

        print len(classified_contexts), "contexts classified"

        new_collocations = build_collocations(classified_contexts, pattern, k, 2)
        if new_collocations == collocations:
            for co in classified_contexts[:200]:
                print co.sense, co.text
            break
        else:
            collocations = new_collocations

    f = open(collocations_log, "w")
    f.write("asdf")
    f.close()


run("space", ["planet", "living"], 15)


class TextExtraction(unittest.TestCase):
    longMessage = True
    TEXT = "Erikoistumislinja kouluttaa bioinformatiikan ammattilaisia, jotka kykenevät ymmärtämään biologisia kysymyksenasetteluja laskennallisina haasteina.  Erikoistumislinjan opiskelijana tulet tutustumaan tämän hetken kuumimpiin tutkimusongelmiin molekyylibiologiassa ja opit yleisiä periaatteita ja menetelmiä laskennallisten ongelmien mallintamiseen ja ratkaisuun. Algoritmien ja koneoppimisen perusteiden lisäksi, tutkintoon kuuluu biologiselle datalle räätälöityjä laskennallisia menetelmiä, sekä valinnaisten opintojen kautta tutkinto antaa mahdollisuuden sisällyttää opintoihin varsinaisia molekyylibiologian ja muiden lähialojen kursseja."
    ARTICLE = TEXT.split()

    def test_extract_context_list(self):
        k = 10
        context_list = extract_context_list(self.ARTICLE, "biologisia", k)
        self.assertEqual(len(context_list), 1, msg="Wrong number of matching contexts found")

        context_list = extract_context_list(self.ARTICLE, "molekyylibiologian", k)
        self.assertEqual(context_list[0].text[-1], "kursseja.")

        context_list = extract_context_list(self.ARTICLE, "koneoppimisen", k)
        self.assertEqual(len(context_list[0].text), 2 * k + 1)

        context_list = extract_context_list(self.ARTICLE, "ammattilaisia,", 2)
        self.assertEqual(context_list[0].text[-1], "kykenevät")
        self.assertEqual(context_list[0].text[0], "kouluttaa")

    def test_init_context_list(self):
        k = 3
        context_list = extract_context_list(self.ARTICLE, "ammattilaisia,", k)
        self.assertEqual(len(context_list[0].text), 2 * k + 1)
        init_context_list(context_list, ["kissa", "kouluttaa"])
        self.assertEqual(len(context_list[0].text), 2 * k + 1)
        self.assertEqual(context_list[0].sense, 1)

    def test_build_collocations(self):
        k = 5
        pattern = "ja"
        context_list = extract_context_list(self.ARTICLE, pattern, k)
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
