#%%
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
#%%[markdown]
## Data Import
data=pd.read_csv("data/apple_one_day_max.csv")
data= data[data['Date'] >= '2010-01-01']
#%%
# information about the data
data.info()

# Na value check
data.isna().sum()


# %% [markdown]

## Plotting the closing price and volume


# Plot the Closing value
plt.figure(figsize=(12, 6))
plt.plot(data['Date'], data['Close'], label='Closing Price')

# Formatting date on x-axis to show years
plt.gca().xaxis.set_major_locator(mdates.YearLocator(2))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.title('Closing Price Over Time')
plt.xlabel('Date')
plt.ylabel('Closing Price')
plt.legend()
plt.show()

# Formatting date on x-axis to show years
plt.gca().xaxis.set_major_locator(mdates.YearLocator(2))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# Creating a second y-axis for Volume
plt.twinx()
plt.bar(data['Date'], data['Volume'], alpha=0.7, color='green', label='Volume')
plt.ylabel('Volume')
plt.legend()

plt.show()

# %%[markdown]
## ADF test

# Here we are going to do ADF test to check whether our data is stationary or not

## Check for stationary 
from statsmodels.tsa.stattools import adfuller

# Augmented Dickey-Fuller test
result = adfuller(data['Close'])

# Print the test statistic and p-value
print(f'Test Statistic: {result[0]}')
print(f'p-value: {result[1]}')
print('Critical Values:')
for key, value in result[4].items():
    print(f'{key}: {value}')

# p value is more than 0.05 which means we cant reject the null hypothesis of the data being non stationary
# This means that data is non-stationary

# %%[markdown]
# Heat map of data
correlation_data = data[['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']]

# Calculate the correlation matrix
correlation_matrix = correlation_data.corr()

# Create a heatmap using Seaborn
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5)
plt.title('Correlation Heatmap')
plt.show()


#%%
####################################
######## Data Preprocessing ########
####################################

#%%
data['Date'] = pd.to_datetime(data['Date'])
data = data.sort_values(by='Date')

# Calculate the differences between consecutive dates
date_diff = data['Date'].diff()

# Check if there are any gaps (missing dates)
if date_diff.eq(pd.Timedelta(days=1)).all():
    print("The dates are continuous.")
else:
    print("There are gaps in the dates.")




#%%[markdown]
# Linear interpolation for numerical columns

data['Date'] = pd.to_datetime(data['Date'], utc=True)
# Create a DataFrame with all dates in the range
date_range = pd.date_range(start=data['Date'].min(), end=data['Date'].max(), freq='D')
all_dates_df = pd.DataFrame({'Date': date_range})

# Merge the original DataFrame with the one containing all dates
merged_data = pd.merge(all_dates_df, data, on='Date', how='left')
# Sort the DataFrame by date
merged_data = merged_data.sort_values(by='Date')

# Linear interpolation for numerical columns
numerical_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
merged_data[numerical_columns] = merged_data[numerical_columns].interpolate(method='linear')

# Print the resulting DataFrame
print(merged_data)
#%%
merged_data.count()
# %%
###############
#### LSTM ####
###############

from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.model_selection import train_test_split
from tensorflow.keras.optimizers import Adam

merged_data.set_index('Date', inplace=True)
merged_data = merged_data.sort_index()
train_size = int(len(merged_data) * 0.95)



# Split the data into training, validation, and test sets
train_data, test_data = train_test_split(merged_data['Close'], test_size=0.05, shuffle=False)
#val_data, test_data = train_test_split(temp, test_size=0.5, shuffle=False)

# %%
# Create sequences for LSTM
def create_sequences(data, sequence_length):
    x, y = [], []
    for i in range(len(data) - sequence_length):
        x.append(data[i:(i + sequence_length)]) ## This appends the previous 2 months
        y.append(data[i + sequence_length])  ## This appends the day after 2 months
        x_combined = np.concatenate([x_sequence, x_prev_90, x_prev_91])
        x.append(x_combined)
    return np.array(x), np.array(y)
## This method helps to basically make y predictions based on the previous 2 months
sequence_length = 90
X_train, y_train = create_sequences(train_data, sequence_length)
#X_val, y_val = create_sequences(val_data, sequence_length)
X_test, y_test = create_sequences(test_data, sequence_length)

#%%
# import datetime
# import pandas as pd
# import numpy as np

