#!/usr/bin/python
from mitie import *
import unittest
from pymongo import MongoClient


class TestNERModel(unittest.TestCase):


    ner =  named_entity_extractor("../model/divesites_ner_model.dat")

    def get_ent_simp(self,tokens,entities):

        entities_list = []
        for e in entities:
            rangex = e[0]
            tag = e[1]
            score = e[2]
            score_text = "{:0.3f}".format(score)
            entity_text = " ".join(tokens[i] for i in rangex)
            print("   Score: " + score_text + ": " + tag + ": " + entity_text)
            entities_list.append((score,tag,entity_text))

        return entities_list

    def test_ner_site_and_org(self):
        sentence = "If it looks the weather/ seas might be an issue though, I might decide to stay around Palm Beach, so I have Blue_Heron_Bridge as a bailout option."

        entities = self.ner.extract_entities(sentence.split())

        simple_ent = self.get_ent_simp(sentence.split(),entities)

        self.assertTrue(len(simple_ent)==1)
        self.assertGreater(simple_ent[0][0], 0) #score greater than 0 means it pulled out a confident site



if __name__ == '__main__':
    unittest.main()
