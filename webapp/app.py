
import os
import re
import sys
import math
import requests

from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).resolve().with_name(".env"))

# Ensure Python can find the model folder
sys.path.append(str(Path(__file__).resolve().parent.parent))
from model.predict import predict_risk

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# DATABASE SETUP
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + str(Path(__file__).resolve().parent / "iot_data.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# DATABASE MODEL
class IoTReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
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


# Create database tables
with app.app_context():
    db.create_all()


# WEBSITE ROUTES

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


# CONTACT ROUTE

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return render_template("contact.html")

    name = request.form.get("name", "").strip()
    user_email = request.form.get("email", "").strip()
    message_body = request.form.get("message", "").strip()

    if (
        not name
        or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", user_email)
        or not message_body
    ):
        return jsonify({
            "status": "error",
            "message": "Please provide a valid name, email, and message."
        }), 400

    resend_api_key = os.environ.get("RESEND_API_KEY", "")

    if not resend_api_key:
        return jsonify({
            "status": "error",
            "message": "The contact form is temporarily unavailable."
        }), 503

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "onboarding@resend.dev",
                "to": ["gumbochumatatenda1@gmail.com"],
                "subject": f"New MalariaAI Message from {name}",
                "text": (
                    f"Name: {name}\n"
                    f"Email: {user_email}\n\n"
                    f"Message:\n{message_body}"
                )
            },
            timeout=10
        )

        if response.status_code not in (200, 201):
            return jsonify({
                "status": "error",
                "message": "We could not send your message."
            }), 500

        return jsonify({
            "status": "success",
            "message": "Email sent successfully!"
        }), 200

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Server connection error."
        }), 500


# SYMPTOM PREDICTION API

@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        data = request.get_json()

        if not isinstance(data, dict):
            return jsonify({
                "error": "A JSON object is required."
            }), 400

        result = predict_risk(data)
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception:
        app.logger.exception("Symptom prediction error")

        return jsonify({
            "error": "An internal server error occurred."
        }), 500


# IOT API: RECEIVE AND SAVE SENSOR DATA

@app.route("/api/iot-readings", methods=["POST"])
def iot_readings():
    try:
        data = request.get_json()

        if not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "message": "A JSON object is required."
            }), 400

        temp = data.get("temperature")
        heart_rate = data.get("heart_rate")

        if temp is None or heart_rate is None:
            return jsonify({
                "status": "error",
                "message": "Missing temperature or heart_rate."
            }), 400

        # Convert readings to numbers
        try:
            temp = float(temp)
            heart_rate = float(heart_rate)

        except (TypeError, ValueError):
            return jsonify({
                "status": "error",
                "message": "Temperature and heart rate must be numeric."
            }), 400

        # Reject invalid temperature sensor values
        if not math.isfinite(temp) or not -55 <= temp <= 125:
            return jsonify({
                "status": "error",
                "message": "Invalid DS18B20 temperature reading."
            }), 400

        # Reject invalid heart-rate values
        if not math.isfinite(heart_rate) or not 20 <= heart_rate <= 250:
            return jsonify({
                "status": "error",
                "message": "Invalid heart-rate reading."
            }), 400

        # IoT measurements alone cannot determine malaria risk.
        # Surface temperature is not treated as core body temperature.
        risk_level = "not_assessed"

        advice = (
            "Sensor readings received successfully. "
            "These readings alone cannot diagnose malaria. "
            "Complete the symptom screening and obtain a malaria "
            "blood test when clinically indicated."
        )

        # Save the original sensor readings
        new_reading = IoTReading(
            device_id=data.get("device_id", "ESP32-Node-1"),
            temperature=temp,
            heart_rate=heart_rate,
            risk_level=risk_level,
            advice=advice
        )

        db.session.add(new_reading)
        db.session.commit()

        print(
            f"Saved IoT data -> Temperature: {temp}°C, "
            f"Heart rate: {heart_rate} BPM"
        )

        return jsonify({
            "status": "success",
            "message": "Data received and saved successfully.",
            "temperature": temp,
            "heart_rate": heart_rate,
            "risk_level": risk_level,
            "advice": advice
        }), 200

    except Exception:
        db.session.rollback()
        app.logger.exception("IoT reading error")

        return jsonify({
            "status": "error",
            "message": "Server error"
        }), 500


# IOT API: RETRIEVE LATEST READING

@app.route("/api/iot-latest", methods=["GET"])
def get_latest_iot():
    latest = IoTReading.query.order_by(
        IoTReading.timestamp.desc()
    ).first()

    if not latest:
        return jsonify({"status": "no_data"}), 200

    return jsonify(latest.to_dict()), 200


# IOT API: RETRIEVE READING HISTORY

@app.route("/api/iot-history", methods=["GET"])
def get_iot_history():
    readings = IoTReading.query.order_by(
        IoTReading.timestamp.desc()
    ).limit(20).all()

    history = [reading.to_dict() for reading in reversed(readings)]

    return jsonify(history), 200


# RUN FLASK SERVER

if __name__ == "__main__":
    app.run(debug=False)
