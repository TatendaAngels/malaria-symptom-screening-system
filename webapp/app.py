import os
import re
import sys
import requests
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).resolve().with_name(".env"))

# Ensure Python can find the 'model' folder
sys.path.append(str(Path(__file__).resolve().parent.parent))
from model.predict import predict_risk

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# --- DATABASE SETUP ---
# Using SQLite (a simple file-based database) inside the webapp folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(Path(__file__).resolve().parent / 'iot_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class IoTReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    device_id = db.Column(db.String(50), default="ESP32-Node-1")
    temperature = db.Column(db.Float, nullable=False)
    heart_rate = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    advice = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "device_id": self.device_id,
            "temperature": self.temperature,
            "heart_rate": self.heart_rate,
            "risk_level": self.risk_level,
            "advice": self.advice
        }

# Create the database file if it doesn't exist
with app.app_context():
    db.create_all()

# --- PAGE ROUTES ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/how-it-works")
def how_it_works():
    return render_template("how.html")

@app.route("/screening")
def screening():
    return render_template("screening.html")

@app.route("/iot-dashboard")
def iot_dashboard():
    return render_template("iot_dashboard.html")

# --- CONTACT ROUTE (Existing) ---
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return render_template("contact.html")

    name = request.form.get("name", "").strip()
    user_email = request.form.get("email", "").strip()
    message_body = request.form.get("message", "").strip()

    if (not name or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", user_email) or not message_body):
        return jsonify({"status": "error", "message": "Please provide a valid name, email, and message."}), 400

    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    if not RESEND_API_KEY:
        return jsonify({"status": "error", "message": "The contact form is temporarily unavailable."}), 503

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": "onboarding@resend.dev",
                "to": ["gumbochumatatenda1@gmail.com"],
                "subject": f"New MalariaAI Message from {name}",
                "text": f"Name: {name}\nEmail: {user_email}\n\nMessage:\n{message_body}"
            },
            timeout=10
        )
        if response.status_code not in (200, 201):
            return jsonify({"status": "error", "message": "We could not send your message."}), 500

        return jsonify({"status": "success", "message": "Email sent successfully!"}), 200
    except Exception:
        return jsonify({"status": "error", "message": "Server connection error."}), 500

# --- SYMPTOM PREDICTION API (Existing) ---
@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        data = request.get_json()
        result = predict_risk(data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "An internal server error occurred."}), 500

# --- IOT API: RECEIVE DATA (Updated to save to DB) ---
@app.route("/api/iot-readings", methods=["POST"])
def iot_readings():
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"status": "error", "message": "A JSON object is required."}), 400

        temp = data.get("temperature")
        heart_rate = data.get("heart_rate")

        if temp is None or heart_rate is None:
            return jsonify({"status": "error", "message": "Missing temperature or heart_rate."}), 400

        # Check for implausible readings
        if not (34.0 <= temp <= 43.0):
            return jsonify({"status": "error", "message": "Temperature out of human bounds."}), 400

        # Map to AI input
        iot_patient = {
            "age": 30,
            "sex": "male",
            "temp_c": temp,
            "fever_now": 1 if float(temp) > 37.5 else 0
        }

        risk_result = predict_risk(iot_patient)

        # Save to Database
        new_reading = IoTReading(
            device_id=data.get("device_id", "ESP32-Node-1"),
            temperature=float(temp),
            heart_rate=float(heart_rate),
            risk_level=risk_result['risk_level'],
            advice=risk_result['advice']
        )
        db.session.add(new_reading)
        db.session.commit()

        print(f"💾 Saved to DB -> Temp: {temp}°C, HR: {heart_rate} bpm | Risk: {risk_result['risk_level']}")

        return jsonify({
            "status": "success",
            "message": "Data received and saved",
            "ai_risk_level": risk_result["risk_level"],
            "ai_advice": risk_result["advice"],
        }), 200

    except Exception as e:
        app.logger.error(f"IoT Error: {str(e)}")
        return jsonify({"status": "error", "message": "Server error"}), 500

# --- IOT API: RETRIEVE DATA ---
@app.route("/api/iot-latest", methods=["GET"])
def get_latest_iot():
    latest = IoTReading.query.order_by(IoTReading.timestamp.desc()).first()
    if not latest:
        return jsonify({"status": "no_data"}), 200
    return jsonify(latest.to_dict()), 200

@app.route("/api/iot-history", methods=["GET"])
def get_iot_history():
    # Get the last 20 readings for the graphs
    readings = IoTReading.query.order_by(IoTReading.timestamp.desc()).limit(20).all()
    # Reverse so the graph draws left-to-right
    history = [r.to_dict() for r in reversed(readings)]
    return jsonify(history), 200

if __name__ == "__main__":
    app.run(debug=False)