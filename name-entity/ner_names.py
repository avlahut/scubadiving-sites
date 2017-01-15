#!/usr/bin/python

import sys
#needed for comments_iterator import
sys.path.append("../word2vec")
import pickle
from mitie import *
from pymongo import MongoClient
from comments_iterator import CommentsIterator
import logging


class ExtractEntities(object):

    def __init__(self, ner, client, collections = [], Ngrams=[]):
        self.ner = ner
        self.db = client.scubaboard
        self.c_iterator = CommentsIterator(ner,client,collections,Ngrams)

    def extract_entities(self,col=[]):
        '''
        Extract PERSON, LOCATION, & ORG from pretrained NER model. Use the db and the collections per input.
        If collections is empty, retrieve all collections within the database
        '''
        #logging.info('Using ' + col + 'to extract entities')
        self.c_iterator.collections = col
        #the ner model requires a list, so use the iterator to pull in data. Expecting throttling will need
        #be done here on the list of collections sent to the iterator
        extract_list = []
        for x in self.c_iterator:
            extract_list.extend(x)

        logging.debug('Extracting entities from %s' % len(extract_list))
        entities = self.ner.extract_entities(extract_list)

        self.people = self.c_iterator.get_ent_person(extract_list,entities)
        self.location = self.c_iterator.get_ent_location(extract_list,entities)
        self.org = self.c_iterator.get_ent_organization(extract_list,entities)

        return entities


    def extract_person(self):
        return self.people

    def extract_location(self):
        return self.location

    def extract_org(self):
        return self.org

if __name__ == "__main__":

    logging.basicConfig(filename='../logs/extract_person.log',level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

    local=False

    if not local: #using SSH tunnel
        ner_model = named_entity_extractor("../../../../MITIE/MITIE-models/english/ner_model.dat")
        client = MongoClient(host='localhost', port=27018)
        #db = client.scubaboard
        #collections = ['florida-diving','asia']
        collections = ['africa', 'europe', 'south-america']
    else:
        ner_model = named_entity_extractor("../../MITIE-models/english/ner_model.dat")
        client = MongoClient(host='localhost', port=27017)
        #db = client.scubaboard
        #collections = ["florida-diving"]
        collections = ['africa', 'asia', 'aust-nz-pacific', 'canada', 'central-america', 'central-us', 'europe', 'florida-diving', 'general-vacation', 'greater-carribean', 'hawaii', 'mexico', 'northeastern-us', 'south-america', 'southeastern-us', 'texas', 'western-us']

    extractor = ExtractEntities(ner_model,client,collections,['bi','tri'])
    first_run = True
    for coll in collections:
        ppl = []
        loc = []
        entities = extractor.extract_entities([coll])
        ppl = extractor.extract_person()
        loc = extractor.extract_location()
        #org = extractor.extract_org()

        print("people:", len(ppl))
        if not first_run:
            logging.debug("Opening previous people file")
            with open(r"../model/ner_ppl.pickle", "rb") as input_file:
                prev_ppl = pickle.load(input_file)
            logging.debug("Loaded prev ppl: %s" % len(prev_ppl))
            ppl.extend(prev_ppl)
            logging.debug("Total ppl: %s" % len(ppl))
            #prev_ppl = []

        with open(r"../model/ner_ppl.pickle", "wb") as output_file:
            pickle.dump(ppl, output_file)

        print("locations:",len(loc))
        if not first_run:
            logging.debug("Opening previous location file")
            with open(r"../model/ner_loc.pickle", "rb") as input_file:
                prev_loc = pickle.load(input_file)
            logging.debug("Loaded prev loc: %s" % len(prev_loc))
            loc.extend(prev_loc)
            #prev_loc = []

        with open(r"../model/ner_loc.pickle", "wb") as output_file:
            pickle.dump(loc, output_file)

        first_run = False
        #print("organizations:", len(org))
        #with open(r"../model/ner_org.pickle", "wb") as output_file:
        #    pickle.dump(org, output_file)
