import csv

import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import sys
from stock_prediction import create_model, load_data
from parameters import *
import os

ticker = "EURUSD=X"
if len(sys.argv) >= 2:
    ticker = sys.argv[1]

LOOKUP_STEP = 1
if len(sys.argv) >= 3:
    LOOKUP_STEP: int = int(sys.argv[2])

now = datetime.now()
timestamp = datetime.timestamp(now)
dias_futuros = 86400 * int(LOOKUP_STEP)
fecha_hora_now = now.strftime('%d/%m/%Y - %I:%M%p')
fecha_img = now.strftime('%d%m%Y%I%M%p')
fecha_futura_timestamp = int(timestamp) + int(dias_futuros)
fecha_futura = str(datetime.fromtimestamp(fecha_futura_timestamp))[5:10].replace('-', '/')

# Amazon stock market
ticker_data_filename = os.path.join("data", f"{ticker}_{date_now}.csv")
# model name to save, making it as unique as possible based on parameters
model_name = f"{date_now}_{ticker}-{shuffle_str}-{scale_str}-{split_by_date_str}-\
{LOSS}-{OPTIMIZER}-{CELL.__name__}-seq-{N_STEPS}-layers-{N_LAYERS}-units-{UNITS}"
if BIDIRECTIONAL:
    model_name += "-b"

if not os.path.isdir("img"):
    os.mkdir("img")


def plot_graph(test_df):
    """
    This function plots true close price along with predicted close price
    with blue and red colors respectively
    """
    plt.figure(figsize=(10, 5))
    plt.plot(test_df[f'true_adjclose_{LOOKUP_STEP}'], c='b')
    plt.plot(test_df[f'adjclose_{LOOKUP_STEP}'], c='r')
    plt.xlabel("Days")
    plt.ylabel("Price")
    plt.title(ticker)
    plt.legend(["Precio real", "Precio estimado"])
    plt.grid(True)

    plt.savefig(f'img/{ticker}_backtesting.png')

    # plt.show()


def get_final_df(model, data):
    """
    This function takes the `model` and `data` dict to
    construct a final dataframe that includes the features along
    with true and predicted prices of the testing dataset
    """
    # if predicted future price is higher than the current,
    # then calculate the true future price minus the current price, to get the buy profit
    buy_profit = lambda current, true_future, pred_future: true_future - current if pred_future > current else 0
    # if the predicted future price is lower than the current price,
    # then subtract the true future price from the current price
    sell_profit = lambda current, true_future, pred_future: current - true_future if pred_future < current else 0
    X_test = data["X_test"]
    y_test = data["y_test"]
    # perform prediction and get prices
    y_pred = model.predict(X_test)
    if SCALE:
        y_test = np.squeeze(data["column_scaler"]["adjclose"].inverse_transform(np.expand_dims(y_test, axis=0)))
        y_pred = np.squeeze(data["column_scaler"]["adjclose"].inverse_transform(y_pred))
    test_df = data["test_df"]
    # add predicted future prices to the dataframe
    test_df[f"adjclose_{LOOKUP_STEP}"] = y_pred
    # add true future prices to the dataframe
    test_df[f"true_adjclose_{LOOKUP_STEP}"] = y_test
    # sort the dataframe by date
    test_df.sort_index(inplace=True)
    final_df = test_df
    # add the buy profit column
    final_df["buy_profit"] = list(map(buy_profit,
                                      final_df["adjclose"],
                                      final_df[f"adjclose_{LOOKUP_STEP}"],
                                      final_df[f"true_adjclose_{LOOKUP_STEP}"])
                                  # since we don't have profit for last sequence, add 0's
                                  )
    # add the sell profit column
    final_df["sell_profit"] = list(map(sell_profit,
                                       final_df["adjclose"],
                                       final_df[f"adjclose_{LOOKUP_STEP}"],
                                       final_df[f"true_adjclose_{LOOKUP_STEP}"])
                                   # since we don't have profit for last sequence, add 0's
                                   )
    return final_df


