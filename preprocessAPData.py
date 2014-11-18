#!/usr/bin/python
#coding: utf8

###
#
# This script preprocesses AP-1988 news data files and stores
# each article in them into a separate file. Preprocessing consists
# of converting to lower case, removing punctuation and truncating each
# sequence of white-space to a single space symbol.
#
###

import os
import sys
import re

OUTPUT_DIR = "ap-singles"
# non-greedy
ARTICLE_REGEX    = r"<TEXT>(.*?)</TEXT>"
PUNCT_REGEX      = r"[^\w\s]"
WHITESPACE_REGEX = r"\s+"

#
# Strips the directory from path. Leaves the file name.
#
# Returns the file name without a directory.
#
def parseFileName(path):
    #  if there's a / in the middle
    if "/" in path.strip("/"):
        return path.rsplit("/", 1)[0]
    else:
        return path.strip("/")

#
# Creates a directory named name if it does not exist.
#
def createDirIfDoesNotExist(name):
    try:
        os.makedirs(name)
    except OSError:
        if not os.path.isdir(name):
            raise
#
# Prints a help message.
#
def print_help():
    print "Usage: python {} FILE...".format(parseFileName(sys.argv[0]))


paths = sys.argv[1:]
if len(paths) == 0:
    print_help()
    exit(1)

createDirIfDoesNotExist(OUTPUT_DIR)

# total number of articles in all files
nrArticles = 0

for path in paths:
    try:
        f = open(path)
    except IOError as e:
        print "Unable to open file {}.".format(path)
        continue
    contents = f.read()
    articles = re.findall(ARTICLE_REGEX, contents, re.DOTALL)

    inputFileName = parseFileName(path)
    # number of articles read from current file
    nrArticlesInFile = 0
    for article in articles:
        article = article.lower()
        article = article.strip()
        # remove punctuation
        article = re.sub(PUNCT_REGEX, '', article)
        # replace sequences of white space with a space
        article = re.sub(WHITESPACE_REGEX, " ", article)

        # if (len(article) < 50):
        #     continue

        outputPath = "{}/{}-{}".format(OUTPUT_DIR, inputFileName, nrArticlesInFile)
        g = open(outputPath, "w")
        g.write(article)
        g.close()

        nrArticles += 1
        nrArticlesInFile += 1

    f.close()

print "Total: {} articles".format(nrArticles)