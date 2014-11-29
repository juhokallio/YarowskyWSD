#coding: utf8

import unittest
import string
from os import listdir
from models import Collocation, Context, Document
from utils import index_of_pattern

# Minimum log-likelihood ratio that causes a context to get classified.
THRESHOLD = 3.9

table = string.maketrans("","")


def init_classified_contexts(contexts, seeds):
    classified_contexts = []
    for context in contexts:
        for index, seed in enumerate(seeds):
            if seed in context.text:
                # Sense is the index of the fitting seed
                context.sense = index
                classified_contexts.append(context)
    return classified_contexts

def build_words_and_rule_to_collocations_map(contexts, pattern, k, sense_count):
    words_and_rule_to_collocations = {}
    for context in contexts:
        context.update_collocations(words_and_rule_to_collocations, pattern, k, sense_count)
    return words_and_rule_to_collocations

#
# Function get_sorted_collocations
#
# Takes as input a words-and-rules-to-collocations map and returns a list of collocations
# sorted by log-likelihood ratio.
#
def get_sorted_collocations(words_and_rule_to_collocations):
   # big_enough = [c for c in collocations.values() if c.log_likelihood() > THRESHOLD]
    return sorted(words_and_rule_to_collocations.values(), lambda x,y: x.cmp(y))


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
            article = []
        else:
            #Remove punctuation, lower case
            stripped = word.translate(table, string.punctuation).lower()
            article.append(stripped)
    # print len(articles), "articles collected"
    return articles


def extract_context_list(article, pattern, k):
    contexts = []
    document = Document()
    for index, word in enumerate(article):
        if word == pattern:
            begin = max(index - k, 0)
            end = min(index + k + 1, len(article))
            contexts.append(Context(article[begin:end], document=document))
    return contexts


def extract_contexts_from_folder(folder, pattern, k):
    contexts = []
    for f in listdir(folder):
        articles = split_to_articles(open(folder + "/" + f).read())
        document_id = 0
        for article in articles:
            contexts.extend(extract_context_list(article, pattern, k))
            document_id += 1
        # print len(contexts), "contexts from the file", f, "extracted"
    return contexts


def classify(context, collocations, pattern, k, threshold):
    for collocation in collocations:
        index = index_of_pattern(context.text, pattern, k)
        if collocation.has_match(context.text, index):
            sense = collocation.best_sense()
            if collocation.log_likelihood(sense) > threshold:
                context.sense = sense
            else:
                context.sense = -1
            return
    context.sense = -1


#
# Function: run
#
# Runs Yarowsky's word sense disambiguation algorithm.
#
# Parameters:
#   pattern: A word with multiple senses.
#   seeds:   Seed words for the algorithm, one for each sense. Should be semantically or otherwise related to the
#            corresponding senses.
#   k:       The number of words to left and right from a pattern occurrence that the algorithm notices when
#            looking for words that occur in the same environment with the pattern.
#
def run(pattern, seeds, k):
    folder = "data"
    log_filename = "collocations.log"
    print "Reading data..."
    contexts = extract_contexts_from_folder(folder, pattern, k)
    classified_contexts = init_classified_contexts(contexts, seeds)
    words_and_rule_to_collocations = build_words_and_rule_to_collocations_map(classified_contexts, pattern, k, 2)
    collocations = get_sorted_collocations(words_and_rule_to_collocations)

    for i in range(0, 1000):
        print i, "iteration"
        for j in range(0, 80):
            print j + 1, collocations[j].log_likelihood(), collocations[j].rule, collocations[j].words, collocations[j].best_sense(), "[", collocations[j].senses[0], ", ", collocations[j].senses[1], "]"

        print "sense 1", sum(1 for c in contexts if c.sense == 0)
        print "sense 2", sum(1 for c in contexts if c.sense == 1)
        print "not classified", sum(1 for c in contexts if c.sense == -1)

        classified_contexts = []
        for index, context in enumerate(contexts):
            classify(context, collocations, pattern, k, THRESHOLD)
            if context.has_sense():
                classified_contexts.append(context)

        print len(classified_contexts), "contexts classified"
        # for co in classified_contexts:
        #         print co.sense, co.text

        new_words_and_rule_to_collocations = build_words_and_rule_to_collocations_map(classified_contexts, pattern, k, 2)
        new_collocations = get_sorted_collocations(new_words_and_rule_to_collocations)
        if new_collocations == collocations:
            # for co in classified_contexts[:200]:
            #     print co.sense, co.text
            break
        else:
            collocations = new_collocations

    log = open(log_filename, "w")
    for k, c in enumerate(collocations):
        line = "{} {} {} {} {}\n".format(k + 1, c.log_likelihood(), c.rule, c.words, c.best_sense())
        log.write(line)

    log.close()


run("bass", ["fish", "player"], 10)


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
        init_classified_contexts(context_list, ["kissa", "kouluttaa"])
        self.assertEqual(len(context_list[0].text), 2 * k + 1)
        self.assertEqual(context_list[0].sense, 1)

    def test_build_collocations(self):
        k = 5
        pattern = "ja"
        context_list = extract_context_list(self.ARTICLE, pattern, k)
        self.assertEqual(context_list[0].text.count(pattern), 2)
        senses = ["yleisiä"]
        init_classified_contexts(context_list, senses)
        collocations = build_words_and_rule_to_collocations_map(context_list, pattern, k, len(senses))
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
        collocation_likelihoods = get_sorted_collocations(collocations)
        self.assertEqual(collocation_likelihoods[0].words, "paras")
        self.assertEqual(collocation_likelihoods[1].words, "foo")
        self.assertEqual(collocation_likelihoods[2].words, ("bar", "bar2"))
        self.assertEqual(collocation_likelihoods[3].words, "ei niin hyva")
        self.assertEqual(collocation_likelihoods[4].words, "jotain")
        self.assertEqual(collocation_likelihoods[5].words, "huonoin")
