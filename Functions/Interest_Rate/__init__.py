import logging
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    print('sefsefsefsef------------------')
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(status_code=400, body=json.dumps({
                        "message": 'amount required, must be a positive number'
                        }), headers=get_header())
    else:

        amount = req_body.get('amount')

        # check for valid request
        if type(amount) != int and type(amount) != float:  
            return send_bad_request()
        if amount <= 0:
            return send_bad_request()

        interest_rate = 0.02
        amount_with_interest = float(amount) * interest_rate + amount
        return func.HttpResponse(status_code=200, body=json.dumps({"amount": amount_with_interest}), headers=get_header())


def send_bad_request():
    return func.HttpResponse(status_code=400, body=json.dumps({
                        "message": 'amount must be a positive number'
                        }), headers=get_header())

def get_header():
    return {'Content-Type': 'application/json'}
