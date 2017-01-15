from unidecode import unidecode
import pandas as pd
from pymongo import MongoClient
import re
import logging

class Divesites(object):

    def __init__(self, db):
        self.all_sites = self.load_divesites(db)


    def load_divesites(self, db):

        collections = db.collection_names()
        collections.remove("system.indexes")
        site_df = pd.DataFrame()
        for col_name in collections:
            col = db[col_name]
            site = col.find()
            json_list = list(site)
            self.site_display = json_list
            temp_df = pd.DataFrame(json_list)
            site_df = pd.concat([temp_df,site_df],axis=0)

        self.divesite_df = site_df

        all_sites = site_df["sites"] #list of json
        all_site_list =[]
        for site_list in all_sites:
            for site in site_list:
                all_site_list.append(site["site"])

        return all_site_list

    def clean_site(self,site_str):
        #take what is before the comma. After the comma is usually location
        site_new = site_str.split(',')[0]
        #handle the case where we screwed up the html scrape
        site_new = site_new.replace('&amp;','and')
        site_match = re.match("(?:.*>)?(.*)",site_new)
        site_new = site_match.group(1)
        return site_new

    def preprocess_divesites(self,site_list):
        '''
        Clean up some of the dive site data. Split divesite names as most comments may not have
        the complete name
        '''
        new_all_sites = set()
        for site in site_list:
            #take what is before the comma. After the comma is usually location
            site_new = self.clean_site(site) #.split(',')[0]
            #handle the case where we screwed up the html scrape
            #full site
            #since most people won't put the unicode in their post but the divesites have it
            new_all_sites.add(unidecode(site_new))

            #now split the cases where there might be two sites in one title.
            site_new2 = site_new.split(' and ')
            for site2 in site_new2:
                #print(type(site2))
                new_all_sites.add(site2.strip())

            site_new3 = site_new.split('/')
            for site3 in site_new3:
                #print(type(site3))
                new_all_sites.add(site3.strip())

        return new_all_sites

    def match_divesiteslist(self,site_list):
        '''
        Method to create divesite tokens to match to n_grams in comments
        '''
        sites = self.preprocess_divesites(site_list)

        new_site_list = []
        for s in sites:
            new_site_list.append(s.lower().replace(' ','_'))

        return new_site_list

    def flatten_divesites(self,divesiteList):
        '''
            Flatten out the divesites to region rather than nested structure
        '''
        divesitejson = []
        for site in divesiteList:
            site_dict = dict(site)
            for site in site_dict["sites"]:
                site_new = self.clean_site(site["site"])
                regString = site_dict["region"] + " : " + site_new
                divesite = {
                    'regionAndName' : regString,
                    'region':site_dict["region"],
                    'name':site_new,
                    'description': site["description"]
                    }
                divesitejson.append(divesite)
        return divesitejson

    def display_divesites_json(self):
        '''
        Returns a json object for pretty display
        '''
        return self.flatten_divesites(self.site_display)

    def search_string_to_site(self, site_vocab):
        '''
        Returns the actual site info (in json) based on the model vocab matched in site_vocab
        '''
        #not the most efficient here but do this for now
        divesites = self.display_divesites_json()

        filtered_sites = []
        #make sure we don't duplicate if we have multiple search terms map to one site
        site_set = set()
        for site in site_vocab:
            groups = re.match("(\w*)(?:/DIVESITE)",site)
            site_string = groups.group(1)
            site_string = site_string.replace('_',' ')
            for complete_site in divesites:
                if complete_site["name"].lower() in site_set:
                    continue
                if site_string in complete_site["name"].lower():
                    site_set.add(complete_site["name"].lower())
                    filtered_sites.append(complete_site)

        return filtered_sites

if __name__ == "__main__":

    local = False

    logging.basicConfig(filename='../logs/create_Ngrams.log',level=logging.DEBUG)

    if not local: #using SSH tunnel
        client = MongoClient(host='localhost', port=27018)
        db = client.divesites
    else:
        client = MongoClient(host='localhost', port=27017)
        db = client.divesites

    ds = Divesites(db)

    ds_list = ds.preprocess_divesites(ds.all_sites)

    print(len(ds_list), type(ds_list))