# def df_to_windowed_df(dataframe, first_date_str, last_date_str, n=3):
#     def str_to_datetime(date_str):
#         return datetime.datetime.strptime(date_str, '%Y-%m-%d')
    
#     first_date = str_to_datetime(first_date_str)
#     last_date = str_to_datetime(last_date_str)
    
#     target_date = first_date
#     dates, X, Y = [], [], []
    
#     # Convert 'Date' column to datetime without time zone
#     dataframe['Date'] = pd.to_datetime(dataframe['Date']).dt.tz_localize(None)

#     while target_date <= last_date:
#         df_subset = dataframe.loc[dataframe['Date'] <= target_date].tail(n + 1)

#         if len(df_subset) != n + 1:
#             print(f'Error: Window of size {n} is too large for date {target_date}')
#             return

#         values = df_subset['Close'].to_numpy()
#         x, y = values[:-1], values[-1]

#         dates.append(target_date)
#         X.append(x)
#         Y.append(y)

#         next_date = target_date + datetime.timedelta(days=4)

#         target_date = min(next_date, last_date)

#     ret_df = pd.DataFrame({})
#     ret_df['Target Date'] = dates

#     X = np.array(X)
    
#     # Create three columns: 'Target', 'Target-1', and 'Target-2'
#     ret_df['Target'] = Y
#     ret_df['Target-1'] = X[:, 0]  # Assuming 'X[:, 0]' corresponds to the first day in the sequence
#     ret_df['Target-2'] = X[:, 1]  # Assuming 'X[:, 1]' corresponds to the second day in the sequence

#     return ret_df

# # Example usage:
# # Start day second time around: '2021-03-25'
# windowed_df = df_to_windowed_df(merged_data, '2010-01-01', '2023-12-29', n=4)  # Increase n to 4 or any desired value
# print(windowed_df)


# #%%
# def windowed_df_to_date_X_y(windowed_dataframe):
#   df_as_np = windowed_dataframe.to_numpy()

#   dates = df_as_np[:, 0]

#   middle_matrix = df_as_np[:, 1:-1]
#   X = middle_matrix.reshape((len(dates), middle_matrix.shape[1], 1))

#   Y = df_as_np[:, -1]

#   return dates, X.astype(np.float32), Y.astype(np.float32)

# dates, X, y = windowed_df_to_date_X_y(windowed_df)

# dates.shape, X.shape, y.shape

# %%
# Min max scaling
# Use MinMaxScaler to scale the data
scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train.reshape(-1, 1)).reshape(X_train.shape)
y_train_scaled = scaler.fit_transform(y_train.reshape(-1, 1)).reshape(y_train.shape)

#X_val_scaled = scaler.transform(X_val.reshape(-1, 1)).reshape(X_val.shape)
#y_val_scaled = scaler.transform(y_val.reshape(-1, 1)).reshape(y_val.shape)

X_test_scaled = scaler.transform(X_test.reshape(-1, 1)).reshape(X_test.shape)
y_test_scaled = scaler.transform(y_test.reshape(-1, 1)).reshape(y_test.shape)


# %%
from tensorflow.keras.optimizers import Adam
learning_rate = 0.0001  # You can adjust this value
optimizer = Adam(learning_rate=learning_rate)
from tensorflow.keras.layers import Dropout

# Add dropout layers to your model

# Add other LSTM layers with dropout as needed

