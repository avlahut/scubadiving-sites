#!/usr/bin/python
# Train a Name Entity Model to pull out divesite destinations
import sys, os
#needed for comments_iterator import
sys.path.append("../name-entity")

import nltk
import re
import logging
import pickle
from pymongo import MongoClient
from mitie import *
from nltk.corpus import stopwords
from nltk.collocations import *
from gensim.models import word2vec, Phrases
from gensim.models.phrases import Phraser
from divesites import Divesites

class CommentsIterator(object):

    stop_words = stopwords.words('english')
    ner = None #our Name Entity model

    def __init__(self, ner, client, collections = [], Ngrams=None):

            self.db = client.scubaboard
            if collections:
                self.collections = collections
            else:
                self.collections = self.db.collection_names()
                 #remove the indexes one
                self.collections.remove("system.indexes")

            #load the NER model in order to use in the iterator
            logging.info("Loading NER model")
            self.ner = ner

            logging.debug("Using %s as Ngrams" % Ngrams)
            self.use_grams = Ngrams

            self.ngrams_transformer = Ngram_words()
            logging.info("Initializing divesite info")
            self.divesites = Divesites(client.divesites)


    def __iter__(self):

            for col_name in self.collections:
                logging.info("Using collection: %s" % col_name)
                printC = True
                col = self.db[col_name]
                comments = col.find({},{ "comments": 1} )
                for c in comments:
                    comment = c["comments"]
                    for line in comment:
                        word= self.tokenize_only(line["text"])
                        if word not in self.stop_words:
                            yield list(word)




    def get_ent_person(self,x,entities,filter_score = 0):
        '''
            Return a list of PERSON entities within x and entities.
        '''
        person_tuple_list = self.get_ent(x,entities,'PERSON')

        return [word for word,score in person_tuple_list if score > filter_score]

    def get_ent_location(self,x,entities, filter_score = 0):
        '''
            Return a list of LOCATION entities within x and entitites
        '''
        location_tuple_list = self.get_ent(x,entities,'LOCATION')

        return [word for word,score in location_tuple_list if score > filter_score]

    def get_ent_organization(self,x,entities, filter_score = 0):
        '''
            Return a list of ORGANIZATION entities within x and entitites
        '''
        org_tuple_list = self.get_ent(x,entities,'LOCATION')

        return [word for word,score in org_tuple_list if score > filter_score]

    def get_ent_divesite(self,tokens):
        '''
        Return list of divesites
        '''
        return self.divesites.match_divesiteslist(self.divesites.all_sites)


    def get_ent(self,x,entities,entity_type):
        entities_list = []
        for e in entities:
            rangee = e[0]
            tag = e[1]
            score = e[2]
            entity_text = " ".join(x[i] for i in rangee)
            if tag == entity_type:
                entities_list.append((entity_text,score))
        return entities_list



    def tokenize_only(self,text):
        '''
        Yield tokens for the given text, removing stop words or diving specific data
        Add bigrams to the return set
        '''
        acronym_dict = {"SG" : "Spiegel_Grove", "WPB" : "West_Palm_Beach", "Speigel" : "Spiegel",
                   "Vandy" : "Vandenburg", "p'cola" : "Pensacola", "KL" : "Key Largo", "KW" : "Key_West",
                   "FL" : "Florida", "GC" : "Grand_Cayman" , "HI" : "" , "AFAIK": "" , "ASAP" : "" , "NOSPAM" : ""
                   , "Hi" : "" , "Thanks": "" , "thanks" : "" , "LOL" : "" , "DM" : "divemaster" , "lol" : ""
                   , 'Hey' : "" , "'" : "" , 'Spiegal': 'Spiegel' , 'Spiegle': 'Spiegel' , 'Speigle': 'Spiegel' ,
                   'Duanne' : 'duane'}

        # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
        text = re.sub("[^a-zA-Z']",             # The pattern to search for
                      " ",                      # The pattern to replace it with
                      text )                    # The text to search

        # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
        tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]


        #logging.debug(bi_grams.vocab)
        #tokens.append(bi_grams)
        if self.use_grams == None:
            pass
            #logging.debug("Not using any Ngrams during iterator process")
        else:
            if 'bi' in self.use_grams:
                #call the bigrams function
                tokens = self.ngrams_transformer.create_bigrams(tokens)

            if 'tri' in self.use_grams:
                #call the trigrams function
                tokens = self.ngrams_transformer.create_trigrams(tokens)


        #Extract all entities
        entities = self.ner.extract_entities(tokens)
        #replace all entities listed as a PERSON to the string NAME as we don't care about these.
        #this string will be filtered out later in the process but important to keep in for the word2vec model
        person_entities = self.get_ent_person(tokens,entities,.5)
        #tag locations accordingly. Use a high score for accurate precision
        location_entities = self.get_ent_location(tokens,entities,1)
        #tag divesites accordingly
        divesite_entities = self.get_ent_divesite(tokens)

        for token in tokens:
            if token.lower() not in self.stop_words or not token:
                if token in acronym_dict:
                    token = acronym_dict[token]

                if token in person_entities:
                    #need to review. filtering out some divesites
                    yield '[NAME]'
                    #yield token + '/NAME'
                elif token in location_entities: #tagging locations, make all lowercase to normalize
                    yield token.lower() + '/LOCATION'
                elif token.lower() in divesite_entities:
                    yield token.lower() + '/DIVESITE'
                else:
                    yield token

