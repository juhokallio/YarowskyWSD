import unittest


def parse_file_name(path):
    """
    Strips the directory from path. Leaves the file name.
    Returns the file name without a directory.
    """
    if "/" in path.strip("/"):
        return path.rsplit("/", 1)[0]
    else:
        return path.strip("/")


def index_of_pattern(text, pattern, k):
    """
    Currently doesn't take account repeating patterns in the end or beginning of corpus.
    Flag based approach should fix this, but gains are minimal.
    """
    for index, value in enumerate(text):
        if value == pattern:
            last_match = index
            if len(text) - index - 1 == k or index == k:
                return index
    return last_match


class TestUtils(unittest.TestCase):
    def test_index_of_pattern(self):
        pattern = "ja"
        text = ["a", pattern, "b"]
        self.assertEqual(index_of_pattern(text, pattern, 1), 1)
        text = [pattern, "b"]
        self.assertEqual(index_of_pattern(text, pattern, 1), 0)
        text = ["a", pattern, pattern, "b", "c"]
        self.assertEqual(index_of_pattern(text, pattern, 2), 2)
