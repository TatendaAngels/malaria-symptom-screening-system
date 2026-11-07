import os
import re
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))

# This ensures Python can find the 'model' folder from the 'webapp' folder
sys.path.append(str(Path(__file__).resolve().parent.parent))
from model.predict import predict_risk

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gumbochumatatenda1@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = 'gumbochumatatenda1@gmail.com'
mail = Mail(app)

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

    if not app.config["MAIL_PASSWORD"]:
        app.logger.error("Contact form email is unavailable because EMAIL_PASSWORD is not configured.")
        return jsonify({"status": "error", "message": "The contact form is temporarily unavailable. Please try again later."}), 503

    msg = Message(
        subject=f"New MalariaAI Contact Form Message from {name}",
        recipients=["gumbochumatatenda1@gmail.com"],
        reply_to=user_email,
        body=f"Name: {name}\nEmail: {user_email}\n\nMessage:\n{message_body}",
    )

    try:
        mail.send(msg)
    except Exception:
        app.logger.exception("Failed to send MalariaAI contact form email.")
        return jsonify({"status": "error", "message": "We could not send your message. Please try again later."}), 500

    return jsonify({"status": "success", "message": "Email sent successfully!"}), 200

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

if __name__ == "__main__":
    app.run(debug=False)