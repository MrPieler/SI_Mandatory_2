import pathlib
from flask import request, Response, Flask
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config["DEBUG"] = True
cwd = pathlib.Path(__file__).parent.absolute()

# CRUD FOR Borger
@app.route("/borger", methods=["POST"])
def create_borger():
    db = sqlite3.connect(f"{cwd}/borger_db.sqlite3")
    response = Response()

    user_id = request.json.get("user_id")
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

@app.route("/borger", methods=["GET"])
def read_borger():
    db = sqlite3.connect(f"{cwd}/borger_db.sqlite3")
    response = Response()

    user_id = request.json.get("user_id")
    if user_id:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM BorgerUser WHERE UserId=?;", (user_id,))
        response.status_code = 201
        user = rows.fetchone()
        response_body = {"BorgerUser":{"Id":user[0], "user_id":user[1], "CreatedAt":user[2]}}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To get a user you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/borger", methods=["PATCH"])
def update_borger():
    db = sqlite3.connect(f"{cwd}/borger_db.sqlite3")
    response = Response()

    identifier = request.json.get("id")
    user_id = request.json.get("user_id")
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
            "message": "To get a user you must specify an 'id' and the new user_id you wish to change to 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/borger", methods=["DELETE"])
def delete_borger():
    db = sqlite3.connect(f"{cwd}/borger_db.sqlite3")
    response = Response()

    user_id = request.json.get("user_id")
    if user_id:
        cursor = db.cursor()
        if cursor.execute("SELECT * FROM BorgerUser WHERE UserId=?", (user_id,)).fetchone():
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
@app.route("/address", methods=["POST"])
def create_address():
    db = sqlite3.connect(f"{cwd}/borger_db.sqlite3")
    response = Response()

    user_id = request.json.get("user_id")
    if user_id:
        cursor = db.cursor()
        cursor.execute("INSERT INTO Address (BorgerUserId, CreatedAt, IsValid) VALUES(?, ?, ?);", (user_id, datetime.now(), 1))
        cursor.execute("COMMIT")
        response.status_code = 201
        response_body = {
            "status": "Creation successful"
        }
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To create an address you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/address", methods=["GET"])
def read_address():
    db = sqlite3.connect(f"{cwd}/borger_db.sqlite3")
    response = Response()

    user_id = request.json.get("user_id")
    if user_id:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM Address WHERE UserId=?;", (user_id,))
        response.status_code = 201
        address = rows.fetchone()
        response_body = {"Address":{"Id":address[0], "user_id":address[1], "CreatedAt":address[2], "IsActive":address[3]}}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To get an address you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response


######################## NÅET HERTIL
@app.route("/address", methods=["PATCH"])
def update_address():
    db = sqlite3.connect(f"{cwd}/borger_db.sqlite3")
    response = Response()

    identifier = request.json.get("id")
    user_id = request.json.get("user_id")
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
            "message": "To get a user you must specify an 'id' and the new user_id you wish to change to 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/address", methods=["DELETE"])
def delete_address():
    db = sqlite3.connect(f"{cwd}/borger_db.sqlite3")
    response = Response()

    user_id = request.json.get("user_id")
    if user_id:
        cursor = db.cursor()
        if cursor.execute("SELECT * FROM BorgerUser WHERE UserId=?", (user_id,)).fetchone():
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

if __name__ == "__main__":
    # begin server
    app.run(port = 8080)
    