#https://danijar.com/tips-for-training-recurrent-neural-networks/
#https://github.com/keras-team/keras/blob/master/examples/lstm_text_generation.py - apparently this works...
#https://github.com/0xnurl/keras_character_based_ner/tree/master/src
#https://github.com/keras-team/keras/issues/197 - a lot of good stuff in here.
#https://github.com/mineshmathew/char_rnn_karpathy_keras/blob/master/char_rnn_of_karpathy_keras.py - suggested replacement network
#https://github.com/yxtay/char-rnn-text-generation/blob/master/keras_model.py - suggested replacement network

#https://groups.google.com/d/msg/keras-users/Y_FG_YEkjXs/QGC58mGHiU8J
# Reason not to use embedding layer for char-RNN - Yes: we want the output to be a probability distribution over characters. If each character was encoded by a dense vector learned with an Embedding layer, then output sampling would become a K-nearest neighbors problem over the embedding space, which would be much more complex to deal with than a dictionary lookup. But, if you're only using the embedding for the input but you're mapping the output with a simple dictionary, then you'll be fine (i.e. your output is still a probability distribution over characters).

# overfitting discussion - https://stats.stackexchange.com/questions/181/how-to-choose-the-number-of-hidden-layers-and-nodes-in-a-feedforward-neural-netw

# reminder: accuracy metrics don't feed into training, they are strictly outputs to gauge overall performance. Only losses actually control training of the network. Dropout can also cause training loss to be higher than validation loss. Dropout is generally not used when calculating validation loss.

# sanity check: http://cs231n.github.io/neural-networks-3/#sanitycheck

import numpy as np
from keras.models import Sequential
from keras.layers import Dense, LSTM, GRU, Embedding, TimeDistributed
from keras.metrics import categorical_accuracy
from keras.optimizers import Adam, RMSprop
from keras.callbacks import ModelCheckpoint, EarlyStopping
from keras.models import load_model
from keras import backend as K
from sklearn.model_selection import train_test_split
import tensorflow as tf
import sys

# one-hot encode on the fly, saves tons of memory
def one_hot_gen(X, Y, vocab_size, seq_length, batch_size=64):
    while True:
        for i in range(0, len(X), batch_size):
            x, y = X[i:i+batch_size].copy(), Y[i:i+batch_size].copy()
            x = np.eye(vocab_size)[x]
            y = np.eye(vocab_size)[y]
            yield (x, y)

# main routine
def train_model(genre, dir_model, MP):
    sess = tf.Session(config=tf.ConfigProto(log_device_placement=True)) #check gpu is being used
    
    batch_size = MP['bs']
    lstm_size = MP['lstm_size']
    seq_length = MP['seq_length']
    drop = MP['dropout']
    lr = MP['lr']
    epochs = MP['epochs']
    
    text_to_int, int_to_text, n_chars = np.load('playlists/%s/ancillary_char.npy'%genre)
    vocab_size = len(text_to_int)
    X = np.load('playlists/%s/X_sl%d_char.npy'%(genre, seq_length))
    y = np.load('playlists/%s/y_sl%d_char.npy'%(genre, seq_length))

    # randomly shuffle samples before test/valid split
    np.random.seed(40)
    ran = [i for i in range(len(X))]
    np.random.shuffle(ran)
    
    X_train, X_valid, y_train, y_valid = train_test_split(X[ran], y[ran], test_size=0.2, random_state=42)

    try:
        model = load_model(dir_model)
        print("successfully loaded previous model, continuing to train")
    except:
        print("generating new model")
        model = Sequential()
        model.add(GRU(lstm_size, dropout=drop, recurrent_dropout=drop, return_sequences=True,
                      input_shape=(seq_length, vocab_size)))
        for i in range(MP['n_layers'] - 1):
            model.add(GRU(lstm_size, dropout=drop, recurrent_dropout=drop, return_sequences=True))
        model.add(TimeDistributed(Dense(vocab_size, activation='softmax'))) #output shape=(bs, sl, vocab)

        decay = 0.5*lr/epochs
        optimizer = Adam(lr=lr, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=decay, clipvalue=1)
        #optimizer = RMSprop(lr=lr, decay=decay)
        model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['categorical_accuracy'])
    print(model.summary())

    # callbacks
    checkpoint = ModelCheckpoint(dir_model, monitor='loss', save_best_only=True, mode='min')
    #earlystop = EarlyStopping(monitor='val_loss', min_delta=0.01, patience=3)
    callbacks_list = [checkpoint]

    # train
    model.fit_generator(one_hot_gen(X_train, y_train, vocab_size, seq_length, batch_size),
                        steps_per_epoch=len(X_train)/batch_size, epochs=epochs, callbacks=callbacks_list,
                        validation_data=one_hot_gen(X_valid, y_valid, vocab_size, seq_length, batch_size),
                        validation_steps=len(X_valid)/batch_size)
    model.save(dir_model)

if __name__ == '__main__':
    genre = sys.argv[1]
    
    # model parameters
    MP = {}
    MP['seq_length'] = 150              # sequence length
    MP['n_layers'] = int(sys.argv[2])   # number of lstm layers
    MP['lstm_size'] = int(sys.argv[3])  # lstm size
    MP['bs'] = int(sys.argv[4])         # batch size
    MP['dropout'] = float(sys.argv[5])  # dropout fraction
    MP['lr'] = 1e-3                     # learning rate
    MP['epochs'] = 60                   # n_epochs
    
    dir_model = 'models/%s_sl150_nl%d_size%d_bs%d_drop%.1f.h5'%(genre, MP['n_layers'],
                                                                MP['lstm_size'], MP['bs'],
                                                                MP['dropout'])
    train_model(genre, dir_model, MP)
