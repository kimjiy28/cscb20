from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt

app = Flask(__name__) # create the instance of class
bcrypt=Bcrypt(app)

app.config["SECRET_KEY"]="019ad4ff03fbc9cb0800448300f40206713f5b3a53c0d4243056b58db843944a"
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///assignment3.db" # creates the database

db = SQLAlchemy(app) # creates the instance

# Tables
class Person(db.Model):
    __tablename__="Person"
    username=db.Column(db.String(20), unique=True, primary_key=True, nullable=False)
    email=db.Column(db.String(30), unique=True, nullable=False)
    password=db.Column(db.String(20), nullable=False)
    role=db.Column(db.String(20), nullable=False) # distinguishes instructor and students

    feedback=db.relationship("Feedback", backref="recipient")
    grades=db.relationship("Grades", backref="owner")

    def __repr__(self):
        return f"Person('{self.username}', '{self.email}')"

class Feedback(db.Model):
    __tablename__="Feedback"
    id=db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    instructor=db.Column(db.Integer, db.ForeignKey(Person.username), nullable=False)
    Q1=db.Column(db.Text, nullable=False)
    Q2=db.Column(db.Text, nullable=False)
    Q3=db.Column(db.Text, nullable=False)
    Q4=db.Column(db.Text, nullable=False)
    date_posted=db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"Post('{self.instructor_id}', '{self.date_posted}')"

class Grades(db.Model):
    __tablename__="Grades"
    id=db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username=db.Column(db.Integer, db.ForeignKey(Person.username), nullable=False)
    assessment=db.Column(db.String(20), nullable=False)
    Grade=db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"Grade('{self.username}', '{self.assessment}', '{self.grade}')"

class Remark_Requests(db.Model):
    __tablename__="Remark_Requests"
    id=db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username=db.Column(db.String(20), nullable=False)
    assessment=db.Column(db.String(20), nullable=False)
    explanation=db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Request('{self.requestor}', '{self.assessment}')"

class Log(db.Model):
    __tablename__="Log"
    id=db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username=db.Column(db.String(20), db.ForeignKey(Person.username), nullable=False)
    date_posted=db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"Log('{self.username}', '{self.date_posted}')"

@app.route('/') # only homepage could be accessed without logging in.
@app.route('/home')
def home():
    return render_template('home.html', title="Home")

@app.route("/assignments")
def assignments():
    if "name" not in session:
        return render_template("no_access.html")
    return render_template("assignments.html")

@app.route("/courseteam")
def courseteam():
    if "name" not in session:
        return render_template("no_access.html")
    return render_template("courseteam.html")

@app.route("/labs")
def labs():
    if "name" not in session:
        return render_template("no_access.html")
    return render_template("labs.html")

@app.route("/lectures")
def lectures():
    if "name" not in session:
        return render_template("no_access.html")
    return render_template("lectures.html")

