import numpy as np
import pandas as pd
from keras.layers.convolutional import Conv1D,MaxPooling1D
from keras.layers import Flatten,SpatialDropout1D
from gensim import corpora
from keras import optimizers
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
from keras.preprocessing import sequence
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers import Dense, Embedding

np.random.seed(0)

if __name__ == "__main__":

    # load data
    train_df = pd.read_csv('train.tsv', sep='\t', header=0)
    test_df = pd.read_csv('test.tsv', sep='\t', header=0)

    raw_docs_train = train_df['Phrase'].values
    raw_docs_test = test_df['Phrase'].values
    sentiment_train = train_df['Sentiment'].values
    num_labels = len(np.unique(sentiment_train))

    # text pre-processing
    stop_words = set(stopwords.words('english'))
    stop_words.update(['.', ',', '"', "'", ':', ';', '(', ')', '[', ']', '{', '}'])
    stemmer = SnowballStemmer('english')

    print("pre-processing train docs...")
    processed_docs_train = []
    for doc in raw_docs_train:
        tokens = word_tokenize(doc)
        filtered = [word for word in tokens if word not in stop_words]
        stemmed = [stemmer.stem(word) for word in filtered]
        processed_docs_train.append(stemmed)

    print("pre-processing test docs...")
    processed_docs_test = []
    for doc in raw_docs_test:
        tokens = word_tokenize(doc)
        filtered = [word for word in tokens if word not in stop_words]
        stemmed = [stemmer.stem(word) for word in filtered]
        processed_docs_test.append(stemmed)

    processed_docs_all = np.concatenate((processed_docs_train, processed_docs_test), axis=0)

    dictionary = corpora.Dictionary(processed_docs_all)
    dictionary_size = len(dictionary.keys())
    print("dictionary size: ", dictionary_size)

    print("converting to token ids...")
    word_id_train, word_id_len = [], []
    for doc in processed_docs_train:
        word_ids = [dictionary.token2id[word] for word in doc]
        word_id_train.append(word_ids)
        word_id_len.append(len(word_ids))

    word_id_test, word_ids = [], []
    for doc in processed_docs_test:
        word_ids = [dictionary.token2id[word] for word in doc]
        word_id_test.append(word_ids)
        word_id_len.append(len(word_ids))

    seq_len = np.round((np.mean(word_id_len) + 2 * np.std(word_id_len))).astype(int)

    # pad sequences
    word_id_train = sequence.pad_sequences(np.array(word_id_train), maxlen=seq_len)
    word_id_test = sequence.pad_sequences(np.array(word_id_test), maxlen=seq_len)
    y_train_enc = np_utils.to_categorical(sentiment_train, num_labels)

    # CNN
    print("fitting CNN ...")
    model = Sequential()
    model.add(Embedding(dictionary_size, 128, dropout=0.2,input_length=seq_len))
    model.add(SpatialDropout1D(0.2))

    model.add(Conv1D(32, kernel_size=3, padding='same', activation='relu'))
    model.add(MaxPooling1D(pool_size=2))

    model.add(Conv1D(64, kernel_size=3, padding='same', activation='relu'))
    model.add(MaxPooling1D(pool_size=2))

    model.add(Flatten())
    model.add(Dense(num_labels,activation='sigmoid'))
    print(model.summary())
    hist = model.compile(loss='categorical_crossentropy', optimizer=optimizers.RMSprop(lr=0.001), metrics=['accuracy'])
    hist = model.fit(word_id_train, y_train_enc, nb_epoch=5, batch_size=256, verbose=1)

    test_pred = model.predict_classes(word_id_test)

    print(hist.history.get('acc')[-1])
    # save to disk
    model2_json = model.to_json()
    with open('model2.json', 'w') as json_file:
        json_file.write(model2_json)
    model.save_weights('model2.h5')
