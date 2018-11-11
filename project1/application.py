import os
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import string
from . import booksapp

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# userdefined vars

authentificated = False
search_criterias = ["isbn", 'author', "title"]
user_id = " "
username = " "

@app.route("/")
def index():
    if session['authentificated']:
        return redirect(url_for('home'))
    return render_template("index.html")

@app.route('/login', methods = ["GET", "POST"])
def login():
    session['authentificated'] = False
    if request.method == "POST":
        login = request.form.get("login").lower()
        password = request.form.get("password")
        response = db.execute("SELECT * FROM users WHERE  username = :username AND password = :password",
        {"username":login, "password": password}).fetchone()
        if not response is None: 
            # make sure the login password combination exists
            session['authentificated'] = True
            session['user_id'] = response.userid
            session['username'] = response.username
            #db.execute("SELECT userid FROM users WHERE username = :username", {"username":login})
            return redirect(url_for("home", method = "GET"))
        else:
            return render_template("login.html", errormessage = "Incorrect credentials")
    return render_template("login.html")

@app.route('/home', methods = ["GET", "POST"])
def home():
    authentificated = session['authentificated']
    if (not authentificated):
        return redirect(url_for("index"))
    else:
        if request.method == "POST":
            search_for = request.form.get("search")
            search_crt = request.form.get("crt")
            search_results = db.execute(f"SELECT * FROM books WHERE {search_crt} LIKE :search_for LIMIT 50", {"search_for": '%'+search_for+'%'}).fetchall()
            if search_results is None or search_results == []:
                return render_template("home.html", criterias = search_criterias, errormessage = f"{search_for} under {search_crt} not found!")
            return render_template("home.html", criterias = search_criterias, search_results = search_results)
        return render_template("home.html", criterias = search_criterias)
   

@app.route('/register', methods = ["POST", "GET"])
def new_user():
    session['authentificate'] = False
    session['user_id']=""
    if request.method == "POST":
        allowed_chars = string.ascii_lowercase
        username = request.form.get("username")
        username = str(username).lower()
        password = request.form.get("password")
        password_repeat = request.form.get("password_repeat")
        errormessage = ""
        if password == password_repeat:
            if len(username)>2:
                for char in username:
                    if not char in allowed_chars:
                        errormessage = "Special symbols are not allowed in the username!"
                        break
                existst = db.execute("SELECT username FROM users WHERE username = :username", {"username" : username}).fetchone()
                if existst is None:
                    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", 
                    {"username": username, "password":password})
                    db.commit()
                    return redirect(url_for('login', method = "GET", errormessage = "Success! Please, login!"))
                else:
                    errormessage = "Username already exists"
            else:
                errormessage = "Username should be at least 3 character long"
        else:
            errormessage = "Passords do not match! "
        return render_template("register.html", errormessage = errormessage)
    else:
        return render_template("register.html", errormessage = "Choose your username and password")

@app.route('/logout')
def logout():
   session["authentificated"] = False
   session["user_id"] = ""
   session["username"] = ""
   return redirect(url_for("index"))


@app.route('/book/<string:bookid>', methods = ["POST", "GET"])
def book(bookid):
    book = db.execute("SELECT * FROM books WHERE isbn = :bookid", {"bookid":bookid}).fetchone()

    # average review score:
    goodreads_book_data = booksapp.get_book(bookid)
    

    reviews_sql = db.execute(f"SELECT by_username, review, score FROM reviews WHERE isbn = :bookid", {"bookid":bookid}).fetchall()
    
    reviews_count_here = len(reviews_sql)
    reviews_count=goodreads_book_data["work_ratings_count"]
    reviews_average = goodreads_book_data["average_rating"]
    reviews_average_here = db.execute("SELECT ROUND(AVG(score),2) FROM reviews WHERE isbn = :isbn", {'isbn':bookid}).fetchone()
    reviews_average_here = reviews_average_here[0]

    context = {'reviews_count':reviews_count, 'reviews_average':reviews_average, 'reviews_count_here':reviews_count_here, 'reviews_average_here':reviews_average_here}
    
    if reviews_sql is None:
        reviews = []
    else:
        reviews = reviews_sql
    # lookup database for reviews 
    if request.method == "POST":
        #check if user already submited a review
        prev_review = db.execute("SELECT * FROM reviews WHERE isbn = :bookid AND byuser = :userid", {"bookid":bookid, "userid":session["user_id"]}).fetchone()
        if prev_review is None:
            review_score = request.form.get("score")
            review_text = request.form.get("review")
            if not review_score is None:
                if not review_text is None:
                    db.execute("INSERT INTO reviews (isbn, review, byuser, score, by_username) VALUES (:isbn, :review, :byuser, :score, :username)", 
                    {"isbn":book.isbn, "review":review_text, "byuser":session["user_id"], "score":review_score, "username":session['username'] })
                    db.commit()
                    return render_template("bookpage.html", book = book, errormessage = "Thank you, your review is submited!", context = context) 
                else:
                    return render_template("bookpage.html", book = book, errormessage = "Look like you forgot to write your reveiw!", context = context)
            else:
                return render_template("bookpage.html", book = book, errormessage = "Please rate the book!", reviewtext = review_text, context = context)
        else:
            return render_template("bookpage.html", book = book, errormessage = f"Looks like you already reviewed the book!", reviewtext = prev_review.review, context = context)
    # fetch review score for the book from goodreads
    # do something with the style 
    return render_template("bookpage.html", book = book, reviewtext = "No review text", reviews = reviews, context = context)


@app.route('/api/<string:bookid>', methods = ["GET"])
def api_return_json(bookid):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":bookid}).fetchone()
    reviews = db.execute("SELECT ROUND(AVG(score),2), COUNT(score) FROM reviews WHERE isbn = :isbn",
    {'isbn': bookid}).fetchone()
    title = book.title
    author = book.author
    year = book.year
    average_score = float(reviews[0])
    review_count =  reviews[1]
    context = {
    "title": title,
    "author": author,
    "year": year,
    "isbn": bookid,
    "review_count": review_count,
    "average_score": average_score }
    return jsonify(context)