def handler(request):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain",
            "Access-Control-Allow-Origin": "*"
        },
        "body": "ok"
    }
