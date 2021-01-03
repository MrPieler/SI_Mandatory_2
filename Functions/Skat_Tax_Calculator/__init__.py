import logging
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(status_code=400, body=json.dumps({
                        "message": 'body required with an amount'
                        }), headers=get_header())
    else:
        amount = req_body.get('amount')

        if amount is None:
            return func.HttpResponse(status_code=400, body=json.dumps({
                        "message": 'amount required'
                        }), headers=get_header())

        # check for valid request
        if type(amount) != int and type(amount) != float:
            return func.HttpResponse(status_code=400, body=json.dumps({
                        "message": 'amount must be a valid positive number'
                        }), headers=get_header())

        if amount < 0:
            return func.HttpResponse(status_code=400, body=json.dumps({
                        "message": 'amount required must be positive'
                        }), headers=get_header())

        tax_percentage = 0.10
        tax_money = float(amount) * tax_percentage
        return func.HttpResponse(status_code=200, body=json.dumps({"tax_money": tax_money}), headers=get_header())
        
def get_header():
    return {'Content-Type': 'application/json'}