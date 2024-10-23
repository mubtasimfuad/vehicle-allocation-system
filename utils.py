# Description: This file contains the utility functions used in the application.

def get_response(status=400, error=True, code="GENERIC", message="NA", data={}):

    return {
        "statusCode": status,
        "error": error,
        "code": code,
        "message": message,
        "data": data,
    }
