"""Turn a patient's answers into a risk band, the main reasons, and safety advice.

    from model.predict import predict_risk      (or: from predict import predict_risk)
    predict_risk({"age": 7, "sex": "female", "temp_c": 39.2, "fever_now": 1, ...})

Symptoms that are missing from `answers` count as "no". Only `age` is required.
The output is a screening aid: it never says a person does NOT have malaria.
"""
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"

DISCLAIMER = ("This is a screening aid, not a diagnosis. Only a blood test "
              "(rapid test or microscopy) can confirm malaria.")

# Danger signs override the model. These are commonly cited warning signs of severe
# malaria; confirm the final list against the Zimbabwe national malaria guidelines.
DANGER_SIGNS = {
    "convulsions": "fits or convulsions",
    "confusion": "confusion or reduced alertness",
    "resp_distress": "difficulty breathing",
    "bleeding": "unusual bleeding",
    "jaundice": "yellow eyes or skin",
    "dark_urine": "dark red or brown urine",
    "cannot_drink": "unable to drink or keep fluids down",
}

READABLE = {
    "fever_now": "fever", "fever_48h": "fever for over 48 hours",
    "fever_7d": "fever during the past 7 days", "weight_loss": "weight loss",
    "headache": "headache", "nausea": "nausea", "vomiting": "vomiting",
    "joint_pain": "joint pain", "muscle_pain": "muscle pain", "chest_pain": "chest pain",
    "back_pain": "back pain", "confusion": "confusion", "loss_appetite": "loss of appetite",
    "runny_nose": "runny nose", "drowsy": "drowsiness", "dizzy": "dizziness",
    "abdominal_pain": "stomach pain", "cough": "cough", "diarrhea": "diarrhoea",
    "chills": "chills or shivering", "low_urine": "passing little urine",
    "prostration": "extreme weakness", "convulsions": "convulsions",
    "resp_distress": "difficulty breathing", "recurrent_fever": "fever that keeps coming back",
}

ADVICE = {
    "urgent": "Go to the nearest clinic or hospital now. Do not wait.",
    "higher": "Malaria is quite possible. Get a malaria blood test today.",
    "moderate": "Malaria cannot be ruled out. Get a malaria blood test as soon as you can.",
    "lower": ("Your answers point to a lower likelihood, but this does not rule malaria out. "
              "If the fever continues or gets worse, get a malaria blood test."),
}


@lru_cache(maxsize=1)
def _bundle():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("model.joblib not found. Run: python model/train_model.py")
    return joblib.load(MODEL_PATH)


def _row(answers, features):
    sex = str(answers.get("sex", "")).lower()
    values = {"age": float(answers["age"]),
              "sex_male": {"male": 1, "female": 0}.get(sex, np.nan),
              "temp_c": answers.get("temp_c")}
    values["temp_c"] = np.nan if values["temp_c"] in (None, "") else float(values["temp_c"])
    for f in features:
        if f not in values:
            values[f] = 1 if answers.get(f) in (1, True, "1", "yes", "on") else 0
    return pd.DataFrame([values])[features]


def validate(answers):
    try:
        age = float(answers["age"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("Please enter a valid age.")
    if not 0 <= age <= 120:
        raise ValueError("Age must be between 0 and 120.")
    t = answers.get("temp_c")
    if t not in (None, "") and not 34 <= float(t) <= 43:
        raise ValueError("Temperature must be between 34 and 43 °C, or left blank.")


def predict_risk(answers):
    validate(answers)
    b = _bundle()
    model, features, thr = b["model"], b["features"], b["thresholds"]
    row = _row(answers, features)
    score = float(model.predict_proba(row)[0, 1])

    # Reasons: how much does the score drop if each reported symptom is switched off?
    reasons = []
    for f in features:
        if f in READABLE and row.at[0, f] == 1:
            off = row.copy(); off.at[0, f] = 0
            drop = score - float(model.predict_proba(off)[0, 1])
            if drop > 0.005:
                reasons.append((drop, READABLE[f]))
    reasons = [name for _, name in sorted(reasons, reverse=True)[:3]]

    danger = [text for key, text in DANGER_SIGNS.items()
              if answers.get(key) in (1, True, "1", "yes", "on")]
    if danger:
        level = "urgent"
    elif score >= thr["higher"]:
        level = "higher"
    elif score >= thr["moderate"]:
        level = "moderate"
    else:
        level = "lower"

    advice = ADVICE[level]
    if float(answers["age"]) < 5 and level != "urgent":
        advice += " Young children can become seriously ill quickly, so do not delay."
    return {"risk_level": level, "score": round(score, 2), "main_factors": reasons,
            "danger_signs": danger, "advice": advice, "disclaimer": DISCLAIMER}


if __name__ == "__main__":
    demo = {"age": 7, "sex": "female", "temp_c": 39.2, "fever_now": 1, "fever_48h": 1,
            "chills": 1, "headache": 1, "prostration": 1, "abdominal_pain": 1}
    print(predict_risk(demo))
    print(predict_risk({"age": 30, "sex": "male", "cough": 1, "runny_nose": 1}))
    print(predict_risk({"age": 4, "sex": "male", "fever_now": 1, "convulsions": 1}))