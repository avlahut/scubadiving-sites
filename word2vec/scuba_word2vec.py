#!/usr/bin/python
import logging
from comments_iterator import CommentsIterator
from gensim.models import word2vec, Phrases
from mitie import *
from pymongo import MongoClient

class ScubaWord2Vec(object):

    def __init__(self):
        self.model = word2vec.Word2Vec.load_word2vec_format('../model/scuba.model.bin', binary=True,unicode_errors='ignore')

    def most_similar_adjective(self,listOfSites):
        '''
            Return the most similar adjectives for the list of sites.
            Adj defined as non-divesite or location
        '''
        most_sim = self.model.most_similar_cosmul(positive=listOfSites,topn=10)
        return_most_sim = []
        for word,score in most_sim:
            if 'DIVESITE' not in word:
                return_most_sim.append(word)
        return return_most_sim

    def most_similar_divesite(self,listOfSites):
        '''
            Return the most similar divesite to the list of sites passed in.
        '''
        most_sim = self.model.most_similar_cosmul(positive=listOfSites,topn=100)
        return_most_sim = set()
        for word,score in most_sim:
            if 'DIVESITE' in word:
                return_most_sim.add(word)
        return return_most_sim

    def is_word_in_vocab(self,words):
        '''
            Returns if any of the list of words are in the vocab of the model
        '''
        contains = []
        for word in words:
            word = word + '/DIVESITE'
            if word in self.model:
                contains.append(word)
        return contains

if __name__ == "__main__":

    logging.basicConfig(filename='../logs/word2vec.log',level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

    ner_model = named_entity_extractor("../../../../MITIE/MITIE-models/english/ner_model.dat")

    client = MongoClient(host='localhost', port=27018)
    db = client.scubaboard
    collections = ["florida-diving"]

    logging.info("Starting to train new Word2Vec model")
    #initiate my iterator
    comments = CommentsIterator(ner_model,db,collections,['bi','tri'])

    w2v = word2vec.Word2Vec(comments,min_count=10,workers=5)

    #?? move old model out of the way before resaving this?

    #save new model
    logging.info("Saving word2vec model.")
    w2v.save_word2vec_format('../model/scuba.model.bin', binary=True)
