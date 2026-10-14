import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
db = SQLAlchemy(app)


@app.route("/")
def home():
    return "Digital Baggage Tracking System is running"


@app.route("/dbtest")
def dbtest():
    tables = db.session.execute(text("SHOW TABLES")).fetchall()
    return "Connected to MySQL. Tables: " + ", ".join(t[0] for t in tables)