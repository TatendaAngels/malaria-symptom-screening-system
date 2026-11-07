from flask import Flask, render_template, request, jsonify
import sys
from pathlib import Path

# This ensures Python can find the 'model' folder from the 'webapp' folder
sys.path.append(str(Path(__file__).resolve().parent.parent))
from model.predict import predict_risk

app = Flask(__name__)

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

@app.route("/contact")
def contact():
    return render_template("contact.html")

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
    # Run the app (debug=True is great for development)
    app.run(debug=True)