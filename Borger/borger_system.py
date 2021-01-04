import pathlib
from sqlite3.dbapi2 import IntegrityError
from flask import request, Response, Flask
import json
import sqlite3
from datetime import date, datetime
from database import Database

app = Flask(__name__)
app.config["DEBUG"] = True
db_path = f"{pathlib.Path(__file__).parent.absolute()}/borger_db.sqlite3"

# CRUD FOR Borger
@app.route("/borger_service/borger", methods=["POST"])
def create_borger():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    user_id = request.json.get("user_id")

    if user_id:
        try:
            db = Database()
            db.connect(db_path)

            data = {
                "UserId": user_id,
                "CreatedAt": datetime.now()
            }

            cur = db.insert("BorgerUser", data)

            # get inserted borger
            query = '''
            SELECT * FROM BorgerUser Where Id = ?;
            '''
            borger = db.execQuery(query, (cur.lastrowid, )).fetchone()

            response.status_code = 201
            response_body = borger

        except sqlite3.IntegrityError:
            response.status_code = 403
            response_body = {
                "status": "Database integrity error.",
                "message": "user_id already exists."
            }
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To create a user you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/borger_service/borger", methods=["GET"])
def read_borger():
    db = sqlite3.connect(db_path)
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    
    user_id = request.args.get("id")

    if user_id:
        try:
            cursor = db.cursor()
            rows = cursor.execute("SELECT * FROM BorgerUser WHERE Id=?;", (user_id,))
            response.status_code = 200
            user = rows.fetchone()
            response_body = {"BorgerUser":{"Id":user[0], "user_id":user[1], "CreatedAt":user[2]}}
        except TypeError:
            response.status_code = 400
            response_body = {"Status":f"user_id '{user_id}' not found."}
    else:
        response.status_code = 400
        response_body = {
            "status": "Missing parameters.",
            "message": "To get a user you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/borger_service/borger", methods=["PATCH"])
def update_borger():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.args is None or request.json is None:
        return gen_bad_request()

    identifier = request.args.get("id")
    user_id = request.json.get("user_id")

    if identifier is None or user_id is None:
        return gen_bad_request("id and/or user_id is missing and are required")

    db = Database()
    db.connect(db_path)

    try:
        data = {
            "UserId": user_id
        }

        db.update("BorgerUser", data, identifier)

        # get updated borger user
        query = 'SELECT * FROM BorgerUser WHERE Id = ?'
        borger_user = db.execQuery(query, (identifier,)).fetchone()

        if borger_user:
            response.status_code = 200
            response_body = borger_user
        else:
            response.status_code = 404
            response_body = {
                "status": "Resource not found",
                "message": f"No user with id '{identifier}' was found"}

    except sqlite3.IntegrityError:
        response.status_code = 403
        response_body = {
            "status": "Database integrity error.",
            "message": "user_id already exists or foreign key constraint fails"
        }
    finally:
        db.close()

    response.data = json.dumps(response_body)
    return response

