import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session,flash,abort
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy import or_

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



STATUS_FLOW = ["Checked in", "Screened", "Loaded", "Arrived", "Collected"]
CHECKPOINT_STATUS = {
    "Check-in": "Checked in",
    "Security": "Screened",
    "Loading": "Loaded",
    "Arrival": "Arrived",
    "Collection": "Collected",
}

def next_checkpoint(status):
    position = STATUS_FLOW.index(status)
    if position + 1 >= len(STATUS_FLOW):
        return None
    next_status = STATUS_FLOW[position + 1]
    for checkpoint, s in CHECKPOINT_STATUS.items():
        if s == next_status:
            return checkpoint

def next_hint(status):
    checkpoint = next_checkpoint(status)
    if checkpoint is None:
        return "The journey is complete" 
    return "Next expected checkpoint: " + checkpoint + "."     


def audit(action, record_id=None):
    db.session.add(AuditLog(user_id=session.get("user_id"), action=action, record_id=record_id))
    db.session.commit()


@app.route("/")
def home():
   if "user_id" in session:
       return redirect(url_for("dashboard"))
   return redirect(url_for("login"))


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
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    flagged_actions = ["SCAN_FLAGGED", "UNKNOWN_TAG_SCAN"]

    q = request.args.get("q", "").strip()
    results = []
    if q:
        pattern = "%" + q + "%"
        results = (
            Baggage.query.filter(
                or_(
                    Baggage.reference_no.ilike(pattern),
                    Baggage.rfid_tag_id.ilike(pattern),
                    Baggage.passenger_name.ilike(pattern),
                )
            )
            .order_by(Baggage.baggage_id.desc())
            .limit(20)
            .all()
        )

    total_bags = Baggage.query.count()
    collected = Baggage.query.filter_by(current_status="Collected").count()
    scans_today = ScanEvent.query.filter(ScanEvent.timestamp >= today).count()
    flagged_today = AuditLog.query.filter(AuditLog.action.in_(flagged_actions), AuditLog.timestamp >= today).count()
    recent = (
        db.session.query(ScanEvent, Baggage)
        .join(Baggage, ScanEvent.baggage_id == Baggage.baggage_id)
        .order_by(ScanEvent.timestamp.desc(), ScanEvent.scan_id.desc())
        .limit(8)
        .all()
    )

    flagged_events = (
        AuditLog.query.filter(AuditLog.action.in_(flagged_actions))
        .order_by(AuditLog.timestamp.desc())
        .limit(5)
        .all()
    )

    chart_labels = list(CHECKPOINT_STATUS)
    chart_values = [ScanEvent.query.filter_by(checkpoint=checkpoint).count() for checkpoint in chart_labels]
    return render_template(
        "dashboard.html",
        name=session["name"],
        total_bags=total_bags,
        collected=collected,
        scans_today=scans_today,
        flagged_today=flagged_today,
        recent=recent,
        flagged_events=flagged_events,
        chart_labels=chart_labels,
        chart_values=chart_values,
        q=q,
        results=results,
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        reference_no = request.form.get("reference_no", "").strip()
        passenger_name = request.form.get("passenger_name", "").strip()
        flight_no = request.form.get("flight_no", "").strip()
        rfid_tag_id = request.form.get("rfid_tag_id", "").strip()

        if not all([reference_no, passenger_name, flight_no, rfid_tag_id]):
            flash("All fields are required.")
        elif Baggage.query.filter_by(reference_no=reference_no).first():
            flash("That baggage reference number already exists.")
        elif Baggage.query.filter_by(rfid_tag_id=rfid_tag_id).first():
            flash("That RFID tag is already assigned to another bag.")
        else:
            bag = Baggage(reference_no=reference_no, passenger_name=passenger_name, flight_no=flight_no, rfid_tag_id=rfid_tag_id)
            db.session.add(bag)
            db.session.commit()
            flash("Baggage" + reference_no + "registered.")
            return redirect(url_for("register"))            
    return render_template("register.html")

@app.route("/scan")
def scan():
    if "user_id" not in session:
        return redirect(url_for("login"))
    stations = [{"name": c, "slug": c.lower(), "status": s} for c, s in CHECKPOINT_STATUS.items()]
    return render_template("scan.html", stations=stations)

def handle_scan(tag_id, checkpoint):
        bag = Baggage.query.filter_by(rfid_tag_id=tag_id).first()
        if bag is None:
            audit("UNKNOWN_TAG_SCAN", tag_id)
            return "flagged", "FLAGGED: unknown or unregistered tag " + tag_id, None
        new_status = CHECKPOINT_STATUS[checkpoint]
        current = STATUS_FLOW.index(bag.current_status)
        new = STATUS_FLOW.index(new_status)

        if new == current:
            audit("SCAN_FLAGGED", bag.reference_no)
            return "flagged", ("FLAGGED: duplicate scan, bag " + bag.reference_no + " is already '" + bag.current_status + "'. " + next_hint(bag.current_status)), bag

        if new < current:
            audit("SCAN_FLAGGED", bag.reference_no)
            return "flagged", ("FLAGGED: out of sequence, bag " + bag.reference_no + " is already '" + bag.current_status + "'. " + next_hint(bag.current_status)), bag

        if new > current + 1:
            audit("SCAN_FLAGGED", bag.reference_no)
            missed = next_checkpoint(bag.current_status)
            return "skipped", ("FLAGGED: bag " + bag.reference_no + " skipped a stage, expected " + missed + " station. Scan it there first."), bag  

        db.session.add(ScanEvent(baggage_id=bag.baggage_id, checkpoint=checkpoint, status=new_status))
        bag.current_status = new_status
        db.session.commit()
        audit("SCAN_SUCCESS", bag.reference_no)
        return "accepted", ("Accepted: bag " + bag.reference_no + " (" + bag.passenger_name + ") is now '" + new_status + "'. " + next_hint(new_status)), bag
          

@app.route("/scan/<station>", methods=["GET", "POST"])
def scan_station(station):
    if "user_id" not in session:
        return redirect(url_for("login"))

    checkpoint = next((c for c in CHECKPOINT_STATUS if c.lower() == station.lower()), None)
    if checkpoint is None:
        abort(404)
    if request.method == "POST":
        session["follow"] = bool(request.form.get("follow"))
        tag_id = request.form.get("tag_id", "").strip()
        if not tag_id:
            flash("Enter a tag ID")
        else:
            outcome, message, bag = handle_scan(tag_id, checkpoint)
            flash(message)
            if outcome == "skipped":
                missed = next_checkpoint(bag.current_status)
                return redirect(url_for("scan_station", station=missed.lower(), tag=tag_id))
            if outcome == "accepted" and session.get("follow"):
                upcoming = next_checkpoint(bag.current_status)
                if upcoming:
    
                  return redirect(url_for("scan_station", station=upcoming.lower()))
        return redirect(url_for("scan_station", station=station))
    return render_template("station.html", checkpoint=checkpoint, tag=request.args.get("tag", ""), follow=session.get("follow", False))
