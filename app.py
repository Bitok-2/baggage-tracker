import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
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


@app.route("/dbtest")
def dbtest():
    tables = db.session.execute(text("SHOW TABLES")).fetchall()
    return "Connected to MySQL. Tables: " + ", ".join(t[0] for t in tables)