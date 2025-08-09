from cs50 import SQL
from datetime import datetime
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from functools import wraps
from urllib.parse import urlparse
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, pwcheck

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"]= False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///taskhero.db")

# Global Variables
PRIORITIES = ["Low", "Medium", "High", "Non-Applicable"]
TYPES = ["Education", "Health", "Others", "Personal", "Social", "Shopping", "Work"]
HEADERS = ["Type", "Description", "Priority", "Due Date", "Status", "Datetime Added", "Datetime Last Edited", "Datetime Completed"]

# Decorator that checks if user is logged in or not
# login_required is a decorator function that takes another function f (the route handler function) as an argument
def login_required(f):

    # Applied to the inner function to ensure it retains the original function’s attributes
    @wraps(f)

    # decorated_function is the inner function that will be executed in place of the original function f
    # *args and **kwargs are used to pass any arguments and keyword arguments to the original function f,
    # where *args is used to pass a variable number of non-keyword arguments to a function and
    # **kwargs is used to pass a variable number of keyword i.e. key-value arguments to a function
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")

        # the original function f is called with its original arguments and keyword arguments
        return f(*args, **kwargs)

    # This is where the user is checked whether they are logged in or not i.e. when decorated_function is executed after defining it
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    # If the form was submitted
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Checks if there is input
        if not username or not password:
            return apology("Blank input(s)", 400)

        # Queries a list of dictionaries with that username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Checks if there is one item in the array i.e. if username exists or if username and password match
        if len(rows) != 1 or check_password_hash(rows[0]["hash"], password) == False:
            return apology("Invalid username and/or password", 400)

        # Remember which user has logged in and storing it in a global variable
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to the homepage
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    # Checks if the key user_id exists i.e. a session has started
    if "user_id" in session:

        # Removes 'datetime completed' sort by option at homepage
        HEADERSINDEX = HEADERS.copy()
        HEADERSINDEX.remove("Status")
        HEADERSINDEX.remove("Datetime Completed")

        user = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])

        # If the sort form was submitted
        if request.method == "POST":
            sort = request.form.get("sort")

            # Validates the sort string to prevent injection attacks since {} is used instead of ? in ORDER BY
            if sort not in HEADERSINDEX:
                return apology("Invalid sort criteria", 400)

            # Removes the dropdown option in select
            HEADERSINDEX.remove(sort)

            # Stores the value of sort (for user friendly purposes)
            option = sort

            # Replaces the value of sort with the name of the column of the table
            # Creates a dictionary
            sort_options = {
                "Due Date": "duedate",
                "Datetime Added": "datetime_added",
                "Datetime Last Edited": "datetime_edited"
            }

            # dict.get(user_input, default_value)
            # user_input is the column name selected by the user, and default_value is the value you want to use if the user's input doesn't match any of the keys in the dictionary
            sort = sort_options.get(sort, option)

            # If sort criteria is priority
            if sort == "Priority":
                # Custom order i.e. not in alphabetical order but from High, Medium to Low
                tasks = db.execute("SELECT * FROM tasks WHERE username = ? AND status = ? ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END",
                                   user[0]["username"], "uncompleted")

            else:
                # Note: ORDER BY cannot use ? placeholder. Need to use {} and "query".format(sort)
                tasks = db.execute("SELECT * FROM tasks WHERE username = ? AND status = ? ORDER BY {}".format(sort),
                                    user[0]["username"], "uncompleted")

            return render_template("index.html", tasks=tasks, headers=HEADERSINDEX, option=option)


        # If the page was accessed via URL and not sorted by anything
        else:
            # Queries the table tasks stored in a list of dictionaries in tasks and is sorted by Datetime Added by default
            tasks = db.execute("SELECT * FROM tasks WHERE username = ? AND status = ? ORDER BY {}".format("datetime_added"),
                               user[0]["username"], "uncompleted")

            HEADERSINDEX.remove("Datetime Added")
            option = "Sort by"

            return render_template("index.html", tasks=tasks, headers=HEADERSINDEX, option=option)


    else:
        return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    # If form was submitted
    if request.method == "POST":
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        # Validates user input
        if not username or not password1 or not password2:
            return apology("Blank input(s)", 400)

        if password1 != password2:
            return apology("Passwords do not match", 400)

        # Strong password used
        if pwcheck(password1) == False:
            return apology("Password must be at least 12 characters long and contain at least one uppercase letter, one digit, and one special character", 400)

        # Check if username is already taken
        if db.execute("SELECT user_id FROM users WHERE username = ?", username):
            return apology("Username already taken", 400)

        # Hashes password
        hashed = generate_password_hash(password1)

        # Insert into users table a new user row
        db.execute("INSERT INTO users (username, hash) VALUES(?,?)", username, hashed)

        # Redirects user to log in
        return redirect("/login")

    else:
        return render_template("register.html")