class Ngram_words(object):

    def __init__(self):
        #read the bigram and trigram objects
        with open(r"../model/bigram_transformer.pickle", "rb") as input_file:
            bigram_transformer = pickle.load(input_file)

        with open(r"../model/trigram_transformer.pickle", "rb") as input_file2:
            trigram_transformer = pickle.load(input_file2)

        self.bigram_phraser = Phraser(bigram_transformer)
        self.trigram_phraser = Phraser(trigram_transformer)

    def create_bigrams(self,sentence):
        '''
        For the given sentence, return the bigrams for that sentence based on the prior pretrained
        Phrases
        '''
        return self.bigram_phraser[sentence]

    def create_trigrams(self,sentence):
        '''
        For the given sentence, return the trigrams for that sentence based on the prior pretrained
        Phrases
        '''
        return self.trigram_phraser[sentence]

    def create_bigrams_transformer(self, c_iterator):
        '''
        Create and return a bigram transformer to be used on individual sentences.
        '''
        #create bigrams from the sentences
        #bigram_measures = nltk.collocations.BigramAssocMeasures()
        #finder = BigramCollocationFinder.from_words(tokens, window_size = 5)
        #finder.apply_freq_filter(10)

        #bi_grams = finder.nbest(bigram_measures.pmi, 5)
        #bi_grams = Phrases(list(tokens))

        phrases =  Phrases(c_iterator, min_count=100,threshold=50)
        self.bigram_phraser = Phraser(phrases)
        return phrases

    def create_trigrams_transformer(self,bi_iterator, c_iterator):
        '''
        Create and return a trigram transformer to be used on individual sentences
        '''
        #return Phrases(bi_iterator[c_iterator])
        return Phrases(self.bigram_phraser[c_iterator], min_count=100, threshold=50)

if __name__ == "__main__":

    local = True

    logging.basicConfig(filename='../logs/create_Ngrams.log',level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

    if not local: #using SSH tunnel
        ner_model = named_entity_extractor("../../../../MITIE/MITIE-models/english/ner_model.dat")
        client = MongoClient(host='localhost', port=27018)
        #db = client.scubaboard
        collections = ["florida-diving"]
    else:
        ner_model = named_entity_extractor("../../MITIE-models/english/ner_model.dat")
        client = MongoClient(host='localhost', port=27017)
        #db = client.scubaboard
        #collections = ["florida-diving"]
        collections = ['africa', 'asia', 'aust-nz-pacific', 'canada', 'central-america', 'central-us', 'europe', 'florida-diving', 'general-vacation', 'greater-carribean', 'hawaii', 'mexico', 'northeastern-us', 'south-america', 'southeastern-us', 'texas', 'western-us']

    #leave ngrams as none to avoid a loop. Here we are training the set.
    c = CommentsIterator(ner_model,client,collections)

    #train the bigram transformer
    bigram_nwords = Ngram_words()

    bigram_transformer = bigram_nwords.create_bigrams_transformer(c)

    logging.debug("Created %s tokens (bigrams + unigrams) based on the given iterator" % len(bigram_transformer.vocab))

    #pickle it for further use
    with open(r"../model/bigram_transformer.pickle", "wb") as output_file:
        pickle.dump(bigram_transformer, output_file)

    trigram_transformer = bigram_nwords.create_trigrams_transformer(bigram_transformer,c)

    logging.debug("Created %s tokens (trigrams + bigrams + unigrams) based on the given iterator" % len(trigram_transformer.vocab))
    with open(r"../model/trigram_transformer.pickle", "wb") as output_file:
        pickle.dump(trigram_transformer, output_file)
