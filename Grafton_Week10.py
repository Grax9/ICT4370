'''
Author: Erik Grafton
E-mail: Erik.Grafton@du.edu
Date: June 04, 2021
Version: 1.0
Code Purpose: 
    The code takes a user defined stock portfolio along with timestamped stock
    information in order to create a png graph of the value of the stock over time 
Code Inputs:
    AllStocks.json, a json file of stock information over time
    Data_Stocks.csv, a csv file of a stock portfolio
Code Output:
    A png file containing a graph with stock values over time
'''
import copy
import csv
import datetime
import json
import os
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import traceback
import tkinter as tk
import tkinter.filedialog

# ==============================================================================
# Define Classes and Functions
# ==============================================================================


class Stock_Timestamp():
    '''Class to hold stock timestamp information'''

    def __init__(self, symbol, date, close_price):
        self.symbol = symbol
        self.date = datetime.datetime.strptime(date, "%d-%b-%y")
        self.close_price = float(close_price)


class Stock():
    '''Class to hold Stock objects'''

    def __init__(self, symbol, number_of_shares):
        self.symbol = symbol
        # Convert necessary string fields to float
        self.number_of_shares = float(number_of_shares)


class Investor():
    '''Primary class, used to hold Stock and Bond objects'''

    def __init__(self, name):
        self.name = name
        self.stocks = {}
        self.stock_timestamps = {}
        self.stock_volumes = {}
        self.symbol_dict = {}

    def add_stock(self, stock):
        '''Add new stock to stocks dictionary'''
        self.stocks[stock.symbol] = stock

    def set_stock_metadata(self):
        '''Function to capture a list of all unique stocks and the 
           number of owned shares per stock'''
        for key, value in self.stocks.items():
            self.stock_volumes[key] = value.number_of_shares

        symbol_set = set(self.stocks.keys())
        for i in symbol_set:
            self.symbol_dict[i] = None

    def calculate_value(self, symbol, close):
        '''Calculate the value of a stock (closing price * number of shares)'''
        num_shares = self.stock_volumes[symbol]
        return num_shares * close

    def add_stock_timestamp(self, timestamp):
        '''Add a stock timestamp to the investor portfolio'''
        # Only process data that the investor owns
        if timestamp.symbol in self.symbol_dict:
            # Calculate the value of the stock on this date
            value = self.calculate_value(
                timestamp.symbol, timestamp.close_price)

            # If a dictionary entry for this date does not exist, create it
            if timestamp.date not in self.stock_timestamps:
                # Deepcopy the default stock dictionary, prepopulated with None values
                self.stock_timestamps[timestamp.date] = copy.deepcopy(
                    self.symbol_dict)

            # Populate the value of the stock on this date
            self.stock_timestamps[timestamp.date][timestamp.symbol] = value

    def prep_for_graph(self):
        '''Function to structure the data for input into matplotlib'''
        # Sort dates to ensure proper order
        sorted_dates = sorted(self.stock_timestamps)

        # Create a dictionary where the values are lists, with an entry for each stock
        # and an entry for dates
        graph_dict = {}
        graph_dict['dates'] = []
        for key in self.symbol_dict.keys():
            # Init list for each stock
            graph_dict[key] = []

        for date in sorted_dates:
            graph_dict['dates'].append(date)
            # Iterate through each stock value on this date and populate the proper lists
            for key, value in self.stock_timestamps[date].items():
                graph_dict[key].append(value)

        return graph_dict

class FileControl():
    '''Class to hold and maintain file paths'''

    def __init__(self):
        self.stock_portfolio_path = None
        self.stock_information_path = None
        self.output_path = None
        self.own_path = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))

    def paths_exist(self):
        '''Function to determine if all required data was entered'''
        if (self.stock_information_path != None and self.stock_portfolio_path != None
                and self.output_path != None):
            return True
        return False

    def set_portfolio_path(self):
        '''Set path to portfolio CSV'''
        # Prompt filename dialog in working dir, only show CSV files
        path = tkinter.filedialog.askopenfilename(initialdir=self.own_path, filetypes=[('CSV Files', '*.csv')])
        self.stock_portfolio_path = path

    def get_portfolio_path(self):
        return self.stock_portfolio_path

    def set_information_path(self):
        '''Set path to portfolio CSV'''
        # Prompt filename dialog in working dir, only show JSON files
        path = tkinter.filedialog.askopenfilename(initialdir=self.own_path, filetypes=[('JSON Files', '*.json')])
        self.stock_information_path = path

    def get_information_path(self):
        return self.stock_information_path

    def set_output_path(self):
        '''Set path to output PNG'''
        # Prompt filename dialog in working dir, require save as PNG
        path = tkinter.filedialog.asksaveasfilename(initialdir=self.own_path, filetypes=[('PNG Files', '*.png')])
        self.output_path = path

    def get_output_path(self):
        return self.output_path