@app.route("/borger_service/borger", methods=["DELETE"])
def delete_borger():
    db = sqlite3.connect(db_path)
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    id = request.args.get("id")

    if id:
        cursor = db.cursor()
        if cursor.execute("SELECT * FROM BorgerUser WHERE Id=?", (id,)).fetchone():
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("DELETE FROM BorgerUser WHERE Id=?;", (id,))
            cursor.execute("COMMIT")
            response.status_code = 200
            response_body = {"status": f"User '{id}' successfully deleted"}
        else:
            response.status_code = 404
            response_body = {
                "status": "Resource not found",
                "message": f"No user with user_id '{id}' was found"}
    else:
        response.status_code = 400
        response_body = {
            "status": "Missing parameters.",
            "message": "To delete a user you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

# CRUD FOR Address
@app.route("/borger_service/address", methods=["POST"])
def create_address():
    db = sqlite3.connect(db_path)
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    # validate reqeust
    if request.json is None:
        return gen_bad_request()

    borger_user_id = request.json.get("borger_user_id")
    street = request.json.get("street")

    if borger_user_id is None or street is None:
        return gen_bad_request()

    db = Database()
    db.connect(db_path)

    try:
        # get borger user
        borger_user = db.execQuery("SELECT * FROM BorgerUser WHERE Id = ?;", (borger_user_id,)).fetchone()

        if borger_user:
            # Change current active address for user
            db.execQuery("UPDATE Address SET IsValid = 0 WHERE BorgerUserId=?", (borger_user_id,))
            
            # Insert new address
            data = {
                "BorgerUserId": borger_user_id,
                "Street": street,
                "CreatedAt": datetime.now(),
                "IsValid": 1 
            }
            
            cur = db.insert("Address", data)
            
            # get inserted address
            address = db.execQuery('SELECT * FROM Address WHERE Id = ?', (cur.lastrowid,)).fetchone()

            response.status_code = 201
            response_body = address
        
        else:
            response.status_code = 404
            response_body = {
            "status": "Not Found.",
            "message": "Borger User does not exists."
        }
        
    except sqlite3.IntegrityError:
        response.status_code = 403
        response_body = {
            "status": "Database integrity error.",
            "message": "borger_user_id not found."
        }
    finally:
        db.close()

    response.data = json.dumps(response_body)
    return response

@app.route("/borger_service/address", methods=["GET"])
def read_address():
    db = sqlite3.connect(db_path)
    response = Response()
    response.headers['Content-Type'] = 'application/json'


    borger_user_id = request.args.get("borger_user_id")

    if borger_user_id:
        
        db = Database()
        db.connect(db_path)

        addresses = db.execQuery("SELECT * FROM Address WHERE BorgerUserId = ?;", (borger_user_id,)).fetchall()
        response_body = {"Addresses":addresses}
    else:
        response.status_code = 400
        response_body = {
            "status": "Missing parameters.",
            "message": "To get an address you must specify a 'borger_user_id'"
        }

    response.data = json.dumps(response_body)
    return response


@app.route("/borger_service/address", methods=["PATCH"])
def update_address():
    db = sqlite3.connect(db_path)
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    # validate request
    if request.args is None or request.json is None:
        return gen_bad_request()

    id = request.args.get("id")
    street = request.json.get("street")
    isValid = request.json.get("is_valid")

    if id is None:
        return gen_bad_request()

    data = {}

    if street != None:
        data['Street'] = street
    
    if isValid != None:
        data['IsValid'] = 1 if isValid == True else 0

    if data:
        db = Database()
        db.connect(db_path)

        try:
            # get existing address
            address = db.execQuery("SELECT * FROM Address WHERE Id = ?;", (id,)).fetchone()

            if address:
                # check if isValid should be updated
                if data['IsValid']:
                    # check if isValid is different than existing
                    if data['IsValid'] != address['IsValid']:
                        # update isValid
                        if data['IsValid'] == 1:
                            # reset other addresses
                            db.execQuery("UPDATE Address SET IsValid = 0 WHERE Id != ? AND BorgerUserId=?", (id, address['BorgerUserId'],))

                # update address
                db.update("Address", data, id)

                # get updated address
                address = db.execQuery("SELECT * FROM Address WHERE Id = ?;", (id,)).fetchone()
                response.status_code = 200
                response_body = address

            else:
                response.status_code = 404
                response_body = {
                    "status": "Resource not found",
                    "message": f"No address with id '{identifier}' was found"}

        except sqlite3.IntegrityError:
            pass
        finally:
            db.close()
    else:
        return gen_bad_request()

    response.data = json.dumps(response_body)
    return response

@app.route("/borger_service/address", methods=["DELETE"])
def delete_address():
    db = sqlite3.connect(db_path)
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.args is None:
        return gen_bad_request()

    id = request.args.get("id")

    if id is None:
        return gen_bad_request()

    db = Database()
    db.connect(db_path)

    address = db.execQuery("SELECT * FROM Address WHERE Id = ?;", (id,)).fetchone()

    if address:
        # check if this address has isValid, if then cancel delete
        if address['IsValid'] == 1:
            response.status_code = 403
            response_body = {
                "message": "Cannot delete an address that is the valid one."
            }
        
        else:
            # delete address
            db.delete("Address", id)
            response.status_code = 200
            response_body = {
                "status": "Resource deleted",
            }

        db.close()

    else:
        # address not found
        response.status_code = 404
        response_body = {
            "status": "Resource not found",
            "message": f"No address with id '{id}' was found"}

    response.data = json.dumps(response_body)
    return response


def gen_bad_request(message = None):
    
    if message is None:
        message = 'Invalid Request'

    response = Response()
    response.headers['Content-Type'] = 'application/json'
    response.status_code = 400
    response.data = json.dumps({
        'message':message
    })
    return response


if __name__ == "__main__":
    # begin server
    app.run(port = 8091)
    