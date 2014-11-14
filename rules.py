__author__ = 'juka'


def k_closest(context, index_of_pattern, words):
    for index, w in enumerate(context):
        if w == words and (index < index_of_pattern - 1 or index > index_of_pattern + 1):
            return True
    return False


def right(context, index_of_pattern, words):
    if len(context) <= index_of_pattern + 1:
        return False
    else:
        return context[index_of_pattern + 1] == words


def left(context, index_of_pattern, words):
    if index_of_pattern == 0:
        return False
    else:
        return context[index_of_pattern - 1] == words


def two_left(context, index_of_pattern, words):
    if index_of_pattern < 2:
        return False
    else:
        return (context[index_of_pattern - 2], context[index_of_pattern - 1]) == words


def surround(context, index_of_pattern, words):
    if index_of_pattern >= len(context) - 1 or index_of_pattern == 0:
        return False
    else:
        return (context[index_of_pattern - 1], context[index_of_pattern + 1]) == words


def two_right(context, index_of_pattern, words):
    if index_of_pattern >= len(context) - 2:
        return False
    else:
        return (context[index_of_pattern + 1], context[index_of_pattern + 2]) == words


RULES = {
    0: right,
    1: left,
    2: k_closest,
    3: two_left,
    4: surround,
    5: two_right
}
