import pathlib
from flask import request, Response, Flask
import json
import sqlite3
from datetime import datetime
from database import Database, BANK_DB
from random import randint
import requests

# TODO delete on cascade does not work, try to turn on the mode in sqlite3 for every operation
# TODO can create accounts with a BankUserId that does not exists fix, right now it is already a foreign key constraint??
# TODO make all database calls via Database class

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/bank/bank_user', methods=['GET'])
def get_bank_user():

    # get url params
    bank_user_id = request.args.get('Id') if request.args else None

    # create response
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    # check for valid request
    if bank_user_id is None:
        # invalid request
        return gen_bad_request()

    # valid request
    # connect to db

    db = Database()
    db.connect(BANK_DB)

    query = 'SELECT * FROM BankUser WHERE Id = ?;'
    bank_user = db.execQuery(query, (bank_user_id, )).fetchone()
    db.close()

    # check if user exists
    if bank_user:
        # user exists
        response.status_code = 200
        response.data = json.dumps({
            'BankUser':bank_user
        })
    else:
        # user does not exists
        response.status_code = 404
        response.data = json.dumps({
            "message":"No user found with id: " + bank_user_id 
        })

    return response


@app.route('/bank/bank_user', methods=['POST'])
def add_bank_user():

    # get url params
    userId = request.json.get('UserId') if request.json else None # check if request has json body

    # create response
    resonse = Response()
    resonse.headers['Content-Type'] = 'application/json'

    # check if valid request
    if userId is None:
        # invalid request
        return gen_bad_request()

    # request is valid
    created_at = datetime.now().timestamp()

    # connect to db
    db = Database()
    db.connect(BANK_DB)

    # run query
    try:
        # query successful

        data = {
            'UserId':userId,
            'CreatedAt':created_at
        }

        cur = db.insert('BankUser', data)
        query = 'SELECT * FROM BankUser WHERE Id = ?;'
        bank_user = db.execQuery(query, (cur.lastrowid,)).fetchone()

        resonse.status_code = 201
        resonse.data = json.dumps({
            'BankUser': bank_user
        })

    except sqlite3.IntegrityError:
        # invalid, dublicate data
        resonse.status_code = 403
        resonse.data = json.dumps({
            'message':'bank user already exists'
        })
    finally:
        db.close()

    return resonse


@app.route('/bank/bank_user', methods=['DELETE'])
def update_bank_user():

    bank_user_id = request.args.get('BankUserId') if request.args else None

    response = Response()
    response.headers['Content-Type'] = 'application/json'

    # check if valid request
    if bank_user_id is None:
        # invalid request
        return gen_bad_request()

    # valid request
    db = Database()
    db.connect(BANK_DB)

    # run query
    try:
        # valid post
        db.delete('BankUser', bank_user_id)
        response.status_code = 204

    except sqlite3.Error:
        # invalid post, dublicate data
        response.status_code = 403
        response.data = json.dumps({
            'message':'invalid bank user id or id not found'
        })
    finally:
        db.close()

    return response

## NO update for BankUser since it makes no sence, 
# the only thing that can be updated is the UserId
#  and that is unique, and a BankUser cannot change user

@app.route('/bank/account', methods=['POST'])
def add_account():

    response = Response()
    response.headers['Content-Type'] = 'application/json'

    # check if request containts data body in json
    if request.json is None:
        return gen_bad_request()

    # get data from reqeust
    bank_user_id = request.json.get('BankUserId')
    is_student = request.json.get('IsStudent')
    interest_rate = request.json.get('InterstRate')
    amount = request.json.get('Amount')

    # check if required field are present
    if bank_user_id and is_student and interest_rate and amount:
        # valid request

        db = Database()
        db.connect(BANK_DB)

        data = {
            'BankUserId':bank_user_id,
            'AccountNo':generate_account_number(),
            'IsStudent':is_student,
            'CreatedAt':datetime.now().timestamp(),
            'InterestRate':interest_rate,
            'Amount':amount
        }

        try:
            cur = db.insert('Account', data)

            # get account to return with the response
            query = 'SELECT * FROM Account WHERE Id = ?;'
            account = db.execQuery(query, (cur.lastrowid,)).fetchone()

            response.status_code = 201
            response.data = json.dumps({
                'Account': account
            })

        except sqlite3.IntegrityError:
            response.status_code = 403
            response.data = json.dumps({
                'message':'BankUser does not exists or an account already exists for the provided BankUser'
            })
        finally:
            db.close()

        return response

    else:
        # invalid requst
        return gen_bad_request()


