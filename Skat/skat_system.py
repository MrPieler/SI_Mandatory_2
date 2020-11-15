import pathlib
from flask import request, Response, Flask
import json
import sqlite3
from datetime import datetime
import requests

app = Flask(__name__)
app.config["DEBUG"] = True
db_path = f"{pathlib.Path(__file__).parent.absolute()}/skat_db.sqlite3"
db = "skat_db.sqlite3"

# CRUD FOR SkatUser
@app.route("/user", methods=["POST"])
def create_user():
    db = sqlite3.connect(db_path)
    response = Response()

    user_id = request.args.get("user_id")
    if user_id:
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO SkatUser (UserId, CreatedAt, IsActive) VALUES(?, ?, ?);", (user_id, datetime.now(), 1))
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

@app.route("/user", methods=["GET"])
def read_user():
    db = sqlite3.connect(db_path)
    response = Response()

    user_id = request.args.get("user_id")
    if user_id:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM SkatUser WHERE UserId=?;", (user_id,))
        user = rows.fetchone()
        if user:
            response.status_code = 201
            response_body = {"SkatUser":{"Id":user[0], "user_id":user[1], "created_at":user[2], "is_active":user[3]}}
        else:
            response.status_code = 404
            response_body = {
                "Status": "Resource not found",
                "Message": f"No user was found with user_id '{user_id}'"}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To get a user you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/user", methods=["PATCH"])
def update_user():
    db = sqlite3.connect(db_path)
    response = Response()

    identifier = request.args.get("id")
    user_id = request.args.get("user_id")
    if identifier and user_id:
        cursor = db.cursor()
        try:
            cursor.execute("UPDATE SkatUser SET UserId=? WHERE Id=?;", (user_id, identifier))
            cursor.execute("COMMIT")
            if cursor.execute("SELECT * FROM SkatUser WHERE Id=?", (identifier,)).fetchone():
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

@app.route("/user", methods=["DELETE"])
def delete_user():
    db = sqlite3.connect(db_path)
    response = Response()

    user_id = request.args.get("user_id")
    if user_id:
        cursor = db.cursor()
        if cursor.execute("SELECT * FROM SkatUser WHERE UserId=?", (user_id,)).fetchone():
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("DELETE FROM SkatUser WHERE UserId=?;", (user_id,))
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

# CRUD FOR SkatYear
@app.route("/year", methods=["POST"])
def create_year():
    db = sqlite3.connect(db_path)
    response = Response()

    label = request.args.get("label")
    start = request.args.get("start")
    end = request.args.get("end")
    if label and start and end:
        try:
            cursor = db.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            # Create new skat year
            cursor.execute("INSERT INTO SkatYear (Label, CreatedAt, ModifiedAt, StartDate, EndDate) VALUES(?,?,?,?,?);", (label, datetime.now(), None, start, end))
            cursor.execute("COMMIT")

            # Get ID of created year
            year_id = cursor.execute("SELECT * FROM SkatYear WHERE Label=?", (label,)).fetchone()[0]
            
            # Create new skat user year for each user
            users = cursor.execute("SELECT * FROM SkatUser").fetchall()
            
            cursor.execute("PRAGMA foreign_keys = OFF;")
            for user in users:
                cursor.execute("INSERT INTO SkatUserYear (SkatUserId, SkatYearId, UserId, IsPaid, Amount) VALUES(?,?,?,?,?)", (user[0], year_id, user[1], 0, 0))
                cursor.execute("COMMIT")

            response.status_code = 201
            response_body = {
                "status": "Year creation successful"
            }
        except sqlite3.IntegrityError:
            response.status_code = 403
            response_body = {
                "status": "Database integrity error.",
                "message": "label already exists."
            }
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To create a year you must specify a 'label', 'start' and 'end'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/year", methods=["GET"])
def read_year():
    db = sqlite3.connect(db_path)
    response = Response()

    label = request.args.get("label")
    if label:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM SkatYear WHERE Label=?;", (label,))
        year = rows.fetchone()
        if year:
            response.status_code = 201
            response_body = {"SkatYear":{
                "id":year[0],
                "label":year[1],
                "created_at":year[2],
                "modified_at":year[3],
                "start":year[4],
                "end":year[5]
                }}
        else:
            response.status_code = 404
            response_body = {
                "Status": "Resource not found",
                "Message": f"No year was found with label '{label}'"}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To get a year you must specify an 'label'"
        }

    response.data = json.dumps(response_body)
    return response


@app.route("/year", methods=["PATCH"])
def update_year():
    db = sqlite3.connect(db_path)
    response = Response()

    label = request.args.get("label")
    start = request.args.get("start")
    end = request.args.get("end")
    if label and start and end:
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("UPDATE SkatYear SET StartDate=?, EndDate=?, ModifiedAt=? WHERE Label=?;", (start, end, datetime.now(), label))
        cursor.execute("COMMIT")
        if cursor.execute("SELECT * FROM SkatYear WHERE Label=?", (label,)).fetchone():
            response.status_code = 200
            response_body = {"status": "Year successfully updated."}
        else:
            response.status_code = 404
            response_body = {
                "status": "Resource not found",
                "message": f"No year with label '{label}' was found"}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To update a year you must specify a 'label' as well as the 'start' and 'end' dates you which to change to."
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/year", methods=["DELETE"])
def delete_year():
    db = sqlite3.connect(db_path)
    response = Response()

    label = request.args.get("label")
    if label:
        cursor = db.cursor()
        if cursor.execute("SELECT * FROM SkatYear WHERE Label=?", (label,)).fetchone():
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("DELETE FROM SkatYear WHERE Label=?;", (label,))
            cursor.execute("COMMIT")
            response.status_code = 200
            response_body = {"status": f"Year '{label}' successfully deleted"}
        else:
            response.status_code = 404
            response_body = {
                "status": "Resource not found",
                "message": f"No year with label '{label}' was found"}
    else:
        response.status_code = 401
        response_body = {
            "status": "Missing parameters.",
            "message": "To delete a year you must specify a 'label'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/pay-taxes", methods=["POST"])
def pay_taxes():
    db = sqlite3.connect(db_path)
    response = Response()

    user_id = request.args.get("user_id")
    total_amount = request.args.get("total_amount")
    
    cursor = db.cursor()
    try:
        user = cursor.execute("SELECT Id, Amount FROM SkatUserYear WHERE UserId=?;", (user_id,)).fetchone()
        is_paid = 0
        if user[1] > 0:
            is_paid = 1
        tax_money = json.loads(requests.post("http://localhost:7071/api/Skat_Tax_Calculator", data=json.dumps({"money":total_amount})).content).get("tax_money")
        cursor.execute("UPDATE SkatUserYear SET Amount=?, IsPaid=? WHERE UserId=?;", (tax_money, is_paid, user_id))
        cursor.execute("COMMIT")
        response.status_code = 200
        response_body = {"status":"Successfully completed payment resgistration."}
    except TypeError:
        response.status_code = 403
        response_body = {"status": "user_id not found."}

    response.data = json.dumps(response_body)
    return response




if __name__ == "__main__":
    # begin server
    app.run(host="localhost", port = 8081, threaded=True)
    