@app.route("/logout")
@login_required
def logout():

    # Clears the session
    session.clear()

    # Returns user to log in page
    return redirect("/login")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    # If form was submitted
    if request.method == "POST":
        type = request.form.get("type")
        description = request.form.get("description")
        # Replace the T in the datetime-local input type
        duedate = (request.form.get("duedate")).replace('T', ' ')
        priority = request.form.get("priority")

        # Gets the current time
        time = datetime.now()

        # Validates user input
        if not type or not description or not duedate or not priority:
            return apology("Blank input(s)", 400)

        if type not in TYPES or priority not in PRIORITIES:
            return apology("Invalid type and/or priority", 400)

        # If task already exists
        user = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
        descriptions = db.execute("SELECT description FROM tasks WHERE username = ?", user[0]["username"])
        for dict in descriptions:
            if dict["description"] == description:
                return apology("Task already exists")

        # Inserts into tasks table
        db.execute("INSERT INTO tasks (description, type, priority, status, duedate, datetime_added, username) VALUES(?, ?, ?, 'uncompleted', ?, ?, ?)",
                   description, type, priority, duedate, time, user[0]["username"])

        # Redirects user to the add page
        return redirect("/add")

    else:
        return render_template("add.html", types=TYPES, priorities=PRIORITIES)

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    # If form is submitted
    if request.method == "POST":
        # Checks if list of tasks exist i.e. user checked at least one checkbox
        if not request.form.get("task"):
            return apology("Blank input(s)", 400)

        # Gets a list of tasks with name="task"
        tasks = request.form.getlist("task")

        # Deletes the tasks
        for task in tasks:
            db.execute("DELETE FROM tasks WHERE task_id = ?", task)

        return redirect("/delete")

    else:
        user = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
        tasks = db.execute("SELECT * FROM tasks WHERE username = ?", user[0]["username"])
        return render_template("delete.html", tasks=tasks)

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():

    # If form was submitted
    if request.method == "POST":
        task_id = request.form.get("task")

        # Queries the specific task which is a list of a dictionary that the user wants to edit
        task = db.execute("SELECT * FROM tasks WHERE task_id = ?", task_id)

        # Removes from the options in the select form (note that lists can only be copied via .copy() method)
        TYPES2 = TYPES.copy()
        PRIORITIES2 = PRIORITIES.copy()
        TYPES2.remove(task[0]["type"])
        PRIORITIES2.remove(task[0]["priority"])

        # Saves the route that accessed this route
        referrer = request.referrer
        result = urlparse(referrer)

        return render_template("edit.html", task=task, types=TYPES2, priorities=PRIORITIES2, path=result.path)

    else:
        return redirect("/")

@app.route("/edited", methods=["GET", "POST"])
@login_required
def edited():

    # If form was submitted
    if request.method == "POST":

        type = request.form.get("type")
        description = request.form.get("description")
        # Replace the T in the datetime-local input type
        duedate = (request.form.get("duedate")).replace('T', ' ')
        priority = request.form.get("priority")
        task_id = request.form.get("task_id")
        path = request.form.get("path")

        # Gets the current time
        time = datetime.now()

        db.execute("UPDATE tasks SET type = ?, description = ?, duedate = ?, priority = ?, datetime_edited = ? WHERE task_id = ?",
                   type, description, duedate, priority, time, task_id)

        return redirect(path)


    else:
        return redirect("/")

