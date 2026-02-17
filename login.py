def username_check(username):
    if len(username) < 5:
        return "Username must be at least 5 characters long."
    
    elif len(username) > 25:
        return "Username cannot be more than 25 characters long."
    
    elif username.isspace():
        return "Username cannot contain only spaces."
    
    elif not username.isalpha():
        return "Username can only contain letters."
    
    else:
        return username
    
    
def password_check(password, user):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    
    if password.isspace():
        return "Password cannot contain only spaces."
    
    if password.isdigit():
        return "Password cannot contain only digits."
    
    if not any(c.isalpha() for c in password):
        return "Password must contain at least one letter."
    
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    
    if password.lower() == user.lower():
        return "Username and password cannot be the same."
    
    return password



def login_check(username, password):
    if username_check(username) is not True:
        return "Username check failed. Please try again!"
    else:
        if password_check(password, username) is not True:
            return "Password check failed. Please try again!"
        else:
            return True
        
