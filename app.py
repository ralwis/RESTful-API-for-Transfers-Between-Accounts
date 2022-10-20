from flask import Flask, request, jsonify 
import flask
from flask_cors import CORS, cross_origin

app = flask.Flask(__name__)
cors = CORS(app)

import sqlite3

def connect():
    """Connect to the SQLite database server"""
    conn = sqlite3.connect('bank.db')
    return conn

@app.route('/dropAndCreateTables', methods=['GET'])
def DropAndCreate():

    conn = connect()

    #drop table if exists
    conn.execute("DROP TABLE IF EXISTS bank_account")
    conn.execute("DROP TABLE IF EXISTS inter_account_transactions")

    #create account table
    conn.execute('''CREATE TABLE bank_account
                    (account_number INTEGER PRIMARY KEY,
                    account_holder_name TEXT,
                    account_type TEXT,
                    account_balance REAL)''')

    #insert sample data
    conn.execute("INSERT INTO bank_account (account_number, account_holder_name, account_type, account_balance) VALUES (123456, 'Dineth', 'Savings', 1000)")
    conn.execute("INSERT INTO bank_account (account_number, account_holder_name, account_type, account_balance) VALUES (456789, 'Thanura', 'Savings', 2000)")
    conn.execute("INSERT INTO bank_account (account_number, account_holder_name, account_type, account_balance) VALUES (456782, 'Vihan', 'Current', 3000)")
    conn.execute("INSERT INTO bank_account (account_number, account_holder_name, account_type, account_balance) VALUES (422789, 'Induwara', 'Current', 4000)")
    conn.execute("INSERT INTO bank_account (account_number, account_holder_name, account_type, account_balance) VALUES (245678, 'Gihan', 'Current', 5000)")

    #create inter_account_transactions table
    conn.execute('''CREATE TABLE inter_account_transactions
                    (transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,                      
                    transaction_date TEXT default CURRENT_DATE,
                    transaction_type TEXT,
                    transaction_amount REAL,
                    from_account_number INTEGER,
                    to_account_number INTEGER,
                    FOREIGN KEY (from_account_number) REFERENCES bank_account(account_number),
                    FOREIGN KEY (to_account_number) REFERENCES bank_account(account_number))''')

    conn.commit()

    return "Tables dropped and created successfully"


@app.route('/inter_account_transfer', methods=['POST'])
def InterAccountTransfer():
    data = request.get_json(force=True)
    from_bank_account = data['from_bank_account']
    to_bank_account = data['to_bank_account']
    transaction_amount = data['transaction_amount']

    try:
        conn = connect()
        print("Opened database successfully")
    except:
        print("Error opening database")
        return jsonify({'error': 'Error opening database'})

    if from_bank_account == to_bank_account:
        return jsonify({'error': 'Cannot transfer money to the same account'})
    #amout is not a number
    if not str(transaction_amount).isnumeric():
        return jsonify({'error': 'Amount must be a number'})
    #amount is negative
    if float(transaction_amount) < 0:
        return jsonify({'error': 'Amount must be positive'})

    #check account number is valid
    cursor = conn.execute("SELECT account_number FROM bank_account WHERE account_number = ?", (from_bank_account,))
    if len(cursor.fetchall()) == 0:
        return jsonify({'error': 'From account number is invalid'})

    cursor = conn.execute("SELECT account_number FROM bank_account WHERE account_number = ?", (to_bank_account,))
    if len(cursor.fetchall()) == 0:
        return jsonify({'error': 'To account number is invalid'})

    #check if from account has enough money
    cursor = conn.execute("SELECT account_balance FROM bank_account WHERE account_number = ?", (from_bank_account,))
    from_account_balance = cursor.fetchone()[0]
    if from_account_balance < float(transaction_amount):
        return jsonify({'error': 'From account does not have enough money'})

    try:

        #insert inter_account_transaction and get the transaction_id
        conn.execute('''INSERT INTO inter_account_transactions
                        (transaction_type, transaction_amount, from_account_number, to_account_number)  
                        VALUES ('Transfer', ?, ?, ?)''', (transaction_amount, from_bank_account, to_bank_account))
        transaction_id = conn.execute('''SELECT transaction_id FROM inter_account_transactions WHERE rowid = last_insert_rowid()''').fetchone()[0]

        #insert account balance
        conn.execute('''UPDATE bank_account
                        SET account_balance = account_balance - ?       
                        WHERE account_number = ?''', (transaction_amount, from_bank_account))

        conn.execute('''UPDATE bank_account
                        SET account_balance = account_balance + ?                       
                        WHERE account_number = ?''', (transaction_amount, to_bank_account))

        #commit the changes
        conn.commit()

        #return the summary of the transaction and transaction_id
        return jsonify({'transaction_id': transaction_id,
                        'from_bank_account': from_bank_account,         
                        'to_bank_account': to_bank_account,
                        'transaction_amount': transaction_amount,
                        'status': 'success'})
    except:
        return jsonify({'status': 'failed'})


@app.route('/getAllTransactions', methods=['GET'])
def getAllTransactions():
    data = request.get_json(force=True)
    account_number = data['account_number']

    try:
        conn = connect()
        print("Opened database successfully")
    except:
        print("Error opening database")
        return jsonify({'error': 'Error opening database'})

    #check account number is valid
    cursor = conn.execute("SELECT account_number FROM bank_account WHERE account_number = ?", (account_number,))
    if len(cursor.fetchall()) == 0:
        return jsonify({'error': 'Account number is invalid'})

    #get all transactions
    cursor = conn.execute('''SELECT transaction_id, transaction_date, transaction_type, transaction_amount, from_account_number, to_account_number
                            FROM inter_account_transactions
                            WHERE from_account_number = ? OR to_account_number = ?''', (account_number, account_number))
    transactions = cursor.fetchall()

    return jsonify({'transactions': transactions})

app.run(port=5000)