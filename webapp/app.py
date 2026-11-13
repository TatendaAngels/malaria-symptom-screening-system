import os
import re
import sys
import requests
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))

# This ensures Python can find the 'model' folder from the 'webapp' folder
sys.path.append(str(Path(__file__).resolve().parent.parent))
from model.predict import predict_risk

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# --- Page Routes ---

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

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return render_template("contact.html")

    name = request.form.get("name", "").strip()
    user_email = request.form.get("email", "").strip()
    message_body = request.form.get("message", "").strip()

    if (
        not name
        or len(name) > 120
        or "\r" in name
        or "\n" in name
        or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", user_email)
        or len(user_email) > 254
        or not message_body
        or len(message_body) > 5000
    ):
        return jsonify({"status": "error", "message": "Please provide a valid name, email, and message."}), 400

    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    if not RESEND_API_KEY:
        app.logger.error("Contact form email unavailable: RESEND_API_KEY not configured.")
        return jsonify({"status": "error", "message": "The contact form is temporarily unavailable."}), 503

    # Send email via Resend API (HTTPS, works on Render)
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "onboarding@resend.dev",
                "to": ["gumbochumatatenda1@gmail.com"],
                "subject": f"New MalariaAI Message from {name}",
                "text": f"Name: {name}\nEmail: {user_email}\n\nMessage:\n{message_body}"
            },
            timeout=10 # Good practice to prevent hanging
        )

        if response.status_code not in (200, 201):
            app.logger.error(f"Resend API error: {response.text}")
            return jsonify({"status": "error", "message": "We could not send your message."}), 500

        return jsonify({"status": "success", "message": "Email sent successfully!"}), 200

    except Exception as e:
        app.logger.error(f"Connection error: {e}")
        return jsonify({"status": "error", "message": "Server connection error."}), 500

# --- API Route ---

@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        # Get the JSON data sent from the frontend
        data = request.get_json()
        
        # Pass the data directly to our AI model's predict function
        result = predict_risk(data)
        
        # Return the result as JSON
        return jsonify(result), 200
        
    except ValueError as e:
        # Catch validation errors (like bad age or temperature)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # Catch any other unexpected errors
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route("/api/iot-readings", methods=["POST"])
def iot_readings():
    try:
        data = request.get_json()

        temp = data.get("temperature")
        heart_rate = data.get("heart_rate", 0)

        if temp is None:
            return jsonify({"status": "error", "message": "No temperature provided"}), 400

        iot_patient = {
            "age": 30,
            "sex": "male",
            "temp_c": temp,
            "fever_now": 1 if float(temp) > 37.5 else 0,
        }

        risk_result = predict_risk(iot_patient)
        print(f"IoT Data -> Temp: {temp}°C, HR: {heart_rate} bpm | AI Risk: {risk_result['risk_level']}")

        return jsonify({
            "status": "success",
            "message": "Data received",
            "ai_risk_level": risk_result["risk_level"],
            "ai_advice": risk_result["advice"],
        }), 200

    except Exception as e:
        app.logger.error(f"IoT Error: {str(e)}")
        return jsonify({"status": "error", "message": "Server error"}), 500

if __name__ == "__main__":
    app.run(debug=False)