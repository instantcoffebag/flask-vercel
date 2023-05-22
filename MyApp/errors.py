def error_message(message):
    if message == f' "INVALID_PASSWORD"' or message == f' "EMAIL_NOT_FOUND"':
        return "incorrect email or password"
    return None