def predict(model, data):
    # retrieve the last sequence from data
    last_sequence = data["last_sequence"][-N_STEPS:]
    # expand dimension
    last_sequence = np.expand_dims(last_sequence, axis=0)
    # get the prediction (scaled from 0 to 1)
    prediction = model.predict(last_sequence)
    # get the price (by inverting the scaling)
    if SCALE:
        predicted_price = data["column_scaler"]["adjclose"].inverse_transform(prediction)[0][0]
    else:
        predicted_price = prediction[0][0]
    return predicted_price


def predict_low(model, data):
    # retrieve the last sequence from data
    last_sequence = data["last_sequence"][-N_STEPS:]
    # expand dimension
    last_sequence = np.expand_dims(last_sequence, axis=0)
    # get the prediction (scaled from 0 to 1)
    prediction = model.predict(last_sequence)
    # get the price (by inverting the scaling)
    if SCALE:
        predicted_price = data["column_scaler"]["low"].inverse_transform(prediction)[0][0]
    else:
        predicted_price = prediction[0][0]
    return predicted_price


def predict_high(model, data):
    # retrieve the last sequence from data
    last_sequence = data["last_sequence"][-N_STEPS:]
    # expand dimension
    last_sequence = np.expand_dims(last_sequence, axis=0)
    # get the prediction (scaled from 0 to 1)
    prediction = model.predict(last_sequence)
    # get the price (by inverting the scaling)
    if SCALE:
        predicted_price = data["column_scaler"]["high"].inverse_transform(prediction)[0][0]
    else:
        predicted_price = prediction[0][0]
    return predicted_price

# load the data
data = load_data(ticker, N_STEPS, scale=SCALE, split_by_date=SPLIT_BY_DATE,
                 shuffle=SHUFFLE, lookup_step=LOOKUP_STEP, test_size=TEST_SIZE,
                 feature_columns=FEATURE_COLUMNS)

# construct the model
model = create_model(N_STEPS, len(FEATURE_COLUMNS), loss=LOSS, units=UNITS, cell=CELL, n_layers=N_LAYERS,
                     dropout=DROPOUT, optimizer=OPTIMIZER, bidirectional=BIDIRECTIONAL)

# load optimal model weights from results folder
model_path = os.path.join("results", model_name) + ".h5"
model.load_weights(model_path)

# evaluate the model
loss, mae = model.evaluate(data["X_test"], data["y_test"], verbose=1)
# calculate the mean absolute error (inverse scaling)
if SCALE:
    mean_absolute_error = data["column_scaler"]["adjclose"].inverse_transform([[mae]])[0][0]
else:
    mean_absolute_error = mae

# get the final dataframe for the testing set
final_df = get_final_df(model, data)
# predict the future price
future_price = predict(model, data)
future_price_low = predict_low(model, data)
future_price_high = predict_high(model, data)
# we calculate the accuracy by counting the number of positive profits
accuracy_score = (len(final_df[final_df['sell_profit'] > 0]) + len(final_df[final_df['buy_profit'] > 0])) / len(
    final_df)
# printing metrics
valores_csv = f"{fecha_hora_now},{ticker},{date_start.replace('-', '/')} - {date_now.replace('-', '/')}," \
              f"{future_price_low:.4f},{future_price_high:.4f},{future_price:.4f}"
valores_csv_futuro = f'{fecha_futura},{future_price_low:.4f},{future_price_high:.4f},{future_price:.4f}'
os.system(f'echo {valores_csv} >> tmp/archivo.csv')
os.system(f'echo {valores_csv_futuro} >> tmp/{ticker}_futuro.csv')
print(f"Future price after {LOOKUP_STEP} days is {future_price:.4f}$")
print(f"{LOSS} loss:", loss)
# plot true/pred prices graph
plot_graph(final_df)
print(final_df.tail(10))
# save the final dataframe to csv-results folder
csv_results_folder = "csv-results"
if not os.path.isdir(csv_results_folder):
    os.mkdir(csv_results_folder)
csv_filename = os.path.join(csv_results_folder, model_name + ".csv")
final_df.to_csv(csv_filename)


