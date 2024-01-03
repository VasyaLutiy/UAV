
import plotly.io as pio
import plotly.express as px
import plotly.offline as py
import plotly.graph_objects as go

import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd

class DataTransform:
  
  def __init__(self, MydataFrame):    
    global TIMESTEPS
    global CHECKLEN
    self.MydataFrame = MydataFrame

  def create_MySeries_aggData(self):    
    
    mav_cols  = ['mav_roll', 'mav_pitch', 'mav_acc_x', 'mav_acc_y', 'mav_acc_z']
    # Можно подобавлять разные синтетические колонки
    #df['ReturnsClose'] = np.log(df['Close']/df['Close'].shift(1))
    #series = df[['Close','High','Volume', 'ReturnsClose']]
    
    #self.MydataFrame['Returns'] = self.MydataFrame['Price'].pct_change()
    #self.MydataFrame['Volatility'] = self.MydataFrame['Returns'].rolling(TIMESTEPS).std()*(252**0.5)
    #series = self.MydataFrame[['Price', 'Quantity', 'Timestamp_diff', 'Returns', 'Volatility']] # Picking the multivariate series
    
    #series = self.MydataFrame[['mav_roll', 'mav_pitch', 'mav_acc_x', 'mav_acc_y', 'mav_acc_z']] # Picking the multivariate series
    series = self.MydataFrame
    series = series.reset_index(drop = True)
    series = series.dropna()

    n = len(series)

    o70 = (int(n*0.70) // TIMESTEPS) * TIMESTEPS
    o85 = (int(n*0.85) // TIMESTEPS) * TIMESTEPS

    train_data = series.loc[0:o70]
    val_data = series.loc[o70:o85]
    test_data = series.loc[o85:]
    num_features = series.shape[1]

    return(train_data, val_data, test_data, num_features)
  
  def create_MySeries_aggTrades_percentage(self):
    es = self.MydataFrame[['Price', 'Quantity']]  # Picking the multivariate series
    series = es.reset_index(drop=True)
    series = series.dropna()

    # Calculate Price_Change column as the percentage change in Price
    series['Price_Change_Percentage'] = series['Price'].pct_change() * 100

    # Classify the Price_Change_Percentage values into custom classes
    series.loc[:, 'Price_Change'] = pd.cut(series['Price_Change_Percentage'],
                                           bins=[-np.inf, -4, -3, -2, -1, 0, 1, 2, 3, 4, np.inf],
                                           labels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    # Drop the 'Price_Change_Percentage' column
    series = series.drop(columns=['Price_Change_Percentage'])
    
    n = len(series)
    

    o70 = (int(n * 0.70) // TIMESTEPS) * TIMESTEPS
    o85 = (int(n * 0.85) // TIMESTEPS) * TIMESTEPS

    train_data = series.loc[0:o70]
    val_data = series.loc[o70:o85]
    test_data = series.loc[o85:]
    num_features = series.shape[1]

    return train_data, val_data, test_data, num_features


  def create_MySeries_klines(self):    
    # Можно подобавлять разные синтетические колонки
    #df['ReturnsClose'] = np.log(df['Close']/df['Close'].shift(1))
    
    #self.MydataFrame['Returns'] = self.MydataFrame['Close'].pct_change()
    #self.MydataFrame['Volatility'] = self.MydataFrame['Returns'].rolling(TIMESTEPS).std()*(252**0.5)
    #series = self.MydataFrame[['Close','Returns','Volatility','Volume',
    #                           'Close time', 'Quote asset volume',
    #                           'Taker buy base asset volume','Taker buy quote asset volume']]   
    #series = series.reset_index(drop = True)
    #series = series.dropna()
    self.MydataFrame['Timestamp_diff'] = self.MydataFrame['Close time'].diff(periods=1)/1000
        
    series = self.MydataFrame[['Close', 'Volume', 'Timestamp_diff', 'Quote asset volume', 'Number of trades']] # Picking the multivariate series
    series = series.reset_index(drop = True)
    series = series.dropna()

    n = len(series)

    o70 = (int(n*0.75) // TIMESTEPS) * TIMESTEPS
    o85 = (int(n*0.90) // TIMESTEPS) * TIMESTEPS

    train_data = series.loc[0:o70]
    val_data = series.loc[o70:o85]
    test_data = series.loc[o85:]
    num_features = series.shape[1]

    return(train_data, val_data, test_data, num_features)

class WindowGenerator:

  def __init__(self,input_width, label_width, 
                          shift,
                          train_df, val_df, test_df, 
                          label_columns):
    # Store the raw data.
    self.train_df = train_df
    self.val_df = val_df
    self.test_df = test_df
    global SEED
    global BATCH_SIZE
    global SHUFFLE
    global SEQSTRIDE

    # Work out the label column indices.
    self.label_columns = label_columns
    if label_columns is not None:
      self.label_columns_indices = {name: i for i, name in
                                    enumerate(label_columns)}
    self.column_indices = {name: i for i, name in
                           enumerate(train_df.columns)}

    # Work out the window parameters.
    self.input_width = input_width
    self.label_width = label_width
    self.shift = shift
    
    self.total_window_size = input_width + shift

    self.input_slice = slice(0, input_width)
    self.input_indices = np.arange(self.total_window_size)[self.input_slice]

    self.label_start = self.total_window_size - self.label_width
    self.labels_slice = slice(self.label_start, None)
    self.label_indices = np.arange(self.total_window_size)[self.labels_slice]

  def __repr__(self):
    return '\n'.join([
        f'Total window size: {self.total_window_size}',
        f'Input indices: {self.input_indices}',
        f'Label indices: {self.label_indices}',
        f'Label column name(s): {self.label_columns}'])

def split_window(self, features):
    inputs = features[:, self.input_slice, :]
    labels = features[:, self.labels_slice, :]
    if self.label_columns is not None:
      labels = tf.stack(
          [labels[:, :, self.column_indices[name]] for name in self.label_columns],
          axis=-1)

    # Slicing doesn't preserve static shape information, so set the shapes
    # manually. This way the `tf.data.Datasets` are easier to inspect.
    inputs.set_shape([None, self.input_width, None])
    labels.set_shape([None, self.label_width, None])

    return inputs, labels

WindowGenerator.split_window = split_window

def plot(self, model=None, plot_col=None, max_subplots=None):
    inputs, labels = self.example_test

    plt.figure(figsize=(12, 8))
    plot_col_index = self.column_indices[plot_col]
    max_n = min(max_subplots, len(inputs))
    for n in range(max_n):
      plt.subplot(max_n, 1, n+1)
      plt.ylabel(f'{plot_col} [normed]')
      plt.plot(self.input_indices, inputs[n, :, plot_col_index],
             label='Inputs', marker='.', zorder=-10)

      if self.label_columns:
        label_col_index = self.label_columns_indices.get(plot_col, None)
      else:
        label_col_index = plot_col_index

      if label_col_index is None:
        continue

      plt.scatter(self.label_indices, labels[n, :, label_col_index],
                edgecolors='k', label='Labels', c='#2ca02c', s=64)
      if model is not None:
        predictions = model(inputs)
        #plt.scatter(self.label_indices, predictions[n, :, label_col_index],
        plt.scatter(self.label_indices, predictions[n, :],
                  marker='X', edgecolors='k', label='Predictions',
                  c='#ff7f0e', s=64)

      if n == 0:
        plt.legend()

    plt.xlabel('Time [h]')

WindowGenerator.plot = plot

def make_dataset(self, data):
  global BATCH, SHUFFLE
  
    
  data = np.array(data, dtype=np.float32)
  #ds = tf.keras.utils.timeseries_dataset_from_array(
  ds = tf.keras.preprocessing.timeseries_dataset_from_array(
      data=data,
      targets=None,
      sequence_length=self.total_window_size,
# MAAAGIIIICC читай мануалы
#      sequence_stride=1,
#      shuffle=True,
      sequence_stride=SEQSTRIDE,
      #sequence_stride = self.total_window_size,
      #sequence_stride = self.total_window_size - 320,
      seed = SEED,
      shuffle=SHUFFLE,
      batch_size=BATCH)

  ds = ds.map(self.split_window)
  return ds

WindowGenerator.make_dataset = make_dataset

@property
def train(self):
  return self.make_dataset(self.train_df)
@property
def val(self):
  return self.make_dataset(self.val_df)
@property
def test(self):
  return self.make_dataset(self.test_df)
@property
def example(self):
  """Get and cache an example batch of `inputs, labels` for plotting."""
  result = getattr(self, '_example', None)
  if result is None:
    # No example batch was found, so get one from the `.train` dataset
    result = next(iter(self.train))
    # And cache it for next time
    self._example = result
  return result
@property
def example_test(self):
  """Get and cache an example batch of `inputs, labels` for plotting."""
  result = getattr(self, '_example_test', None)
  if result is None:
    # No example batch was found, so get one from the `.train` dataset
    result = next(iter(self.test))
    # And cache it for next time
    self._example_test = result
  return result


WindowGenerator.train = train
WindowGenerator.val = val
WindowGenerator.test = test
WindowGenerator.example = example
WindowGenerator.example_test = example_test

# Plotting the predictions
def plot_data(Y_test,Y_hat):
    nx = np.arange(len(Y_hat))
    fig = px.line(x=nx, y=[Y_test, Y_hat])
    fig.show()
    # Plotting the training errors
def plot_error(train_loss,val_loss):
    plt.plot(train_loss,c = 'r')
    plt.plot(val_loss,c = 'b')
    plt.ylabel('Loss')
    plt.xlabel('Epochs')
    plt.title('Loss Plot')
    plt.legend(['train','val'],loc = 'upper right')
    plt.show()
    
def plot_v2(Y_test, Y_hat):
    nx = np.arange(len(Y_hat))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=nx,
        y=Y_test,
        name="Real",
        line=dict(color='red'),
        mode='markers',
    ))
    fig.add_trace(go.Scatter(
        x=nx,
        y=Y_hat,
        name="Predict",
        mode="markers",
        line=dict(color='black'),
    ))

    fig.update_layout(
        title="Plot Title",
        xaxis_title="timesteps",
        yaxis_title="Wind.Speed",
        legend_title="Charts",
        font=dict(
            family="Courier New, monospace",
            size=12,
            color="RebeccaPurple"
        )
    )
    
    fig.update_layout(
    autosize=False,
    width=600,
    height=300,)
    
    fig.show()
    
def plot_v3(Y_test, Y_hat, FileName):
    nx = np.arange(len(Y_hat))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=nx,
        y=Y_test,
        name="Real",
        line=dict(color='red'),
        mode='markers',
    ))
    fig.add_trace(go.Scatter(
        x=nx,
        y=Y_hat,
        name="Predict",
        mode="markers",
        line=dict(color='black'),
    ))

    fig.update_layout(
        title=FileName,
        xaxis_title="timesteps",
        yaxis_title="Wind.Speed",
        legend_title="Charts",
        font=dict(
            family="Courier New, monospace",
            size=12,
            color="RebeccaPurple"
        )
    )
    
    fig.update_layout(
    autosize=False,
    width=900,
    height=450,)
    
    fig.show()
