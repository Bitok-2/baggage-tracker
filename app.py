import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session,flash
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")


class Baggage(db.Model):
    __tablename__ = "baggage"
    baggage_id = db.Column(db.Integer, primary_key=True)
    reference_no = db.Column(db.String(30), unique=True, nullable=False)
    rfid_tag_id = db.Column(db.String(64), unique=True, nullable=False)
    passenger_name = db.Column(db.String(100), nullable=False)
    flight_no = db.Column(db.String(20), nullable=False)
    current_status = db.Column(db.String(20), nullable=False, default="Checked in")


class ScanEvent(db.Model):
    __tablename__ = "scan_event"
    scan_id = db.Column(db.Integer, primary_key=True)
    baggage_id = db.Column(db.Integer, db.ForeignKey("baggage.baggage_id"), nullable=False)
    checkpoint = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)


class AuditLog(db.Model):
    __tablename__ ="audit_log"
    audit_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    action = db.Column(db.String(40), nullable=False)
    record_id = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)        


@app.route("/")
def home():
    return "Digital Baggage Tracking System is running"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.user_id
            session["name"] = user.name
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.")
    return render_template("login.html")    


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", name=session["name"])


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))
     


@app.route("/dbtest")
def dbtest():
    tables = db.session.execute(text("SHOW TABLES")).fetchall()
    return "Connected to MySQL. Tables: " + ", ".join(t[0] for t in tables)