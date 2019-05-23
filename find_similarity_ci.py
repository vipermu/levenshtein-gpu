import pymysql.cursors
from techniques import *
import string
from Levenshtein import distance

import time
import os
import pickle


# QUERY SQL: 
#"SELECT id, name FROM crawling_item WHERE reference IS NULL"


""" 
    SQL Connection to the desired database
"""
def find_similarity_ci(ci_ids_list, ci_names_list, ref, ean, *, ref_name = "Chicco Physio chupete caucho todogoma cereza talla media",
                        num_posible_products = 20, visuals = False):
    

    """ 
        Preprocess the names
    """

    print("Starting preprocess..\n")

    stoplist = stopwords.words(language)
    extra_stopwords = "" # extra stopwords
    stoplist = stoplist + extra_stopwords.split()
    lemmatizer = WordNetLemmatizer() # set lemmatizer
    stemmer = PorterStemmer() # set stemmer

    # Preprocess a given string name
    def name_preprocessing(name):
        text = removeUnicode(name)
        text = replaceURL(text) # normalization in case of having urls
        text = removeNumbers(text) # remove integers from text
        text = replaceMultiExclamationMark(text) #  repetitions of exlamation marks with the tag "multiExclamation"
        text = replaceMultiQuestionMark(text) #  repetitions of question marks with the tag "multiQuestion"
        text = replaceMultiStopMark(text) #  repetitions of stop marks with the tag "multiStop"
        
        return text

    # Tokenize a given string (converts string to a list os strings applying intermediate preprocessings)
    def tokenize(text):
        onlyOneSentenceTokens = [] # tokens of one sentence each time

        tokens = nltk.word_tokenize(text)    
        tokens = replaceNegations(tokens) #  "not" and antonym for the next word and if found, replaces not and the next word with the antonym
        translator = str.maketrans('', '', string.punctuation)
        text = text.translate(translator) #  punctuation
        tokens = nltk.word_tokenize(text) # it takes a text as an input and provides a list of every token in it
            
        for w in tokens:
            if (w not in stoplist): #  remove stopwords
                final_word = addCapTag(w) #  a word with at least 3 characters capitalized and adds the tag ALL_CAPS_
                final_word = final_word.lower() #  all characters
                final_word = replaceElongated(final_word) #  replaces an elongated word with its basic form, unless the word exists in the lexicon
                final_word = lemmatizer.lemmatize(final_word) #  lemmatizes words
                final_word = stemmer.stem(final_word) #  apply stemming to words
                    
                onlyOneSentenceTokens.append(final_word)           
            
        return onlyOneSentenceTokens 



    # Reference name tokenized
    ref_token = tokenize(name_preprocessing(ref_name))



    """ 
        find_products: finds the most similar products given a list of crawling item name strings
    """
    def find_products(name_list):
        posible_products = []
        offset = 0

        for idx, name in enumerate(name_list):
            # Conditions to speed-up the process
            name_splitted = name.split(' ')
            if len(name_splitted) <= 0 or len(set(name_splitted).intersection(set(ref_name.split(" ")))) <= 2:
                offset += 1 # because of an initial condition for the minimum distance algorithm
                continue
            
            if visuals:
                print(idx, end='\r')

            # Current text preprocessing and tokenization      
            text = name_preprocessing(name)
            token = tokenize(text)  
            
            # Algorithm to select the most similar products
            word_distances = []
            for t in token:
                min_dist = 100000

                for r in ref_token:
                    dist = distance(r,t)

                    if dist<min_dist:
                        min_dist = dist
                
                word_distances.append(min_dist)
            
            token_distance = sum(word_distances)/len(token)

            if idx<num_posible_products+offset:
                posible_products.append((idx, token_distance))

            else:
                index, distances = list(zip(*posible_products))
                if token_distance < max(distances):
                    substitution_index = distances.index(max(distances))
                    posible_products[substitution_index] = (idx, token_distance)

        return posible_products

    posible_products = find_products(ci_names_list)
    indexes, distances = list(zip(*posible_products))

    if visuals:
        print("##################################################################")  
        print(f"Reference text: {ref_name}")
        print("##################################################################\n")    
        print("Most similar texts:")
        sorted_dist = sorted(distances)
        for i, idx in enumerate([idx for dist,idx in sorted(zip(distances, indexes))]):
            print(f"Name: {ci_names_list[idx]}")
            print(f"Distance: {sorted_dist[i]} \n")

    posible_products_ids = []
    for idx in [idx for _,idx in sorted(zip(distances, indexes))]:
        posible_products_ids.append(ci_ids_list[idx])

    print(posible_products_ids)
    return posible_products


# EXAMPLE:
init = time.time()
find_similarity_ci()
print(f"Time elapsed: {time.time() - init}")