import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk import pos_tag, ne_chunk
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import WordNetLemmatizer
from nltk.data import load

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import OneHotEncoder

import numpy as np
import pandas as pd
import string
import sys
sys.path.append("..")
from utils.data import WordEmbeddings

STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
    'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
    'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
    'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
    'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
    'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've',
    'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven',
    'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren',
    'won', 'wouldn', "'ll", "'re", "'ve", "n't", "'s", "'d", "'m", "''", "``"
}

POSTAGS = {'$': 0, "''": 1, '(': 2, ')': 3, ',': 4, '--': 5, '.': 6, ':': 7, 'CC': 8,
 'CD': 9, 'DT': 10, 'EX': 11, 'FW': 12, 'IN': 13, 'JJ': 14, 'JJR': 15, 'JJS': 16, 
 'LS': 17, 'MD': 18, 'NN': 19, 'NNP': 20, 'NNPS': 21, 'NNS': 22, 'PDT': 23, 'POS': 24, 
 'PRP': 25, 'PRP$': 26, 'RB': 27, 'RBR': 28, 'RBS': 29, 'RP': 30, 'SYM': 31, 'TO': 32, 
 'UH': 33, 'VB': 34, 'VBD': 35, 'VBG': 36, 'VBN': 37, 'VBP': 38, 'VBZ': 39, 'WDT': 40, 
 'WP': 41, 'WP$': 42, 'WRB': 43, '``': 44}

# { Part-of-speech constants
ADJ, ADJ_SAT, ADV, NOUN, VERB = 'a', 's', 'r', 'n', 'v'
# }

class Embedder:
    def __init__(self, word_embeddings, seq_length=1000, stopwords='default'):
        """
        Initialises the embedder class.
        Expects a WordEmbeddings object.
        """
        self.embeddings = word_embeddings
        self.MAX_SEQUENCE_LENGTHS = seq_length
        
        if(stopwords == 'default'):
            self.STOPWORDS = STOPWORDS
        else:
            self.STOPWORDS = stopwords

        self.postags = load('help/tagsets/upenn_tagset.pickle')
    
    def tokenize(self, docs):
        """
        Expects a list of strings.
        Returns the tokens and the padded sequences of the documents.
        """
        tokens = []
        sequences = []
        for doc in docs:
            """ Get Tokens """
            doc_tokens = word_tokenize(doc)

            filtered_tokens = []
            filtered_sequence = []

            for w in doc_tokens:
                """ Convert to lowercase """
                word = w.lower()

                """ Remove Stopwords """
                if word not in self.STOPWORDS:
                    if(self.embeddings.in_vocab(word)):
                        filtered_sequence.append(self.embeddings.word_to_index[word])
                    else:
                        """ Autocorrect if word does not exist """
                        filtered_sequence.append(
                            self.embeddings.word_to_index[self.embeddings.autocorrect(word)]
                        )
                    filtered_tokens.append(word)

            sequences.append(filtered_sequence)
            tokens.append(filtered_tokens)

        sequences = pad_sequences(sequences, maxlen=self.MAX_SEQUENCE_LENGTHS)
        return tokens, sequences

    def get_embeddings(self, docs):
        """
        Returns a three dimensional array of shape (n_docs, seq_len, embed_dim)
        Tokenizes every doc, pads them into a sequence of equal length and gets
        the embedding vector for every word. 
        Passable into a keras input layer.
        """

        doc_tokens, sequences = self.tokenize(docs)
        list_of_matrices = []
        """
        Every Matrix should be of shape (SEQ_LEN, EMBEDDING_DIM + meha)
        Use doc_tokens to get the features meha made
        Make one hot vectors out of all of them and append to vector
        """
        
        meha = 0
        seq_len = self.MAX_SEQUENCE_LENGTHS
        emb_dim = self.embeddings.EMBEDDING_DIM

        for sequence in sequences:
            matrix = np.zeros((seq_len, emb_dim + meha))
            print(sequence)
            sentence = [sequence[j] for j in range(0,seq_len)]
            freqs = self.word_frequency(sentence)

            for i in range(0, seq_len):
                index = sequence[i]
                if index != 0:
                    word = self.embeddings.index_to_word[index]
                    vector = self.embeddings.word_to_vec[word]
                    ### Feautures ###
                    pos = self.OneHotEncode(POSTAGS, self.GetPOSTags(word)[1])
                    word_freq = freqs[i]
                    lemma = self.Lemmatize(word)
                    """
                    APPEND FEATURES TO VECTOR HERE
                    """
                    vector.append(pos)
                    vector.append(word_freq)
                    vector.append(self.embeddings.word_to_index[lemma])

                    #Glove, POS, Word_freq, lemmatized wordindex
                    matrix[i] = vector

            list_of_matrices.append(matrix)
        
        list_of_matrices = np.array(list_of_matrices)
        return list_of_matrices

    def GetPOSTags(self, text):
        text = word_tokenize(text)
        return pos_tag(text)

    def OneHotEncode(self, tag_dict, tag):
        one_hot = np.zeros((len(tag_dict), ))
        one_hot[tag_dict[tag]] = 1

        return one_hot

    def NER(self, doc):
        #pos = self.GetPOST(text)
        #return ne_chunk(pos)
        tagged_s = self.GetPOSTags(doc)
        chunked_s = nltk.ne_chunk(tagged_s)
        named_entities={}

        for tree in chunked_s:
            print(tree)
            if hasattr(tree,'label'):
                entity_name = ' '.join(c[0] for c in tree.leaves())
                entity_type = tree.label()
                if entity_name not in named_entities.keys():
                    named_entities[entity_name]=entity_type
        return named_entities

    def word_frequency(self,words):
        word_counts = {}
        for word in words:
            if(word in word_counts.keys()):
                word_counts[word] += 1
            else:
                word_counts[word] = 1
        for key,value in word_counts.items():
            word_counts[key]= value / len(words)

        return word_counts
    
    def get_word_synonyms_from_sent(self, word, sent):
        word_synonyms = []
        for synset in wordnet.synsets(word):
            for lemma in synset.lemma_names():
                if lemma in sent and lemma != word:
                    word_synonyms.append(lemma)

        return word_synonyms

    def exact_match(self, word,question):
        ans = []
        synonym = self.get_word_synonyms_from_sent(word,question) 
        if(word in question): #exact
            ans.append(1)
        else:
            ans.append(0)
        if word.lower() in question: #lower
            ans.append(1)
        else:
            ans.append(0)

        if(len(synonym) > 0): #lemma
            ans.append(1)
        else:
            ans.append(0)
        
        return ans
    def Lemmatize(self, text):
        lemma = WordNetLemmatizer()
        text = text.lower()
        lemma_list = []

        for word_token in word_tokenize(text):
            if word_token in string.punctuation:
                pass
            #yield lemma.lemmatize(word_token) #returns a generator , can only iterate through thhis once
            lemma_list.append(lemma.lemmatize(word_token))
        return lemma_list

e = Embedder(None)
q = 'You could, of course, write your own depth first search'
e.tokenize(q)