@app.route('/bank/account', methods=['GET'])
def get_account():

    response = Response()
    response.headers['Content-Type'] = 'application/json'

    account_id = request.args.get('Id') if request.args else None

    if account_id is None:
        return gen_bad_request()

    db = Database()
    db.connect(BANK_DB)

    query = 'SELECT * FROM Account WHERE Id = ?;'
    data = db.execQuery(query, (account_id,)).fetchone()
    db.close()

    if data:
        response.status_code = 200
        response.data = json.dumps({
            'Account':data
        })
    else:
        response.status_code = 404
        response.data = json.dumps({
            'message':'no account with the provided id'
        })

    return response


@app.route('/bank/account', methods=['PATCH'])
def update_account():

    response = Response()
    response.headers['Content-Type'] = 'application/json'

    # check if request have query param and body
    if request.args is None or request.json is None:
        return gen_bad_request()

    account_id = request.args.get('Id')
    # convert true/false to 1/0 because the database update function 
    # does create a literal sql string and does not format pyhton data to sql
    isStudent = 1 if (request.json.get('IsStudent') == True) else 0

    data = {
        'BankUserId':request.json.get('BankUserId'),
        'AccountNo':request.json.get('AccountNo'),
        'IsStudent':isStudent,
        'InterestRate':request.json.get('InterestRate'),
        'Amount':request.json.get('Amount'),
        'ModifiedAt':datetime.now().timestamp()
    }

    # removes entries where value is None
    data = {k: v for k, v in data.items() if v is not None}

    # check if fields are provided
    if account_id is None or len(data.values()) == 0:
        return gen_bad_request()

    # field provided update database
    db = Database()
    db.connect(BANK_DB)

    try:
        db.update('Account', data, account_id)

        # get updated account
        query = 'SELECT * FROM Account WHERE Id = ?;'
        account = db.execQuery(query, (account_id,)).fetchone()

        response.status_code = 200
        response.data = json.dumps({
            'Account':account
        })

    except sqlite3.IntegrityError:
        response.status_code = 403
        response.data = json.dumps({
            'message':'BankUserId is already taken or does not exists'
        })

    finally:
        db.close()

    
    return response


@app.route('/bank/account', methods=['DELETE'])
def delete_account():
    response = Response()
    response.headers['Content-Type'] = 'application/json'
    account_id = request.args.get('Id') if request.args else None

    if account_id is None:
        return gen_bad_request()

    # valid request
    db = Database()
    db.connect(BANK_DB)
        
    try:
        db.delete('Account', account_id)
        response.status_code = 204

    except sqlite3.Error:
        response.status_code = 403
        response.data = json.dumps({
            'message':'Invalid Account Id'
        })

    finally:
        db.close()

    return response


@app.route('/bank/deposit', methods=['GET'])
def get_deposits():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    bank_user_id = request.args.get('BankUserId') if request.args else None

    if bank_user_id is None:
        # invalid request
        return gen_bad_request()
    
    db = Database()
    db.connect(BANK_DB)
    query = 'SELECT * FROM Deposit WHERE BankUserId = ?;'
    deposits = db.execQuery(query, (bank_user_id,)).fetchall()

    response.status_code = 200
    response.data = json.dumps({
        'deposits':deposits
    })
    return response


@app.route('/bank/loan', methods=['GET'])
def get_loans():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    bank_user_id = request.args.get('BankUserId') if request.args else None

    if bank_user_id is None:
        # invalid request
        return gen_bad_request()
    
    db = Database()
    db.connect(BANK_DB)

    query = '''
    SELECT * FROM Loan WHERE BankUserId = ? AND Amount > 0;
    '''
    loans = db.execQuery(query, (bank_user_id,)).fetchall()

    response.status_code = 200
    response.data = json.dumps({
        'loans':loans
    })
    return response