# ==============================================================================
# Main
# ==============================================================================
try:
    # Init FileControl object to store paths
    file_control = FileControl()

    # Open tkinter GUI for user
    window = tk.Tk()
    # Default window size/title
    window.geometry('400x300')
    window.title('Grafton ICT4370 Final Project')

    # Create and pack CSV selection button
    profile_button = tk.Button(window, text = "Select path to Stock Profile CSV", command=file_control.set_portfolio_path)
    profile_button.pack(pady=20)

    # Create and pack JSON selection button
    information_button = tk.Button(window, text = "Select path to Stock Information JSON", command=file_control.set_information_path)
    information_button.pack(pady=20)

    # Create and pack PNG output selection button
    output_button = tk.Button(window, text = "Select path for output graph", command=file_control.set_output_path)
    output_button.pack(pady=20)

    # Create and pack Submit button, which closes tkinter GUI
    exit_button = tk.Button(window, text="Submit", command=window.destroy)
    exit_button.pack(pady=20)

    # Keeps tkinter window open until exit_button is clicked
    window.mainloop()

    # Warning that not all of the paths were entered in tkinter, imminent failure.
    # Will allow to pass for traceback
    if not file_control.paths_exist():
        print ('File paths not populated correctly. Application will close')

    # Create SQLite DB
    conn = sqlite3.connect(':memory:')

    cur = conn.cursor()
    # Create table for stock date information
    cur.execute('CREATE TABLE stock_dates (symbol TEXT, date TEXT, open TEXT, high TEXT, ' +
                'low TEXT, close REAL, volume REAL)')
    print('Table Created')

    # Create Investor object
    investor = Investor('Bob Smith')

    # Read in CSV
    with open(file_control.get_portfolio_path(), mode='r') as csv_file:
        stock_csv = csv.DictReader(csv_file)
        for stock in stock_csv:
            # Instantiate a Stock object for each row in the CSV
            try:
                stock_obj = Stock(stock['SYMBOL'], stock['NO_SHARES'])
            except:
                print ('Error creating Stock object')

            # Add the stock object to the investor object
            investor.add_stock(stock_obj)

    # Set stock metadata (unique names and share numbers)
    investor.set_stock_metadata()

    # Open stock date json file
    with open(file_control.get_information_path()) as f:
        data = json.load(f)

    # Iterate dicts in file
    for row in data:
        symbol = row['Symbol']
        date = row['Date']
        open_price = row['Open']
        high_price = row['High']
        low_price = row['Low']
        close = row['Close']
        volume = row['Volume']

        # Write each row to the database
        cur.execute(f"INSERT INTO stock_dates VALUES ('{symbol}', '{date}', '{open_price}', " +
                    f"'{high_price}', '{low_price}', {close}, {volume})")
        conn.commit()

        # Add each dict to investor as a Stock_Timestamp object
        investor.add_stock_timestamp(Stock_Timestamp(symbol, date, close))

    # Format the data for ingest into matplotlib
    data = investor.prep_for_graph()

    # Define X axis as dates and remove from dict
    x = data['dates']
    data.pop('dates')

    # Iterate each stock list and create a plot line
    for key, value in data.items():
        plt.plot(x, value, label=key)

    # Format X axis dates
    plt.gcf().autofmt_xdate()
    # Add legend
    plt.legend()
    # Save plot to disk as PNG
    plt.savefig(file_control.get_output_path())

except:
    print('An error occured')
    traceback.print_exc()
