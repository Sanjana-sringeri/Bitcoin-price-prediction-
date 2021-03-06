# -*- coding: utf-8 -*-
"""Ml Mini Project Final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1jH3jZ9BPDutZ61SDoU9tsTVJfQtdMMqR
"""

! pip install -q kaggle

from google.colab import files

files.upload()

! mkdir ~/.kaggle

! cp kaggle.json ~/.kaggle/

! chmod 600 ~/.kaggle/kaggle.json

! kaggle datasets list

! kaggle datasets download -d mczielinski/bitcoin-historical-data

! mkdir bitcoin

! unzip bitcoin-historical-data.zip -d bitcoin

cd /content/bitcoin/

import pandas as pd
df = pd.read_csv("bitstampUSD_1-min_data_2012-01-01_to_2021-03-31.csv")

df.head()

df.info()

df.columns

df.isnull().sum()

df = df.dropna()
df.head()

df['date'] = pd.to_datetime(df['Timestamp'],unit='s').dt.date
group = df.groupby('date')
real_price = group['Weighted_Price'].mean()

real_price

df.info()

df.corr()

df.describe()

import numpy as np
import matplotlib.pyplot as plt
import math
import seaborn as sns
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

pd.set_option('display.float_format', lambda x: '%.3f' % x)

f,ax = plt.subplots(figsize=(9, 9))
sns.heatmap(df.corr(), annot=True, linewidths=0.75, fmt= '.1f',ax=ax)
plt.show()

df.Weighted_Price.plot(kind = "line", color = "red", label = "Weighted_Price",linewidth=1,alpha=0.5,grid=True,linestyle=':')

plt.legend(loc="upper right")   
plt.xlabel("x axis")            
plt.ylabel("y axis")           
plt.title("Line Plot for Weighted_Price") 

plt.show()

df.plot(kind='scatter', x='Volume_(BTC)', y='Volume_(Currency)',alpha = 0.5,color = 'red')
plt.xlabel('BTC')              
plt.ylabel('Currency')
plt.title('Scatter Plot of the BTC_Currency')
plt.show()

#Histogram
# bins = number of bar in figure
df.Weighted_Price.plot(kind = 'hist',bins = 50,figsize = (9,9), color='red')
plt.show()

bins = np.linspace(200, 2000, 100)
plt.hist(df.High, bins, alpha=1, density=True, color = 'red')
plt.hist(df.High, bins, alpha=1, density=True, color = 'red')
plt.legend(loc='upper right')
plt.title("High price")
plt.xlabel("Amount")
plt.ylabel("Percentage of increasing")
plt.show()

# split data
prediction_days = 90
df_train=real_price[:len(real_price)-prediction_days]
df_test=real_price[len(real_price)-prediction_days:]

# Data preprocess
training_set = df_train.values
training_set = np.reshape(training_set, (len(training_set), 1))

testing_set = df_test.values
testing_set = np.reshape(testing_set, (len(testing_set), 1))

from sklearn.preprocessing import MinMaxScaler
sc = MinMaxScaler()
training_set = sc.fit_transform(training_set)
X_train = training_set[0:len(training_set)-1]
y_train = training_set[1:len(training_set)]
X_train = np.reshape(X_train, (len(X_train), 1, 1))

X_test = testing_set[0:len(testing_set)-1]
y_test = testing_set[1:len(testing_set)]
X_test = np.reshape(X_test, (len(X_test), 1, 1))

# Here I start cleaning the data. Firstly, converting Timestamp to datetime64
df.Timestamp = pd.to_datetime(df.Timestamp)
df.index = df.Timestamp
A = df
size = int(len(A) * 0.7)
data_train, data_test = A[0:size], A[size:len(A)]

# a method to create a variety of features from a time series df
def create_features(df, label=None):
    df['date'] = df.index
    df['hour'] = df['date'].dt.hour
    df['dayofweek'] = df['date'].dt.dayofweek
    df['quarter'] = df['date'].dt.quarter
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    df['dayofyear'] = df['date'].dt.dayofyear
    df['dayofmonth'] = df['date'].dt.day
    df['weekofyear'] = df['date'].dt.weekofyear
    A = df[['hour','dayofweek','quarter','month','year',
           'dayofyear','dayofmonth','weekofyear']]
    if label:
        b = df[label]
        return A, b
    return A

