#!/usr/bin/python
# Train a Name Entity Model to pull out divesite destinations
import sys, os
#needed for comments_iterator import
sys.path.append("../word2vec")

import pandas as pd
from pymongo import MongoClient
from comments_iterator import CommentsIterator
import numpy as np
import logging
import pickle
#MIT NER models
#https://github.com/mit-nlp/MITIE/blob/master/examples/python/train_ner.py
from mitie import *
from nltk.corpus import stopwords
from nltk.collocations import *
from gensim.models import word2vec, Phrases
from gensim.models.phrases import Phraser


def generate_training_sentences(db):
    '''
    Pulls known divesites from the mongo db and creates statements to train the NER models

    input: pymongo database object to pull dive sites data
    output: ner sentences with entities tagged as dive sites
    '''

    words = ['of','dive','wreck','drift','beach','drive','kelp','tank','buddy','save','recommend','walk','the','a','fish','reef']

    #assume all collections but the native system indexes have our dive sites, regardless of source
    collections = db.collection_names()
    collections.remove("system.indexes")

    #Read in our list of divesites from the database; assuming multiple collections
    site_df = pd.DataFrame()
    for col_name in collections:
        col = db[col_name]
        site = col.find()
        temp_df = pd.DataFrame(list(site))
        site_df = pd.concat([temp_df,site_df],axis=0)

    #Pull the individual dive sites out into a list
    all_sites = site_df["sites"] #list of json
    all_site_list =[]
    for site_list in all_sites:
        for site in site_list:
            site_trimmed = site["site"].split(',')
            all_site_list.append(site_trimmed[0])

    sample_list = []
    #labeled
    sample_size = 5000
    for i in range(1,sample_size):
        ran_site = list(np.random.choice(all_site_list,1))
        ran_words = list(np.random.choice(words,size=6,replace=True)) #number of random words for this sentence
        #place in word to put the divesite
        in_sentence = np.random.randint(0,7)
        #create random sentences, even if they don't make sense
        #insert site in a random spot in the sentence
        ran_words.insert(in_sentence,ran_site[0])#.append(ran_words[in_sentence:])
        sample = ner_training_instance(ran_words)
        #print(in_sentence)
        #print(ran_words)
        sample.add_entity(range(in_sentence,in_sentence+1),'DIVESITE')
        sample_list.append(sample)

    #unlabeled
    sample_size = 5000
    for i in range(1,sample_size):
        ran_site = list(np.random.choice(all_site_list,1))
        ran_words = list(np.random.choice(words,size=6,replace=True)) #number of random words for this sentence
        #create random sentences, even if they don't make sense
        ran_words.append(ran_site[0])
        #place in word to put the divesite
        in_sentence = np.random.randint(0,7)
        #sentence = ran_words[:in_sentence].append(ran_site[0]).append(ran_words[in_sentence:])
        ran_words.insert(in_sentence,ran_site[0])
        #print(ran_words)
        sample = ner_training_instance(ran_words)
        #sample.add_entity(range(6,len(ran_words)),'DIVESITE')
        sample_list.append(sample)

    return sample_list

def train_ner_model(sentences):
    '''
    Use the given sentences to create custom dive site identifier for a NER model.
    '''
    #using MIT trainer since it was trained on English words
    trainer = ner_trainer("../../MITIE-models/english/total_word_feature_extractor.dat")

    for sentence in sentences:
        trainer.add(sentence)

    ner = trainer.train()

    return ner

def extract_divesites(dive_ner, c_iterator):
    '''
    Using the previously trained model, extract the names of divesites from the raw comments data
    to be incorporated with the iterator.
    '''
    extract_list = []
    for x in c_iterator:
        extract_list.extend(x)

    entities = dive_ner.extract_entities(extract_list)

    divesites = c_iterator.get_ent(extract_list,entities,"DIVESITE")

    return divesites

if __name__ == "__main__":

    logging.basicConfig(filename='trainDiveSites.log',level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    # 1 = train, 0 = load previously trained model.
    train_fl = sys.argv[1]
    logging.debug("System arg is: %s" % train_fl)

    local = True

    #TODO: read from config file; hide behind interface with iterator
    #client = MongoClient(host='localhost', port=27018)
    #db = client.divesites

    if not local: #using SSH tunnel
        ner_model = named_entity_extractor("../../../../MITIE/MITIE-models/english/ner_model.dat")
        client = MongoClient(host='localhost', port=27018)
        db = client.scubaboard
        db2 = client.divesites
        collections = ["florida-diving"]
    else:
        ner_model = named_entity_extractor("../../MITIE-models/english/ner_model.dat")
        client = MongoClient(host='localhost', port=27017)
        db = client.scubaboard
        db2 = client.divesites
        #collections = ["florida-diving"]
        collections = ['africa','asia','aust-nz-pacific','central-america','central-us','florida-diving','greater-carribean','hawaii','mexico','northeastern-us','south-america','southeastern-us','texas','western-us']


    logging.info("Generating training sentences")
    #generate new sentences based on divesites stored within the db
    sentences = generate_training_sentences(db2)

    if len(sentences) > 0:
        #train entity extraction on the new sentences

        if train_fl == 'train':
            logging.info("Generating dive model")
            ner_dive_model = train_ner_model(sentences)

            ner_dive_model.save_to_disk("../model/divesites_ner_model.dat")
        elif train_fl == 'load':
            logging.info("Loading trained divesite model")
            ner_dive_model = named_entity_extractor("../model/divesites_ner_model.dat")
        else:
            print("invalid command line flag: %s. Should be 'train' or  'load' " % train_fl)
            exit(1)

        #run the model against the data to see what kind of divesites it identifies
        logging.info("Extract dive models from data")

        c_iterator = CommentsIterator(ner_model,db,collections,["bi","tri"])
        divesites = extract_divesites(ner_dive_model,c_iterator)

        #pickle it for further use
        with open(r"../model/ner_dive.pickle", "wb") as output_file:
            pickle.dump(divesites, output_file)

    else:
        print("No sentences found to train model")

    #check if the test data passes