@app.route('/bank/bank_user/withdraw', methods=['POST'])
def withdraw_money():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.json is None:
        return gen_bad_request()

    user_id = request.json.get('UserId')
    amount = request.json.get('Amount')

    if user_id is None or amount is None:
        return gen_bad_request()

    # check if amount is above 0
    if type(amount) != int and type(amount) != float:
        response.status_code = 403
        response.data = json.dumps({
            'message':'amount must be a number over 0'
        })
        return response

    if amount <= 0:
        response.status_code = 403
        response.data = json.dumps({
            'message':'amount must be a number over 0'
        })
        return response

    # valid request
    db = Database()
    db.connect(BANK_DB)

    db.execQuery('BEGIN TRANSACTION;')

    query = '''
    SELECT a.Id, a.Amount FROM Account a
    LEFT JOIN BankUser b ON b.Id = a.BankUserId
    WHERE b.UserId = ?;
    '''
    row = db.execQuery(query, (user_id,)).fetchone()

    # check if any results
    if row is None:
        db.close()
        # no Account and/or BankUser exists for the given UserId
        response.status_code = 403
        response.data = json.dumps({
            'message':'No Account and/or BankUser exists for the given UserId'
        })
        return response

    # account and bankuser exists
    account_id = row['Id']
    available_amount = row['Amount']

    # check if the user has the requested amount
    if available_amount >= amount:
        # sufficent money

        updated_balance = available_amount - amount

        data = {
            'Amount':updated_balance,
            'ModifiedAt':datetime.now().timestamp()
            }

        db.update('Account', data, account_id)

        # get updated account info to send back
        query = '''
        SELECT b.UserId, a.Id AS AccountId, b.Id AS BankUserId, a.Amount, a.ModifiedAt
        FROM Account a
        LEFT JOIN BankUser b ON a.BankUserId = b.Id
        WHERE b.UserId = ?;
        '''
        account_details = db.execQuery(query, (user_id,)).fetchone()

        response.status_code = 200
        response.data = json.dumps({
            'data':account_details
        })
    
    else:
        # not enough money
        response.status_code = 403
        response.data = json.dumps({
            'message':'Account does not have sufficent funds'
        })

    db.close()

    return response


@app.route('/bank/bank_user/deposit', methods=['POST'])
def add_deposit():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.json is None or request.args is None:
        return gen_bad_request()

    bank_user_id = request.args.get('BankUserId')
    amount = request.json.get('amount')

    if bank_user_id is None or amount is None:
        return gen_bad_request()

    if type(amount) != int and type(amount) != float:
        response.status_code = 400
        response.data = json.dumps({
            'message':'amount must be a positive number'
        })
        return response

    if amount <= 0:
        response.status_code = 400
        response.data = json.dumps({
            'message':'amount must be a positive number'
        })
        return response

    db = Database()
    db.connect(BANK_DB)

    # check if bank User has an account
    # if exists get current account balance
    query = '''
    SELECT a.Id, a.Amount 
    FROM Account a
    WHERE a.BankUserId = ?;
    '''
    
    row = db.execQuery(query, (bank_user_id,)).fetchone()

    if row is None:
        response.status_code = 403
        response.data = json.dumps({
            'message':'Bank User does not have an account'
        })
        return response

    account_id = row.get('Id')
    account_balance = row.get('Amount')

    # get interest rate
    call = requests.post('http://127.0.0.1:7071/api/Interest_Rate', data=json.dumps({'amount':amount}))

    if call.status_code != 200:
        response.status_code = call.status_code
        response.data = call.content
        return response

    body = json.loads(call.content)
    interest_amount = round(body.get('amount'), 2)

    data = {
        'BankUserId':bank_user_id,
        'CreatedAt':datetime.now().timestamp(),
        'Amount':interest_amount
    }

    try:
        # insert deposit entry
        cur = db.insert('Deposit',data)

        # get inserted entry
        query = 'SELECT * FROM Deposit WHERE Id = ?;'
        deposit = db.execQuery(query, (cur.lastrowid,)).fetchone()

        # update account balance
        account_data = {
            'ModifiedAt':datetime.now().timestamp(),
            'Amount':account_balance + interest_amount
        }

        db.update('Account', account_data, account_id)


    except sqlite3.IntegrityError:
        response.status_code = 403
        response.data = json.dumps({'message':'No BankUser exists with the given Id.'})
        return response
    finally:
        db.close()

    response.status_code = 200
    response.data = json.dumps({'Deposit':deposit})
    return response


