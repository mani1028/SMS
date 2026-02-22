def success_response(message="", data=None, code=200):
    """Standard success response format"""
    return {
        "status": True,
        "message": message,
        "data": data or {}
    }, code


def error_response(message="", code=400, data=None):
    """Standard error response format"""
    return {
        "status": False,
        "message": message,
        "data": data or {}
    }, code