# Build and train the LSTM model
model = Sequential()
model.add(LSTM(units=200, return_sequences=True, input_shape=(X_train.shape[1], 1)))
model.add(LSTM(units=150,return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(units=100,return_sequences=True))
model.add(LSTM(units=10))
model.add(Dense(units=1,activation='linear'))

model.summary()

# %%

from tensorflow.keras.models import load_model
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping

# Define a ModelCheckpoint callback to save the best model
checkpoint_filepath = 'best_model.h5'
model_checkpoint = ModelCheckpoint(
    filepath=checkpoint_filepath,
    save_best_only=True,
    monitor='val_loss',  
    mode='min',
    verbose=1
)

# Define EarlyStopping callback
early_stopping = EarlyStopping(
    monitor='val_loss',  
    patience=2,  
    restore_best_weights=True,
    verbose=1
)

# Compile and train the model with the callbacks
model.compile(optimizer=optimizer, loss='mean_squared_error')
history = model.fit(
    X_train_scaled, y_train_scaled,
    epochs=20, batch_size=7,
    validation_data=(X_test_scaled, y_test_scaled),
    callbacks=[model_checkpoint, early_stopping]
)

# %%[markdown]
## Results 
# %%
############################
## Evaluation of Results ###
############################


from sklearn.metrics import mean_squared_error
# Load the best model
best_model = load_model(checkpoint_filepath)

# Make predictions on the test set using the best model
best_predictions_scaled = best_model.predict(X_test_scaled)
best_predictions = scaler.inverse_transform(best_predictions_scaled.reshape(-1, 1)).flatten()

# Evaluate the best model on the test set
mse_best_model = mean_squared_error(test_data[sequence_length:], best_predictions.flatten())
print(f'Mean Squared Error on Test Set (Best Model): {mse_best_model}')


# Plot the predictions from the best model against the actual and training values
plt.figure(figsize=(15, 6))

# Plot training data
plt.plot(train_data.index, train_data, label='Train Data', color='green')
#plt.plot(val_data.index, val_data, label='Validation Data', color='purple')

# Plot actual values
plt.plot(test_data.index, test_data, label='Actual', color='blue')

# Plot predicted values from the best model
plt.plot(test_data.index[sequence_length:], best_predictions.flatten(), label='Predicted', color='orange')

plt.title('LSTM Model Predictions vs Actual Values')
plt.xlabel('Date')
plt.ylabel('Closing Price')
plt.legend()
plt.show()
#%%
plt.figure(figsize=(15, 6))

# Plot actual values
plt.plot(test_data.index[sequence_length:], test_data[sequence_length:], label='Actual', color='blue')

# Plot predicted values from the best model
plt.plot(test_data.index[sequence_length:], best_predictions.flatten(), label='Predicted', color='orange')

plt.title('LSTM Model Predictions vs Actual Values')
plt.xlabel('Date')
plt.ylabel('Closing Price')
plt.legend()
plt.show()
#%%
from sklearn.metrics import mean_absolute_error, mean_squared_error

mae_best_model = mean_absolute_error(test_data[sequence_length:], best_predictions.flatten())
rmse_best_model = np.sqrt(mse_best_model)

print(f'Mean Absolute Error on Test Set (Best Model): {mae_best_model}')
print(f'Root Mean Squared Error on Test Set (Best Model): {rmse_best_model}')
#%%
## Gradient Descent
# Plot the training curve
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()



#%%

###########################################
############# FORECASTING #################
###########################################

#%%

# Define the number of future time steps to forecast
import numpy as np

# Define the number of future time steps to forecast
num_forecast_steps = 181  # Adjust this according to your needs

# Determine the start date for the future forecast
start_date = test_data.index[-1] - pd.Timedelta(days=129)  # Previous 90 days

# Create sequences for future dates within the new date range
future_dates = pd.date_range(start=start_date + pd.Timedelta(days=1), periods=num_forecast_steps, freq='B')

future_data = pd.Series(index=future_dates)

# Create a Series with random values for the new date range
np.random.seed(42)  # Set a seed for reproducibility
future_data_values = np.random.uniform(low=192, high=200, size=num_forecast_steps)  # Adjust the range as needed
future_data = pd.Series(data=future_data_values, index=future_dates)


# Print the filled future_data
print(future_data)


#%%

X_future, _ = create_sequences(future_data, sequence_length)

# Min-max scaling for the future data
X_future_scaled = scaler.transform(X_future.reshape(-1, 1)).reshape(X_future.shape)

# Make predictions using the best model
future_predictions_scaled = best_model.predict(X_future_scaled)
future_predictions = scaler.inverse_transform(future_predictions_scaled.reshape(-1, 1)).flatten()

# Plot the predictions for the future
plt.figure(figsize=(15, 6))
#plt.plot(train_data.index, train_data, label='Train Data', color='green')

# Plot actual values
plt.plot(test_data.index, test_data, label='Actual', color='blue')

# Plot predicted values for the test set
plt.plot(test_data.index[sequence_length:], best_predictions.flatten(), label='Predicted (Test Set)', color='orange')

# Plot predicted values for the future
plt.plot(future_dates[sequence_length:], future_predictions, label='Forecast', color='red', linestyle='dashed')

plt.title('LSTM Model Predictions and Forecast')
plt.xlabel('Date')
plt.ylabel('Closing Price')
plt.legend()
plt.show()

#%%
pd.DataFrame(future_predictions,columns=['Closing Price'],index=future_data.index[sequence_length:])


# %%