@app.route("/complete", methods=["GET", "POST"])
@login_required
def complete():

    # If form was submitted
    if request.method == "POST":
        task_id = request.form.get("task")
        time = datetime.now()

        # Changes the columns status and datetime_completed
        db.execute("UPDATE tasks SET status = ?, datetime_completed = ? WHERE task_id = ?",
                   "completed", time, task_id)

        # Redirects to the route that accessed this route
        referrer = request.referrer
        result = urlparse(referrer)

        return redirect(result.path)

    else:
        return redirect("/")

@app.route("/completed", methods=["GET", "POST"])
@login_required
def completed():
    HEADERSCOMPLETED = HEADERS.copy()
    HEADERSCOMPLETED.remove("Due Date")

    user = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])

    if request.method == "POST":
        sort = request.form.get("sort")

        # Validate user input
        if sort not in HEADERSCOMPLETED:
            return apology("Invalid sort criteria", 400)

        # Removes the dropdown option in select
        HEADERSCOMPLETED.remove(sort)

        # Stores the value of sort (for user friendly purposes)
        option = sort

        # Replaces the value of sort with the name of the column of the table
        # Creates a dictionary
        sort_options = {
            "Datetime Added": "datetime_added",
            "Datetime Last Edited": "datetime_edited",
            "Datetime Completed": "datetime_completed"
        }

        # dict.get(user_input, default_value)
        # user_input is the column name selected by the user, and default_value is the value you want to use if the user's input doesn't match any of the keys in the dictionary
        sort = sort_options.get(sort, option)

        # If sort criteria is priority
        if sort == "Priority":
            # Custom order i.e. not in alphabetical order but from High, Medium to Low
            tasks = db.execute("SELECT * FROM tasks WHERE username = ? AND status = ? ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END",
                               user[0]["username"], "completed")

        else:
            # Note: ORDER BY cannot use ? placeholder. Need to use {} and "query".format(sort)
            tasks = db.execute("SELECT * FROM tasks WHERE username = ? AND status = ? ORDER BY {}".format(sort),
                                user[0]["username"], "completed")

        return render_template("completed.html", tasks=tasks, headers=HEADERSCOMPLETED, option=option)

    if request.method == "GET":

        # Sorts table by datetime completed by default
        HEADERSCOMPLETED.remove("Datetime Completed")
        option = "Sort by"
        tasks = db.execute("SELECT * FROM tasks WHERE username = ? AND status = ? ORDER BY {}".format("datetime_completed"),
                           user[0]["username"], "completed")

        return render_template("completed.html", headers=HEADERSCOMPLETED, option=option, tasks=tasks)

@app.route("/uncomplete", methods=["GET", "POST"])
@login_required
def uncomplete():

    # If form was submitted
    if request.method == "POST":
        task_id = request.form.get("task")

        # Change status of task to uncompleted
        db.execute("UPDATE tasks SET status = ?, datetime_completed = ? WHERE task_id = ?", "uncompleted", "None", task_id)

        # Requests the URL of the route that redirected it to this route, be it from /completed or from /history
        referrer = request.referrer

        # Parses the URL of the route, returing result.scheme, result.netloc, result.path (which is what we need)
        result = urlparse(referrer)

        return redirect(result.path)

    # If page was accessed via URL
    else:
        return render_template("/completed")

"""
@app.route("/sort", methods=["GET", "POST"])
@login_required
def sort():
    # If form was submitted
    if request.method == "POST":
        sort = request.form.get("sort")

        # Queries the table tasks stored in a list of dictionaries in tasks
        user = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
        tasks = db.execute("SELECT * FROM tasks WHERE username = ? AND status = ? SORT BY ?", user[0]["username"], "uncompleted", sort)

        return render_template("index.html", tasks=tasks, headers=HEADERSINDEX)

    else:
        return redirect("/")
"""

