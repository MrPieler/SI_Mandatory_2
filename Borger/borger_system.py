import pathlib
from flask import request, Response, Flask
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config["DEBUG"] = True
db_path = f"{pathlib.Path(__file__).parent.absolute()}/borger_db.sqlite3"

# CRUD FOR Borger
@app.route("/borger_service/borger", methods=["POST"])
def create_borger():
    db = sqlite3.connect(db_path)
    response = Response()

    user_id = request.args.get("user_id")
    if user_id:
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO BorgerUser (UserId, CreatedAt) VALUES(?, ?);", (user_id, datetime.now()))
            cursor.execute("COMMIT")
            response.status_code = 201
            response_body = {
                "status": "Creation successful"
            }
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
    
    user_id = request.args.get("user_id")
    if user_id:
        try:
            cursor = db.cursor()
            rows = cursor.execute("SELECT * FROM BorgerUser WHERE UserId=?;", (user_id,))
            response.status_code = 201
            user = rows.fetchone()
            response_body = {"BorgerUser":{"Id":user[0], "user_id":user[1], "CreatedAt":user[2]}}
        except TypeError:
            response.status_code = 403
            response_body = {"Status":f"user_id '{user_id}' not found."}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To get a user you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/borger_service/borger", methods=["PATCH"])
def update_borger():
    db = sqlite3.connect(db_path)
    response = Response()

    identifier = request.args.get("id")
    user_id = request.args.get("user_id")
    if identifier and user_id:
        cursor = db.cursor()
        try:
            cursor.execute("UPDATE BorgerUser SET UserId=? WHERE Id=?;", (user_id, identifier))
            cursor.execute("COMMIT")
            if cursor.execute("SELECT * FROM BorgerUser WHERE Id=?", (identifier,)).fetchone():
                response.status_code = 200
                response_body = {"status": "User successfully updated."}
            else:
                response.status_code = 404
                response_body = {
                    "status": "Resource not found",
                    "message": f"No user with id '{identifier}' was found"}
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
            "message": "To update a user you must specify an 'id' and the new user_id you wish to change to"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/borger_service/borger", methods=["DELETE"])
def delete_borger():
    db = sqlite3.connect(db_path)
    response = Response()

    user_id = request.args.get("user_id")
    if user_id:
        cursor = db.cursor()
        if cursor.execute("SELECT * FROM BorgerUser WHERE UserId=?", (user_id,)).fetchone():
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("DELETE FROM BorgerUser WHERE UserId=?;", (user_id,))
            cursor.execute("COMMIT")
            response.status_code = 200
            response_body = {"status": f"User '{user_id}' successfully deleted"}
        else:
            response.status_code = 404
            response_body = {
                "status": "Resource not found",
                "message": f"No user with user_id '{user_id}' was found"}
    else:
        response.status_code = 401
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

    user_id = request.args.get("user_id")
    street = request.args.get("street")
    if user_id and street:
        cursor = db.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON;")
            # Change current active address for user
            cursor.execute("UPDATE Address SET IsValid = 0 WHERE BorgerUserId=?", (user_id,))
            # Insert new address
            cursor.execute("INSERT INTO Address (BorgerUserId, Street, CreatedAt, IsValid) VALUES(?,?,?,?);", (user_id, street, datetime.now(), 1))
            cursor.execute("COMMIT")
            response.status_code = 201
            response_body = {
                "status": "Address creation successful"
            }
        except sqlite3.IntegrityError:
            response.status_code = 403
            response_body = {
                "status": "Database integrity error.",
                "message": "user_id not found."
            }
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To create an address you must specify a 'user_id' and 'street' to create an address"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/borger_service/address", methods=["GET"])
def read_address():
    db = sqlite3.connect(db_path)
    response = Response()

    user_id = request.args.get("user_id")
    if user_id:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM Address WHERE BorgerUserId=?;", (user_id,))
        response.status_code = 201
        addresses = {}
        i = 1
        for address in rows.fetchall():
            addresses[f"Address {i}"] = {
                "id":address[0],
                "user_id":address[1],
                "street":address[2],
                "created_at":address[3],
                "active":bool(address[4])}
            i += 1
        response_body = {"Addresses":addresses}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To get an address you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response


@app.route("/borger_service/address", methods=["PATCH"])
def update_address():
    db = sqlite3.connect(db_path)
    response = Response()

    identifier = request.args.get("id")
    street = request.args.get("street")
    if identifier and street:
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("UPDATE BorgerUser SET Street=? WHERE Id=?;", (street, identifier))
        cursor.execute("COMMIT")
        if cursor.execute("SELECT * FROM Address WHERE Id=?", (identifier,)).fetchone():
            response.status_code = 200
            response_body = {"status": "Address successfully updated."}
        else:
            response.status_code = 404
            response_body = {
                "status": "Resource not found",
                "message": f"No address with id '{identifier}' was found"}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To update an address you must specify an 'id' and the new street you wish to change to"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/borger_service/address", methods=["DELETE"])
def delete_address():
    db = sqlite3.connect(db_path)
    response = Response()

    identifier = request.args.get("id")
    if identifier:
        cursor = db.cursor()
        if cursor.execute("SELECT * FROM Address WHERE Id=?", (identifier,)).fetchone():
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("DELETE FROM Address WHERE Id=?;", (identifier,))
            cursor.execute("COMMIT")
            response.status_code = 200
            response_body = {"status": f"Address '{identifier}' successfully deleted"}
        else:
            response.status_code = 404
            response_body = {
                "status": "Resource not found",
                "message": f"No address with id '{identifier}' was found"}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To delete an address you must specify an 'id'"
        }

    response.data = json.dumps(response_body)
    return response

if __name__ == "__main__":
    # begin server
    app.run(port = 8091)
    