# scubadiving-sites
Recommend dive sites based on comments using NLP

This project uses NLP techniques against comments retrieved from the scubaboard.com website. This website is unique such that divers often post questions on individual regional boards as to where the best place in that region is to dive, or what divesites would be most appropriate based on their situation within that region. However, one must have already eliminated all other regions before deciding on that one board, or post the question generically on multiple boards. This project was meant to streamline the process and provide the user the ability to narrow down regions and sites that might be most related to previously dived sites.  

###  Pipeline

1. Retrieve data from website (see separate scrapy projects) and load into MongoDB
2. Run comments_iterator.py to create bigrams and trigram phrase models from the data
3. Run ner_names.py to create location, people and places name entity models
4. Run ner_divesites.py to create divesite name entity model
5. Run scuba_word2vec.py to create word2vec model which is ultimately used by the flask app

###  Directories

* model : individual models for the pipeline process. Given their size, models are currently not stored in github
* name-entity : stores classes that create and use the named entity models in the pipeline. 
* word2vec : stores classes that create and use the word2vec model in the pipeline
* FlaskRecommender : simple flask app that provides a front end to query the word2vec model. Also includes installed angular and other required javascript libraries