@app.route('/bank/bank_user/loan', methods=['POST'])
def create_loan():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    # validate request
    if request.json is None:
        return gen_bad_request()

    bank_user_id = request.json.get('BankUserId')
    loan_amount = request.json.get('LoanAmount')

    if bank_user_id is None or loan_amount is None:
        return gen_bad_request()

    if type(loan_amount) != int and type(loan_amount) != float:
        return gen_bad_request()
    
    if loan_amount <= 0:
        return gen_bad_request()

    db = Database()
    db.connect(BANK_DB)

    query = '''
    SELECT a.Amount 
    FROM Account a WHERE a.BankUserId = ?;
    '''

    row = db.execQuery(query, (bank_user_id,)).fetchone()

    if row is None:
        # BankUser/Account does not exists for the given BankUserId
        db.close()
        response.status_code = 403
        response.data = json.dumps({'message':'No BankUser and/or Account exists for the given Id.'})
        return response
        
    # BankUser/Account exists
    total_amount = row.get('Amount')

    # make call to loan function
    request_body = json.dumps({
        'loan_amount':loan_amount,
        'total_amount':total_amount
    })

    call = requests.post('http://127.0.0.1:7071/api/Loan_Algorithm', data=request_body)

    if call.status_code != 200:
        db.close()
        response.status_code = call.status_code
        response.data = call.content
        return response
    
    # account has sufficient funds, create loan
    loan = {
        'BankUserId':bank_user_id,
        'CreatedAt':datetime.now().timestamp(),
        'ModifiedAt':None,
        'Amount':loan_amount
    }

    try:
        # create loan entry
        cur = db.insert('Loan', loan)

        # get created loan
        query = 'SELECT * FROM Loan WHERE Id = ?;'
        loan_entry = db.execQuery(query, (cur.lastrowid,)).fetchone()

        # insert mony from loan into account
        loan_data = {
        'Amount': loan_amount + total_amount,
        'ModifiedAt':datetime.now().timestamp()
        }

        db.update('Account', loan_data, id_value = bank_user_id, id_name = 'BankUserId')

        response.status_code = 200
        response.data = json.dumps({'Loan':loan_entry})
        return response

    except sqlite3.IntegrityError:
        response.status_code = 403
        response.data = json.dumps({'message':'BankUser already has a Loan'})
        return response

    finally:
        db.close()


@app.route('/bank/bank_user/pay-loan', methods=['POST'])
def pay_load():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.json is None:
        return gen_bad_request()

    bank_user_id = request.json.get('BankUserId')
    loan_id = request.json.get('LoanId')

    if bank_user_id is None or loan_id is None:
        return gen_bad_request()

    # begin a transaction
    db = Database()
    db.connect(BANK_DB)

    # read Account balance and loan amount
    loan_query = '''
    SELECT Amount, BankUserId FROM Loan WHERE Id = ?;
    '''

    row = db.execQuery(loan_query, (loan_id,)).fetchone()

    if row is None:
        db.close()
        response.status_code = 403
        response.data = json.dumps({'message':'No BankUser/Loan for the given id'})
        return response
    
    loan_amount = row.get('Amount')

    account_query = '''
    SELECT Id, Amount FROM Account WHERE BankUserId = ?;
    '''

    row = db.execQuery(account_query, (bank_user_id,)).fetchone()

    if row is None:
        db.close()
        response.status_code = 403
        response.data = json.dumps({'message':'No BankUser/Account for the given id'})
        return response

    account_id = row.get('Id')
    account_amount = row.get('Amount')

    if loan_amount > account_amount:
        # insufficient funds
        db.close()
        response.status_code = 403
        response.data = json.dumps({'message':'Account has insufficent funds'})
        return response
    
    # account has enough money
    # update loan

    loan_data = {
        'Amount':0,
        'ModifiedAt':datetime.now().timestamp()
    }

    db.update('Loan', loan_data, loan_id)

    # update account
    account_data = {
        'Amount':account_amount - loan_amount,
        'ModifiedAt':datetime.now().timestamp()
    }

    db.update('Account', account_data, account_id)

    response.status_code = 200
    return response


def gen_bad_request():
    response = Response()
    response.headers['Content-Type'] = 'application/json'
    response.status_code = 400
    response.data = json.dumps({
        'message':'invalid request'
    })
    return response


def generate_account_number():
    return ''.join(["{}".format(randint(0, 9)) for num in range(0, 8)])


if __name__ == "__main__":
    # begin server
    app.run(port = 8090, threaded=True)
