import re
def check_valid_email(email):
    valid_p = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(valid_p,email) is not None

def valid_phone_number(num):
    valid_p = r'^[6-9]\d{9}$'
    return re.match(valid_p, num) is not None

def valid_password(password):
    if len(password) < 8:
        return False ,"password must contain minimum 8 characters"
    if re.search(r'[A-Z]',password):
        return False,"password must contain a  Capital letter"
    if re.search(r'[a-z]',password):
        return False,"password must contain a  Small letter"
    if re.search(r'[0-9]',password):
        return False,"password must contain a number"

def valid_entry_details(data):
    errors = []
    if not data.get('username') or len(data['username'].strip()) < 5:
        errors.append("Username must be at least 5 characters")
    if not data.get('email') or not check_valid_email(data['email']):
        errors.append("Valid email is required")
    if not data.get('password'):
        errors.append("Password is required")
    else:
        valid, msg = valid_password(data['password'])
        if not valid:
            errors.append(msg)
    if data.get('phone') and not valid_phone_number(data['phone']):
        errors.append("Phone number must be valid 10-digit number")
    return errors
