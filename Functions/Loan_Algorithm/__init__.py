import logging
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(status_code=404)
    else:

        loan_amount = req_body.get('loan_amount')
        total_amount = req_body.get('total_amount')

        # validate request
        if loan_amount is None or total_amount is None:
            return send_bad_request()

        if is_number(loan_amount) is False or is_number(total_amount) is False:
            # invalid request, params not numbers
            return send_bad_request_numbers()

        if loan_amount <= 0 or total_amount < 0:
            return send_bad_request_numbers()

    
        # valid request
        # check for sufficent funds
        available_funds = total_amount * 0.75
        if loan_amount > available_funds:
            # insufficient funds
            return send_insufficent_funds_response()
        
        # sufficient funds
        return func.HttpResponse(status_code=200)

def is_number(amount):
    return type(amount) == int or type(amount) == float

def send_insufficent_funds_response():
    return func.HttpResponse(status_code=403, body=json.dumps({
                        "message": 'insufficient funds'
                        }))

def send_bad_request():
    return func.HttpResponse(status_code=403, body=json.dumps({
                        "message": 'invalid requst'
                        }))

def send_bad_request_numbers():
    return func.HttpResponse(status_code=403, body=json.dumps({
                        "message": 'loan_amount/total_amount must be positive numbers'
                        }))
