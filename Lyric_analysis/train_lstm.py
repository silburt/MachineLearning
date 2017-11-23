import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.callbacks import ModelCheckpoint
from keras.utils import np_utils
import tensorflow as tf

def train_model(genre,dir_model,epochs,seq_length):
    sess = tf.Session(config=tf.ConfigProto(log_device_placement=True)) #check gpu is being used
    
    X = np.load('playlists/%s/X_sl%d.npy'%(genre,seq_length))
    y = np.load('playlists/%s/y_sl%d.npy'%(genre,seq_length))
    
    model = Sequential()
    model.add(LSTM(1024, return_sequences=True, input_shape=(X.shape[1], X.shape[2])))
    model.add(Dropout(0.2))
    model.add(LSTM(1024, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(y.shape[1], activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam')
    checkpoint = ModelCheckpoint(dir_model, monitor='loss', verbose=1, save_best_only=True, mode='min')
    callbacks_list = [checkpoint]
    
    model.fit(X, y, epochs=epochs, batch_size=128, callbacks=callbacks_list)#, validation_split=0.2)
    model.save(dir_model)

if __name__ == '__main__':
    genre = 'country'
    seq_length = 200
    epochs = 60
    dir_model = 'models/%s_novalid_lstm1024.h5'%genre
    
    train_model(genre,dir_model,epochs,seq_length)