@app.route("/tests")
def tests():
    if "name" not in session:
        return render_template("no_access.html")

    return render_template("tests.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method=="GET":
        return render_template("register.html", title="Registration")
    else:
        role = request.form["role"]
        username = request.form["username"]
        email = request.form["email"]
        hashed_password = bcrypt.generate_password_hash(request.form["password"]).decode('utf-8')
        details = [username, email, hashed_password, role]
        add_user(details)
        flash("Registration successful! Please login:")
        return redirect(url_for("login"))

@app.route('/login', methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        if "name" in session:
            return render_template("success.html", title="LogIn", text="You are logged in as", user=session["name"])
        else:
            return render_template("login.html", title="LogIn")
    else:
        username = request.form["username"]
        password = request.form["password"]
        person = Person.query.filter_by(username=username).first()
        if not person or not bcrypt.check_password_hash(person.password, password):
            flash("Please check your login details and try again.", "ERROR")
            return render_template("login.html")
        else:
            log_details = (username, password)
            session["name"] = username
            session.permanent = True
            return render_template("success.html", title="LogIn", text="You are logged in as", user=username)

@app.route('/logout')
def logout():
    session.pop("name", default = None)
    return redirect(url_for("login"))

@app.route('/remarkrequest', methods=["GET", "POST"])
def remarkrequest():
    if "name" not in session:
        return render_template("no_access.html")

    user = session["name"]

    instructors = []
    for person in db.session.query(Person).filter(Person.role=="instructor").all():
        instructors.append(person.username)

    if user in instructors:
        return redirect(url_for("remark_instructors"))

    if request.method=="GET":
        return render_template("remark_students.html", title="Remark Request")
    else:
        assessment = request.form["assessment"]
        explanation = request.form["explanation"]
        details = (user, assessment, explanation)
        add_request(details)
        return render_template("success.html", text="Remark request submitted")

@app.route('/remark_instructors')
def remark_instructors():
    user = session["name"]

    instructors = []
    for person in db.session.query(Person).filter(Person.role=="instructor").all():
        instructors.append(person.username)

    request= db.session.query(Remark_Requests).all()
    if user not in instructors:
        return render_template("no_access.html")
    return render_template("remark_instructors.html", title="Remark Request", user=user, requests=request)

@app.route('/feedback', methods = ["GET", "POST"])
def feedback():
    if "name" not in session:
        return render_template("no_access.html")

    user = session["name"]
    instructors = []
    for person in db.session.query(Person).filter(Person.role=="instructor").all():
        instructors.append(person.username)
    feedback = db.session.query(Feedback).filter(Feedback.instructor==user).all()

    if request.method == 'GET':
        return render_template("feedback.html",
                               title="Feedback", user=user, instructors=instructors, feedback=feedback)
    else:
        feedback = (request.form["instructor"],
                    request.form["Q1"],
                    request.form["Q2"],
                    request.form["Q3"],
                    request.form["Q4"])
        add_feedback(feedback)
        return render_template("success.html", title="Feedback", text="Thank you for submitting the feedback")

@app.route('/grades', methods=["GET", "POST"])
def grades():
    if "name" not in session:
        return render_template("no_access.html")

    user = session["name"]
    instructors=[]
    for person in db.session.query(Person).filter(Person.role=="instructor").all():
        instructors.append(person.username)
    grades = db.session.query(Grades).filter(Grades.username==user)
    if request.method=="GET":
        if user in instructors:
            return redirect(url_for("grades_instructors"))
        else:
            return render_template("grades_students.html", title="grades", grades=grades)

@app.route('/grades_instructors', methods=["GET", "POST"])
def grades_instructors():
    instructors=[]
    students=[]
    for person in db.session.query(Person).all():
        if person.role=="instructor":
            instructors.append(person.username)
        else:
            students.append(person.username)

    user = session["name"]
    if user not in instructors:
        return render_template("no_access.html")

    if request.method=="GET":
        return render_template("grades_instructors.html", user=user, students=students)
    else:
        grade = (request.form["username"],
                  request.form["assessment"],
                  request.form["grade"])
        add_grade(grade)
        return render_template("success.html", title="Grades", text="Grade updated")

@app.route('/grades_all')
def grades_all():
    instructors=[]
    for person in db.session.query(Person).filter(Person.role=="instructor").all():
        instructors.append(person.username)
    students = db.session.query(Grades).all()

    user = session["name"]
    if user not in instructors:
        return render_template("no_access.html")

    return render_template("grades_all.html", title="Grades", user=user, students=students)



def add_user(details):
    user = Person(username = details[0],
                  email = details[1],
                  password = details[2],
                  role = details[3])
    db.session.add(user)
    db.session.commit()

def add_request(details):
    request = Remark_Requests(username=details[0],
                              assessment=details[1],
                              explanation=details[2])
    db.session.add(request)
    db.session.commit()

def add_feedback(details):
    feedback = Feedback(instructor=details[0],
                       Q1 = details[1],
                       Q2 = details[2],
                       Q3 = details[3],
                       Q4 = details[4])
    db.session.add(feedback)
    db.session.commit()

def add_grade(details):
    grade = Grades(username=details[0],
                   assessment=details[1],
                   Grade=details[2])
    db.session.add(grade)
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)