@app.route("/history", methods=["GET", "POST"])
@login_required
def history():

    # Creates list of selectors specific to /history
    HEADERSHISTORY = HEADERS.copy()

    user = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])

    # If form was submitted
    if request.method == "POST":
        sort = request.form.get("sort")

        # Validate user input
        if sort not in HEADERSHISTORY:
            return apology("Invalid sort criteria", 400)

        # Removes the dropdown option in select
        HEADERSHISTORY.remove(sort)

        # Stores the value of sort (for user friendly purposes)
        option = sort

        # Replaces the value of sort with the name of the column of the table
        # Creates a dictionary
        sort_options = {
            "Due Date": "duedate",
            "Datetime Added": "datetime_added",
            "Datetime Last Edited": "datetime_edited",
            "Datetime Completed": "datetime_completed"
        }

        # dict.get(user_input, default_value)
        # user_input is the column name selected by the user, and default_value is the value you want to use if the user's input doesn't match any of the keys in the dictionary
        sort = sort_options.get(sort, option)

        # If sort criteria is priority
        if sort == "Priority":
            # Custom order i.e. not in alphabetical order but from High, Medium to Low
            tasks = db.execute("SELECT * FROM tasks WHERE username = ? ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END", user[0]["username"])

        else:
            # Note: ORDER BY cannot use ? placeholder. Need to use {} and "query".format(sort)
            tasks = db.execute("SELECT * FROM tasks WHERE username = ? ORDER BY {}".format(sort),
                                user[0]["username"])

        return render_template("history.html", tasks=tasks, headers=HEADERSHISTORY, option=option)

    if request.method == "GET":

        # Sorts table by datetime added by default
        HEADERSHISTORY.remove("Datetime Added")
        option = "Sort by"
        tasks = db.execute("SELECT * FROM tasks WHERE username = ? ORDER BY {}".format("datetime_added"),
                           user[0]["username"])

        return render_template("history.html", headers=HEADERSHISTORY, option=option, tasks=tasks)

@app.route("/changepassword")
@login_required
def changepassword():
    return render_template("changepassword.html")

@app.route("/changedpassword", methods=["GET", "POST"])
@login_required
def changedpassword():
    # If form was submitted
    if request.method == "POST":
        currentpassword = request.form.get("currentpassword")
        newpassword1 = request.form.get("newpassword1")
        newpassword2 = request.form.get("newpassword2")

        hash = db.execute("SELECT hash FROM users WHERE user_id = ?", session["user_id"])

        # Validate user input
        if not currentpassword or not newpassword1 or not newpassword2:
            return apology("Blank input(s)", 400)

        if check_password_hash(hash[0]["hash"], currentpassword) == False:
            return apology("Wrong Password", 400)

        if newpassword1 != newpassword2:
            return apology("Passwords do not match", 400)

        if pwcheck(newpassword1) == False:
            return apology("Password must be at least 12 characters long and contain at least one uppercase letter, one digit, and one special character", 400)

        hashed = generate_password_hash(newpassword1)

        # Updates users table with new hashed password
        db.execute("UPDATE users SET hash = ? WHERE user_id = ?", hashed, session["user_id"])

        # Logs user out
        session.clear()

        return redirect("/login")

    else:
        return redirect("/")

@app.route("/changeusername")
@login_required
def changeusername():
    return render_template("changeusername.html")

@app.route("/changedusername", methods=["GET", "POST"])
@login_required
def changedusername():
    # If form was submitted
    if request.method == "POST":
        newusername = request.form.get("newusername")
        password = request.form.get("password")

        user = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])

        # Validate user input
        if not newusername or not password:
            return apology("Blank input(s)", 400)

        if check_password_hash(user[0]["hash"], password) == False:
            return apology("Wrong Password", 400)

        if db.execute("SELECT user_id FROM users WHERE username = ?", newusername):
            return apology("Username already taken", 400)

        # Updates tasks table with new username
        db.execute("UPDATE tasks SET username = ? WHERE username = ?", newusername, user[0]["username"])

        # Updates users table with new username
        db.execute("UPDATE users SET username = ? WHERE user_id = ?", newusername, session["user_id"])

        # Logs user out
        session.clear()

        return redirect("/login")

    else:
        return redirect("/")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")
