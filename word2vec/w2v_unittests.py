#!/usr/bin/python
from gensim.models import word2vec

class TestW2VModel(unittest.TestCase):

    model = word2vec.Word2Vec.load_word2vec_format('scuba.model.bin', binary=True)
