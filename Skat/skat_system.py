import pathlib
from flask import request, Response, Flask
import json
import sqlite3
from datetime import datetime
import requests
from database import Database

app = Flask(__name__)
app.config["DEBUG"] = True
db_path = f"{pathlib.Path(__file__).parent.absolute()}/skat_db.sqlite3"
db = "skat_db.sqlite3"

# CRUD FOR SkatUser
@app.route("/skat/user", methods=["POST"])
def create_user():
    db = sqlite3.connect(db_path)
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.json is None:
        return gen_bad_request()

    user_id = request.json.get("user_id")

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

@app.route("/skat/user", methods=["GET"])
def read_user():
    db = sqlite3.connect(db_path)
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    user_id = request.args.get("user_id")

    if user_id:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM SkatUser WHERE UserId=?;", (user_id,))
        user = rows.fetchone()
        if user:
            response.status_code = 200
            response_body = {"SkatUser":{"Id":user[0], "user_id":user[1], "created_at":user[2], "is_active":user[3]}}
        else:
            response.status_code = 404
            response_body = {
                "Status": "Resource not found",
                "Message": f"No user was found with user_id '{user_id}'"}
    else:
        response.status_code = 400
        response_body = {
            "status": "Missing parameters.",
            "message": "To get a user you must specify a 'user_id'"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/skat/user", methods=["PATCH"])
def update_user():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.args is None or request.json is None:
        return gen_bad_request()

    identifier = request.args.get("id")
    user_id = request.json.get("user_id")
    is_active = request.json.get("is_active")

    if identifier is None:
        return gen_bad_request()

    data = {}

    if is_active is not None:
        data['IsActive'] = 1 if is_active == True else 0
    
    if user_id:
        data['UserId'] = user_id

    if not data:
        return gen_bad_request()

    print(data)

    db = Database()
    db.connect(db_path)

    try:
        db.update("SkatUser", data, identifier)

        skat_user = db.execQuery("SELECT * FROM SkatUser WHERE Id = ?;", (identifier,)).fetchone()

        if skat_user:
            response.status_code = 200
            response_body = skat_user
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
    finally:
        db.close()

    response.data = json.dumps(response_body)
    return response

@app.route("/skat/user", methods=["DELETE"])
def delete_user():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.args is None:
        return gen_bad_request()

    id = request.args.get("id")

    if not id:
        return gen_bad_request()

    db = Database()
    db.connect(db_path)

    try:
        db.delete("SkatUser", id)
        response.status_code = 200
        response_body = {"status": f"User with id:'{id}' successfully deleted"}

    except sqlite3.IntegrityError:
        response.status_code = 403
        response_body = {
            "status": "Integrity error",
            "message": "Cannot delete skat user because of relation constraints"}
    else:
        db.close()

    response.data = json.dumps(response_body)
    return response

# CRUD FOR SkatYear
@app.route("/skat/year", methods=["POST"])
def create_year():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if not request.json:
        return gen_bad_request()
    
    label = request.json.get("label")
    start = request.json.get("start")
    end = request.json.get("end")

    if label is None or start is None or end is None:
        return gen_bad_request()
    
    db = Database()
    db.connect(db_path)

    try:
        data = {
            "Label": label,
            "CreatedAt": datetime.now(),
            "ModifiedAt": None,
            "StartDate": start,
            "EndDate": end
        }

        cur = db.insert("SkatYear", data)
        skat_year = db.execQuery("SELECT * FROM SkatYear WHERE Id = ?", (cur.lastrowid,)).fetchone()

        # get all users
        users = db.execQuery("SELECT * FROM SkatUser").fetchall()

        for user in users:

            skat_user_year = {
                "SkatUserId": user['Id'],
                "SkatYearId": skat_year['Id'],
                "UserId": user['UserId'],
                "IsPaid": 0,
                "Amount": 0
            }

            db.insert("SkatUserYear", skat_user_year)

        response.status_code = 201
        response_body = skat_year
        
    except sqlite3.IntegrityError:
            response.status_code = 403
            response_body = {
                "status": "Database integrity error.",
                "message": "label already exists."
            }

    finally:
        db.close()

    response.data = json.dumps(response_body)
    return response

@app.route("/skat/year", methods=["GET"])
def read_year():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.args is None:
        return gen_bad_request()

    id = request.args.get("id")

    if not id:
        return gen_bad_request()

    db = Database()
    db.connect(db_path)

    skat_year = db.execQuery("SELECT * FROM SkatYear WHERE Id = ?;", (id,)).fetchone()

    if skat_year:
        response.status_code = 200
        response_body = skat_year
    else:
        response.status_code = 404
        response_body = {
            "Status": "Resource not found",
            "Message": "No skat year exists with given id"}

    db.close()

    response.data = json.dumps(response_body)
    return response


@app.route("/skat/year", methods=["PATCH"])
def update_year():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.args is None or request.json is None:
        return gen_bad_request()

    id = request.args.get("id")
    label = request.json.get("label")
    start = request.json.get("start")
    end = request.json.get("end")

    if not id:
        return gen_bad_request()

    data = {}

    if label:
        data["Label"] = label
    
    if start:
        data["StartDate"] = start

    if end:
        data["EndDate"] = end 

    if not data:
        return gen_bad_request()

    data["ModifiedAt"] = datetime.now()

    db = Database()
    db.connect(db_path)

    #check if exists
    if not db.execQuery("SELECT * FROM SkatYear WHERE Id = ?;", (id,)).fetchone():
        response.status_code = 404
        response_body = {
            "status": "Resource not found",
            "message": "No skat year with the given id"
        }
    else:
        db.update("SkatYear", data, id)
        # get updated skat year
        skat_year = db.execQuery("SELECT * FROM SkatYear WHERE Id = ?;", (id,)).fetchone()

        response.status_code = 200
        response_body = skat_year

    response.data = json.dumps(response_body)
    return response

@app.route("/skat/year", methods=["DELETE"])
def delete_year():
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if request.args is None:
        return gen_bad_request()

    id = request.args.get("id")

    if not id:
        return gen_bad_request()

    db = Database()
    db.connect(db_path)

    skat_year = db.execQuery("SELECT * FROM SkatYear WHERE Id = ?;", (id,)).fetchone()

    if skat_year:
        db.delete("SkatYear", id)
        response.status_code = 200
        response_body = {"status": "Skat Year deleted"}
    else:
        response.status_code = 404
        response_body = {
            "status": "Resource not found",
            "message": "No skat year with the given id"
        }

    response.data = json.dumps(response_body)
    return response

@app.route("/skat/pay-taxes", methods=["POST"])
def pay_taxes():
    db = sqlite3.connect(db_path)
    response = Response()
    response.headers['Content-Type'] = 'application/json'

    if not request.args or not request.json:
        return gen_bad_request()

    user_id = request.args.get("user_id")
    total_amount = request.json.get("total_amount")

    if not user_id or not total_amount:
        return gen_bad_request()
    
    cursor = db.cursor()
    try:
        user = cursor.execute("SELECT Id, Amount FROM SkatUserYear WHERE UserId=?;", (user_id,)).fetchone()
        if user[1] <= 0:
            resp = requests.post("http://localhost:7071/api/Skat_Tax_Calculator", json={"amount":total_amount})
            tax_money = json.loads(resp.content).get("tax_money")
            cursor.execute("UPDATE SkatUserYear SET Amount=?, IsPaid=? WHERE UserId=?;", (tax_money, 1, user_id))
            cursor.execute("COMMIT")

            # Withdraw money from bank account
            resp = requests.post("http://127.0.0.1:8090/bank/bank_user/withdraw", json={"UserId":user_id, "Amount":tax_money})
            if resp.status_code == 200:
                response.status_code = 200
                response_body = {"status":"Successfully completed payment resgistration."}
            else:
                response.status_code = 500
                response_body = {"status":"An error occoured during bank account withdrawal"}
        else:
            response.status_code = 200
            response_body = {"status":"User has already paid tax. Payment cancelled."}


    except TypeError:
        response.status_code = 403
        response_body = {"status": "user_id not found."}

    response.data = json.dumps(response_body)
    return response


def gen_bad_request():
    response = Response()
    response.headers['Content-Type'] = 'application/json'
    response.status_code = 400
    response.data = json.dumps({
        'message':'invalid request'
    })
    return response


if __name__ == "__main__":
    # begin server
    app.run(host="localhost", port = 8092, threaded=True)
    