import pathlib
from flask import request, Response, Flask
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
cwd = pathlib.Path(__file__).parent.absolute()

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
    
    query = '''
    DELETE FROM BankUser WHERE id = ?
    '''
    # connect to db
    db = sqlite3.connect(f'{cwd}/bank_db.sqlite3')
    curser = db.cursor()

    # run query
    try:
        # valid post
        curser.execute(query, (bank_user_id,))
        curser.execute('commit')
        response.status_code = 204

    except sqlite3.IntegrityError:
        # invalid post, dublicate data
        response.status_code = 403
        response.data = json.dumps({
            'message':'bank user already exists'
        })

    return response




## NO update for BankUser since it makes no sence, 
# the only thing that can be updated is the UserId
#  and that is unique, and a BankUser cannot change user


if __name__ == "__main__":
    # begin server
    app.run(port = 8080)
    