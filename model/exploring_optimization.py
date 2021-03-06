#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Code cells I used to explore optimizing my FB-reaction-prediction model.

Disorganized rapid exploration code - what worked was incorporated into 
model_fb_reactions.

Created on Sun Oct  2 16:03:30 2016

@author: dsaunder
"""

##%%
#from nltk.stem.porter import PorterStemmer
#
#porter = PorterStemmer()
#
#def tokenizer(text):
#    return text.split()
#def tokenizer_porter(text):
#    return [porter.stem(word) for word in text.split()]
#
#%%
def tokenizer(text):
    tokenized = [w for w in text.split() if w not in stop]
    return tokenized
def plot_feature_importance(features, fitted_forest):
    plt.figure()
    vals = fitted_forest.feature_importances_
    sortorder = np.flipud(np.argsort(vals))
    features = np.array(features)
    with sns.axes_style("whitegrid"):
        sns.stripplot(y=features[sortorder], x=vals[sortorder], orient="h", color='red', size=10)
    xl = plt.xlim()
    plt.xlim(0,xl[1])
    plt.grid(axis='y',linestyle=':')
    plt.xlabel('Feature importance score')

def print_feature_importances(clf):
    ordering = np.argsort(clf.feature_importances_)
    ordering = ordering[::-1]
    words = [revocab[a] for a in ordering]
    for i in range(20):
        print "%.2f\t%s" % (clf.feature_importances_[ordering[i]], words[i])

        
from sklearn.ensemble import RandomForestRegressor
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
stop = stopwords.words('english')
from sqlalchemy import create_engine
from sklearn import preprocessing
from sklearn import cross_validation


dbname = 'frontpage'
username = 'dsaunder'
# prepare for database
engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))

sql_query = 'SELECT * FROM fb_statuses;'
fb = pd.read_sql_query(sql_query,engine)


#%%
# Random forest with a binary outcome
# Compute the proportion angry/sad/controversial
fb.loc[:,'prop_angry'] = fb.num_angries/fb.num_reactions
fb.loc[:,'prop_sad'] = fb.num_sads/fb.num_reactions
fb.loc[:,'prop_contro'] = fb.num_comments/fb.num_reactions
# Add src
sql_query = 'SELECT * FROM srcs;'
srcs = pd.read_sql_query(sql_query,engine)
src_lookup = {a.prefix:a.loc['index'] for i,a in srcs.iterrows()}
src_code = fb.src.map(src_lookup)
revocab[X.shape[1]]= 'SOURCE'
src_matrix = scipy.sparse.csr.csr_matrix(src_code.values.reshape(-1,1))
X_with_src = hstack((X, src_matrix))

y_binary = fb.prop_angry > 0
from sklearn.ensemble import RandomForestClassifier
clf = RandomForestClassifier(n_estimators=150, n_jobs=-1, verbose=1)
cv = cross_validation.KFold(X_with_src.shape[0], n_folds=3, shuffle=True, random_state=0)
scores = cross_validation.cross_val_score( clf, X_with_src, y_binary, cv=cv, n_jobs=-1, scoring='f1')
print np.mean(scores)

clf.fit(X,y_binary)

print_feature_importances(clf)


e#%%
# Compare proportion angry across news sources 
g = sns.FacetGrid(fb.loc[fb.src.isin(['fox','cnn','nbc']),:], row="src")
g.map(sns.distplot,'prop_angry')

#%%
# Attempt at naive bayesian on classification data

from sklearn.naive_bayes import GaussianNB
gnb = GaussianNB()
gnb.fit(X.toarray(),y_binary)

scores = cross_validation.cross_val_score( gnb, X.toarray(), y_binary, cv=5, n_jobs=-1)

#print gnb.score(X.toarray(),y_binary)s

#%%
# Distribution of angry reactions
plt.figure()
plt.subplot(1,2,1)
sns.set(font_scale=1.5)
sns.distplot(fb.prop_angry,kde=False, color='purple')
plt.xlabel('Proportion of "Angry" reactions')
plt.tight_layout()


plt.subplot(1,2,2)

sns.set(font_scale=1.5)
sns.distplot(np.log(fb.prop_angry+0.01),kde=False, color='orange')
plt.xlabel('Log proportion of "Angry" reactions')
plt.tight_layout()

#%%
# Random forest regression with different root transforms

y_root = fb.prop_angry# ** (1/4.)
y_root = y_root[y_root > 0]
y_root = np.log(y_root)
X_root = X_with_src[np.where(fb.prop_angry)[0],:]
from sklearn.linear_model import LinearRegression
#clf = LinearRegression()
clf = RandomForestRegressor(n_estimators=15, n_jobs=-1, verbose=1)

cv = cross_validation.KFold(X_root.shape[0], n_folds=5, shuffle=True, random_state=0)
scores = cross_validation.cross_val_score( clf, X_root, y_root, cv=cv, n_jobs=-1, scoring='r2', verbose=1)
print np.mean(scores)
y_cv = cross_validation.cross_val_predict( clf, X_root, y_root, cv=cv, n_jobs=-1, verbose=1)
plt.figure()
sns.regplot(y_root,y_cv)


#%%
############
# Begin second exploring Word2Vec representations of headlines.

start = time.time()
model = Word2Vec.load_word2vec_format('~/GoogleNews-vectors-negative300.bin', binary= True)
print (time.time()-start)/60.
#%%
def headline_to_vector(headline, size):
    vec = np.zeros(size).reshape((1, size))
    count = 0
    # Remove punctuation
    headline = re.sub('[%s]' % re.escape(string.punctuation),'', headline)

    # For each word, if it's found in either lower case or upper case add it
    words = headline.split()
    for word in words:
        upper = word
        upper = upper[0].upper() + upper[1:]
        try:
            vec += model[upper].reshape((1, size))
            count+=1.
            print upper
        except KeyError:
            pass

        lower = word
        lower = lower[0].lower() + lower[1:]
        try:
            vec += model[lower].reshape((1, size))
            count+=1.
            print lower
        except KeyError:
            pass
    if count != 0:
        vec /= count
    return vec
#%%
def headline_to_vector_list(headline, size):
    vecs = []

    headline = re.sub('[%s]' % re.escape(string.punctuation),'', headline)
    words = headline.split()
    for word in words:
        upper = word
        upper = upper[0].upper() + upper[1:]
        try:
            vecs.append(model[upper])
        except KeyError:
            pass

        lower = word
        lower = lower[0].lower() + lower[1:]
        try:
            vecs.append(model[lower])
        except KeyError:
            pass
    return vecs


    #%%
regex = re.compile('[%s]' % re.escape(string.punctuation))
out = headline.translate(string.maketrans("",""), string.punctuation)
re.sub(re.escape(string.punctuation),'', headline)
#%%
wordvecs = np.zeros([len(fb),300])
for i,headline in tqdm.tqdm(enumerate(fb.link_name)):
    print headline
    wordvecs[i,:] = headline_to_vector(headline, 300)

#%%
from sklearn.manifold import TSNE
tsne_model = TSNE(n_components=2, random_state=0)
projected = model.fit_transform(wordvecs)
#%%
plt.figure()
plt.plot(projected[np.where(y_binary),0].squeeze(), projected[np.where(y_binary),1].squeeze(), '.')
plt.plot(projected[np.where(np.invert(y_binary)),0].squeeze(), projected[np.where(np.invert(y_binary)),1].squeeze(),'.')

#%%
from sklearn.linear_model import SGDClassifier



lr = SGDClassifier(loss='log', penalty='l1')


lr.fit(wordvecs, y_binary)


#%%
# Use the word vectors for scoring
from sklearn.ensemble import RandomForestRegressor

forest = RandomForestRegressor(n_estimators=15, n_jobs=-1)
forest.fit(wordvecs, y)

cv = cross_validation.KFold(wordvecs.shape[0], n_folds=3, shuffle=True, random_state=0)
scores = cross_validation.cross_val_score( forest, wordvecs, y, cv=cv, n_jobs=-1)
y_cv = cross_validation.cross_val_predict( forest, wordvecs, y, cv=cv, n_jobs=-1)


#%%
all_vecs = []
wordvecs = np.zeros([len(fb),300])
for i,headline in tqdm.tqdm(enumerate(fb.link_name)):
    all_vecs.extend(headline_to_vector_list(headline, 300))

# Set "k" (num_clusters) to be 1/5th of the vocabulary size, or an
# average of 5 words per cluster
num_clusters = len(all_vecs)/10

#%%
from sklearn.cluster import KMeans
import time
start = time.time() # Start time

# Initalize a k-means object and use it to extract centroids
kmeans_clustering = KMeans( n_clusters = num_clusters, n_jobs=-1, verbose=1)
idx = kmeans_clustering.fit_predict( all_vecs )

# Get the end time and print how long the process took
end = time.time()
elapsed = end - start
print "Time taken for K Means clustering: ", elapsed, "seconds."




#%%
size= 400
import gensim
LabeledSentence = gensim.models.doc2vec.LabeledSentence

#Do some very minor text preprocessing
def cleanText(corpus):
    punctuation = """.,?!:;(){}[]"""
    corpus = [z.lower().replace('\n','') for z in corpus]
    corpus = [z.replace('<br />', ' ') for z in corpus]

    #treat punctuation as individual words
    for c in punctuation:
        corpus = [z.replace(c, ' %s '%c) for z in corpus]
    corpus = [z.split() for z in corpus]
    return corpus

x_train = cleanText(fb.link_name)
x_test = cleanText(fb_test.link_name)

def labelizeReviews(reviews, label_type):
    labelized = []
    for i,v in enumerate(reviews):
        label = '%s_%s'%(label_type,i)
        labelized.append(LabeledSentence(v, [label]))
    return labelized

x_train = labelizeReviews(x_train, 'TRAIN')
x_test = labelizeReviews(x_test, 'TEST')

model_dm = gensim.models.Doc2Vec(min_count=1, window=10, size=size, sample=1e-3, negative=5, workers=3)
model_dbow = gensim.models.Doc2Vec(min_count=1, window=10, size=size, sample=1e-3, negative=5, dm=0, workers=3)

#%%
model_dm.build_vocab(np.concatenate((x_train, x_test)))
model_dbow.build_vocab(np.concatenate((x_train, x_test)))

#We pass through the data set multiple times, shuffling the training reviews each time to improve accuracy.
all_train_reviews = np.concatenate((x_train))
for epoch in range(10):
    perm = np.random.permutation(all_train_reviews.shape[0])
    model_dm.train(all_train_reviews[perm])
    model_dbow.train(all_train_reviews[perm])

#Get training set vectors from our models
def getVecs(model, corpus, size):
    vecs = [np.array(model[z.labels[0]]).reshape((1, size)) for z in corpus]
    return np.concatenate(vecs)

#%%
#

model_dm = gensim.models.Doc2Vec(min_count=1, window=10, size=size, sample=1e-3, negative=5, workers=3)



import random

size = 400

#instantiate our DM and DBOW models
model_dm = gensim.models.Doc2Vec(min_count=1, window=10, size=size, sample=1e-3, negative=5, workers=3)
model_dbow = gensim.models.Doc2Vec(min_count=1, window=10, size=size, sample=1e-3, negative=5, dm=0, workers=3)

#build vocab over all reviews
model_dm.build_vocab(np.concatenate((x_train, x_test, unsup_reviews)))
model_dbow.build_vocab(np.concatenate((x_train, x_test, unsup_reviews)))

#We pass through the data set multiple times, shuffling the training reviews each time to improve accuracy.
all_train_reviews = np.concatenate((x_train, unsup_reviews))
for epoch in range(10):
    perm = np.random.permutation(all_train_reviews.shape[0])
    model_dm.train(all_train_reviews[perm])
    model_dbow.train(all_train_reviews[perm])

#Get training set vectors from our models
def getVecs(model, corpus, size):
    vecs = [np.array(model[z.labels[0]]).reshape((1, size)) for z in corpus]
    return np.concatenate(vecs)

train_vecs_dm = getVecs(model_dm, x_train, size)
train_vecs_dbow = getVecs(model_dbow, x_train, size)

train_vecs = np.hstack((train_vecs_dm, train_vecs_dbow))
