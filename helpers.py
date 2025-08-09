from flask import redirect, render_template, request, session
from string import ascii_uppercase, digits, punctuation

# Apology function with the default error number of 400
def apology(message, error=400):

    # Escape special characters in string s so that img src works
    def escape(s):
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=error, bottom=escape(message))

# Checks if password meets certain requirements
def pwcheck(password):

    # Minimum 12 characters
    if len(password) < 12:
        return False

    # Password contains at least an uppercase letter, a number, and a special character
    uppercase = digit = punct = False
    for character in password:
        if character in ascii_uppercase:
            uppercase = True
        elif character in digits:
            digit = True
        elif character in punctuation:
            punct = True

    if uppercase == True and digit == True and punct == True:
        return True

    return False