# assigning training and testing, features and labels (price)
A_train, b_train = create_features(data_train, label='Weighted_Price')
A_test, b_test = create_features(data_test, label='Weighted_Price')

from sklearn.ensemble import RandomForestRegressor

model_rf = RandomForestRegressor(max_depth = 3, n_estimators = 75)
model_rf.fit(A_train, b_train)
data_test['Weighted_Price_Prediction_rf'] = model_rf.predict(A_test)
data_all = pd.concat([data_test, data_train], sort=False)
data_all[['Weighted_Price','Weighted_Price_Prediction_rf']].plot(figsize=(15, 5))

#Finding the RMSE of the Random forest
from sklearn.metrics import mean_squared_error, mean_absolute_error
rmse_rf = np.sqrt(mean_squared_error(data_test['Weighted_Price'], data_test['Weighted_Price_Prediction_rf']))
print('Test RMSE: %.3f' % rmse_rf)

#Finding the mean absolute error of Random forest
mean_abs_rf = mean_absolute_error(data_test['Weighted_Price'], data_test['Weighted_Price_Prediction_rf'])
print('Test RMSE: %.3f' % mean_abs_rf)

import xgboost as xgb
from xgboost import plot_importance, plot_tree
model_xgb =  xgb.XGBRegressor(objective ='reg:linear',min_child_weight=10, booster='gbtree', colsample_bytree = 0.3, learning_rate = 0.1,
                max_depth = 5, alpha = 10, n_estimators = 100)
model_xgb.fit(A_train, b_train, eval_set=[(A_train, b_train), (A_test, b_test)], early_stopping_rounds=50, verbose=False)

# assign predictions to data_test and then data_all
data_test['Weighted_Price_Prediction'] = model_xgb.predict(A_test)
data_all = pd.concat([data_test, data_train], sort=False)

data_all[['Weighted_Price','Weighted_Price_Prediction']].plot(figsize=(15, 5))

#Finding the RMSE of the XGBoost
from sklearn.metrics import mean_squared_error, mean_absolute_error
rmse_xgb = np.sqrt(mean_squared_error(data_test['Weighted_Price'], data_test['Weighted_Price_Prediction']))
print('Test RMSE: %.3f' % rmse_xgb)

#Finding the mean absolute error of XGBoost
mean_abs_xgb = mean_absolute_error(data_test['Weighted_Price'], data_test['Weighted_Price_Prediction'])
print('Test RMSE: %.3f' % mean_abs_xgb)

### Importing the Keras libraries and packages
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import SimpleRNN
from keras.layers import Dropout

# Initialising the RNN
model_rnn = Sequential()

# Adding the first RNN layer and some Dropout regularisation
model_rnn.add(SimpleRNN(units = 50,activation='relu', return_sequences = True, input_shape = (X_train.shape[1], 1)))
model_rnn.add(Dropout(0.2))

model_rnn.add(SimpleRNN(units = 50,activation='relu', return_sequences = True))
model_rnn.add(Dropout(0.2))

model_rnn.add(SimpleRNN(units = 50,activation='relu', return_sequences = True))
model_rnn.add(Dropout(0.2))

model_rnn.add(SimpleRNN(units = 50))
model_rnn.add(Dropout(0.2))

model_rnn.add(Dense(units = 7))

# Compiling the RNN
model_rnn.compile(optimizer = 'adam', loss = 'mean_squared_error')

# Fitting the RNN to the Training set
model_rnn.fit(X_train, y_train, epochs = 100, batch_size = 32)

# Making the predictions
test_set_rnn = df_test.values
inputs_rnn = np.reshape(test_set_rnn, (len(test_set_rnn), 1))
inputs_rnn = sc.transform(inputs_rnn)
inputs_rnn = np.reshape(inputs_rnn, (len(inputs_rnn), 1))
predicted_btc_price = model_rnn.predict(inputs_rnn)
predicted_btc_price = sc.inverse_transform(predicted_btc_price)

