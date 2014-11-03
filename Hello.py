#coding: utf8

import unittest


def init_context_list(contexts, seeds):
    def classify(context):
        for index, seed in enumerate(seeds):
            if seed in context:
                # Sense is the index of the fitting seed
                return context, index
        # Unknown sense
        return context, -1

    return map(classify, contexts)


def build_collocations(contexts, pattern):
    collocations = [{}, {}, {}, {}, {}, {}]

    def add_collocation(c_index, word, sense):
        # Not yet in collocation
        if word not in collocations[c_index]:
            collocations[c_index][word] = []
            collocations[c_index][word][sense] = 1
        else:
            collocations[c_index][word][sense] += 1

    for context in contexts:
        sense = context[1]
        index = context[0].index(pattern)
        for word_index, word in enumerate(context):
            if abs(word_index - index) > 1:
                add_collocation(2, word, sense)
            elif word_index == index + 1:
                add_collocation(0, word, sense)
            elif word_index == index - 1:
                add_collocation(1, word, sense)


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
