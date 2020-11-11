import pathlib
from flask import request, Response, Flask
import json
import sqlite3
from datetime import datetime
from bank_db import Database
from random import randint

# TODO delete on cascade does not work, try to turn on the mode in sqlite3 for every operation
# TODO can create accounts with a BankUserId that does not exists fix, right now it is already a foreign key constraint??
# TODO make all database calls via Database class

app = Flask(__name__)
app.config['DEBUG'] = True
cwd = pathlib.Path(__file__).parent.absolute()

BASE_PATH = pathlib.Path(__file__).parent.absolute()
BANK_DB = f'{BASE_PATH}/bank_db.sqlite3'

@app.route('/bank/bank_user', methods=['GET'])
def get_bank_user():

    # get url params
    bank_user_id = request.args.get('bank_user_id')

    # create response
    response = Response()

    # check for valid request
    if bank_user_id is None:
        response.status_code = 401
        response_body = {
            "message":"Missing params" 
        }
        response.data = json.dumps(response_body)
        return response

    # valid request
    # connect to db
    db = sqlite3.connect(f'{cwd}/bank_db.sqlite3')

    # query for user
    curser = db.cursor()
    curser.execute('SELECT * FROM BankUser WHERE id = ?', (bank_user_id,))
    user = curser.fetchone()

    # close db connection
    db.close()

    # check if user exists
    if user:
        # user exists
        response_body = {
            "Id":user[0],
            "UserId":user[1],
            "CreatedAt":user[2],
            "ModifiedAt":user[3]
        }
        response.status_code = 200
    else:
        # user does not exists
        response.status_code = 404
        response_body = {
            "message":"No user found with id: " + bank_user_id 
        }

    # return response
    response.data = json.dumps(response_body)
    return response


@app.route('/bank/bank_user', methods=['POST'])
def add_bank_user():

    # get url params
    userId = request.json.get('UserId') if request.json else None # check if request has json body

    # create response
    resonse = Response()

    # check if valid request
    if userId is None:
        # invalid request
        resonse.status_code = 403
        resonse.data = json.dumps({
            'message':'Invalid request body'
        })
        return resonse

    # request is valid
    created_at = datetime.now().microsecond

    # make query
    query = '''
    INSERT INTO BankUser (UserId, CreatedAt, ModifiedAt)
    VALUES (?, ?, NULL);
    '''

    # connect to db
    db = sqlite3.connect(f'{cwd}/bank_db.sqlite3')
    curser = db.cursor()

    # run query
    try:
        # valid post
        curser.execute(query, (userId, created_at))
        curser.execute('commit')

        resonse.status_code = 201
        resonse.data = json.dumps({
            'Id':curser.lastrowid,
            'UserId': userId,
            "CreatedAt": created_at,
            'ModifiedAt': None
        })

    except sqlite3.IntegrityError:
        # invalid post, dublicate data
        resonse.status_code = 403
        resonse.data = json.dumps({
            'message':'bank user already exists'
        })

    
    return resonse


@app.route('/bank/bank_user', methods=['DELETE'])
def update_bank_user():

    bank_user_id = request.args.get('BankUserId') if request.args else None

    response = Response()

    # check if valid request
    if bank_user_id is None:
        # invalid request
        response.status_code = 403
        response.data = json.dumps({
            'message':'invalid param'
        })
        return response

    # valid request
    db = Database()
    db.connect(BANK_DB)

    # run query
    try:
        # valid post
        db.delete('BankUser', 'Id', bank_user_id)
        response.status_code = 204

    except sqlite3.IntegrityError:
        # invalid post, dublicate data
        response.status_code = 403
        response.data = json.dumps({
            'message':'bank user already exists'
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
            'CreatedAt':datetime.now().microsecond,
            'InterestRate':interest_rate,
            'Amount':amount
        }

        try:
            cur = db.insert('Account', data)
            response.status_code = 201
            response.data = json.dumps({
                'Id':f'{cur.lastrowid}'
            })

        except sqlite3.IntegrityError as e:
            response.status_code = 403
            response.data = json.dumps({
                'message':'BankUser already have an account'
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

    account_id = request.args.get('Id') if request.args else None

    if account_id is None:
        return gen_bad_request()

    db = Database()
    db.connect(BANK_DB)

    query = '''
    SELECT * FROM Account WHERE Id = ?;
    '''

    data = db.execQuery(query, (account_id, )).fetchone()

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

    db.close()

    return response


@app.route('/bank/account', methods=['PATCH'])
def update_account():

    response = Response()

    # check if request have query param and body
    if request.args is None or request.json is None:
        return gen_bad_request()

    account_id = request.args.get('Id')

    data = {
        'BankUserId':request.json.get('BankUserId'),
        'AccountNo':request.json.get('AccountNo'),
        'IsStudent':request.json.get('IsStudent'),
        'InterestRate':request.json.get('InterestRate'),
        'Amount':request.json.get('Amount'),
        'ModifiedAt':datetime.now().microsecond
    }

    data = {k: v for k, v in data.items() if v is not None}

    # check if fields are provided
    if account_id is None or len(data.values()) == 0:
        return gen_bad_request()

    # field provided update database
    db = Database()
    db.connect(BANK_DB)
    db.update('Account', data, 'Id', account_id)
    db.close()

    response.status_code = 204
    return response


@app.route('/bank/account', methods=['DELETE'])
def delete_account():

    response = Response()

    account_id = request.args.get('Id') if request.args else None

    print(account_id, flush=True)

    if account_id is None:
        return gen_bad_request()

    # valid request
    db = Database()
    db.connect(BANK_DB)
    db.delete('Account', 'Id', account_id)

    response.status_code = 204
    return response
    

def gen_bad_request():
    response = Response()
    response.status_code = 403
    response.data = json.dumps({
        'message':'invalid request'
    })
    return response


def generate_account_number():
    return ''.join(["{}".format(randint(0, 9)) for num in range(0, 8)])


if __name__ == "__main__":
    # begin server
    app.run(port = 8080)