#Prediction plot
plt.figure(figsize = (20,7))
plt.plot(test_set_rnn)
plt.plot(predicted_btc_price)
plt.xlabel('Time')
plt.ylabel('Price')
plt.title('Closing Price vs Time')
plt.legend(['Actual price', 'Predicted price'])
plt.show()

#Finding the RMSE value
predicted_btc_price = np.reshape(inputs_rnn, (len(predicted_btc_price), 1))
from sklearn.metrics import mean_squared_error, mean_absolute_error
rmse_rnn = np.sqrt(mean_squared_error(test_set_rnn, predicted_btc_price))
print('Test RMSE: %.3f' % rmse_rnn)

#Finding the mean absolute error 
mean_abs_rnn = mean_absolute_error(test_set_rnn, predicted_btc_price)
print('Test RMSE: %.3f' % mean_abs_rnn)

#for lstm
# Importing the Keras libraries and packages
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM

# Initialising the LSTM
model_lstm = Sequential()

# Adding the input layer and the LSTM layer
model_lstm.add(LSTM(units = 10, activation = 'relu', input_shape = (None, 1)))

# Adding the output layer
model_lstm.add(Dense(units = 1))

# Compiling the LSTM
model_lstm.compile(loss=["mse","mae"], loss_weights=[1,1], optimizer = 'adam',)

# Fitting the LSTM to the Training set
history = model_lstm.fit(X_train, y_train, batch_size = 32, epochs = 100)

# Making the predictions
test_set_lstm = df_test.values
inputs_lstm = np.reshape(test_set_lstm, (len(test_set_lstm), 1))
inputs_lstm = sc.transform(inputs_lstm)
inputs_lstm = np.reshape(inputs_lstm, (len(inputs_lstm), 1))
predicted_BTC_price = model_lstm.predict(inputs_lstm)
predicted_BTC_price = sc.inverse_transform(predicted_BTC_price)

#Prediction plot
plt.figure(figsize = (20,7))
plt.plot(test_set_lstm)
plt.plot(predicted_BTC_price)
plt.xlabel('Time')
plt.ylabel('Price')
plt.title('Closing Price vs Time')
plt.legend(['Actual price', 'Predicted price'])
plt.show()

#Plot of the model evaluation
plt.figure(figsize=(15,5))
plt.plot(history.history['loss'])
plt.title("The model's evaluation", fontsize=14)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.show()

import matplotlib.pyplot as plt
pd.DataFrame(history.history).plot(figsize=(8, 5))
plt.grid(True)
plt.gca().set_ylim(-10, 100)
plt.show()

#calculate MSE and MAE
from sklearn.metrics import mean_squared_error, mean_absolute_error
rmse_lstm = np.sqrt(mean_squared_error(test_set_lstm, predicted_BTC_price))
print('Test RMSE: %.3f' % rmse_lstm)

mean_abs_lstm = mean_absolute_error(test_set_lstm, predicted_BTC_price)
print('MAE: %.3f' %mean_abs_lstm)

# Final graph for the RMSE's of each model
fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
modelz = ['Random Forest', 'XGBoost', 'RNN', 'LSTM']
nums = [rmse_rf, rmse_xgb, rmse_rnn, rmse_lstm]
ax.bar(modelz,nums)
plt.xlabel('Models')
plt.ylabel('RMSE')
plt.title('RMSE of the Models')
plt.gca().set_ylim(100,60000)
plt.show()
plt.show()

# Final graph for the mean absolute error's of each model
fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
modelz = [ 'RandomForest','XGBoost', 'RNN', 'LSTM']
nums = [mean_abs_rf, mean_abs_xgb, mean_abs_rnn, mean_abs_lstm ]
ax.bar(modelz,nums)
plt.xlabel('Models')
plt.ylabel('MAE')
plt.title('Mean absolute error of the Models')
plt.gca().set_ylim(100,60000)
plt.show()
plt.show()