import sys, traceback
#needed for comments_iterator import
sys.path.append("../name-entity")
sys.path.append("../word2vec")
from flask import Flask,render_template, request,send_from_directory, send_file
from divesites import Divesites
from scuba_word2vec import ScubaWord2Vec
from pymongo import MongoClient
import json
from os import listdir
from os.path import isfile, join


app = Flask(__name__)

local = False

if not local: #using SSH tunnel
    client = MongoClient(host='localhost', port=27018)
    db = client.divesites
else:
    client = MongoClient(host='localhost', port=27017)
    db = client.divesites

ds = Divesites(db)

w2v = ScubaWord2Vec()

@app.route('/images/<path:path>')
def send_image(path):
    return send_file("images/" + path, mimetype='image/jpg')

@app.route('/getimages/<path:path>')
def send_images(path):
    return json.dumps([f for f in listdir("images/" + path) if isfile(join("images/" + path, f)) and not f.startswith('.')])#send_from_directory('images', path)

@app.route('/')
def showMachineList():
    return render_template('list.html')

@app.route("/getSimiliarSite",methods=['GET','POST'])
def getSimiliarDiveSites():

    app.logger.debug("JSON received...")
    #app.logger.debug(request.json)

    if request.json:
        sitedata = request.json # will be
        app.logger.debug(type(sitedata))
        #pull out the names of the site to search against the model
        searchList = []
        for key, value in sitedata.items():
            siteName = value["name"]
            searchList.append(siteName)

        #retrieve strings to search by. This will translate the search strings
        #to variations that the model may know about
        sitesToMatch = ds.match_divesiteslist(searchList)

        app.logger.debug(sitesToMatch)
        #verify which words are in the model vocab
        wordsInVocab = w2v.is_word_in_vocab(sitesToMatch)

        app.logger.debug(wordsInVocab)
        if len(wordsInVocab) > 0:
        #retrieve the most similar divesites to the words in the vocab
            mostSimilar = w2v.most_similar_divesite(wordsInVocab)
            app.logger.debug(mostSimilar)
            similarJSON = ds.search_string_to_site(mostSimilar)
            app.logger.debug(similarJSON)
        else:
            similarJSON = "site is not in vocab"

        return json.dumps(similarJSON)

    else:
        return "no json received"


@app.route("/getDiveSite",methods=['GET'])
def getDiveSites():
    try:
        divesiteList = ds.display_divesites_json()
    except Exception as e:
        traceback.print_exc()
        return str(e)

    return json.dumps(sorted(divesiteList, key = lambda site: site["regionAndName"]))

@app.route("/getSimiliarAdj",methods=['GET','POST'])
def getSimiliarAdjs():

    if request.json:
        sitedata = request.json # will be
        app.logger.debug(type(sitedata))
        #pull out the names of the site to search against the model
        searchList = []
        for key, value in sitedata.items():
            siteName = value["name"]
            searchList.append(siteName)

            #retrieve strings to search by. This will translate the search strings
            #to variations that the model may know about
            sitesToMatch = ds.match_divesiteslist(searchList)

            app.logger.debug(sitesToMatch)
            #verify which words are in the model vocab
            wordsInVocab = w2v.is_word_in_vocab(sitesToMatch)
            if len(wordsInVocab) > 0:
                #retrieve the most similar adjectives to the words in the vocab
                mostSimilar = w2v.most_similar_adjective(wordsInVocab)
                app.logger.debug(mostSimilar)
            else:
                mostSimilar = "site is not in vocab"

        return json.dumps(mostSimilar)

    else:
        return "no json received"


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)
