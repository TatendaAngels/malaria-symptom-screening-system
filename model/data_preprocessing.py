"""Load and clean the Burkina Faso fever dataset (Mendeley Data, cf49v47z4c, CC BY 4.0).

The CSV uses ';' as separator and long bilingual headers, so columns are picked by
position and double-checked against a keyword from the header. Only information a
patient (or health worker with a thermometer) can supply is used as a model input:
no blood tests, no exam findings, no other-disease diagnoses (those would leak the answer).
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "data.csv"

# feature name -> (column position in data.csv, keyword that must appear in that header)
YES_NO_COLUMNS = {
    "fever_now": (5, "temp"),
    "fever_48h": (6, "48"),
    "fever_7d": (7, "7 days"),
    "weight_loss": (9, "weight"),
    "headache": (10, "headache"),
    "nausea": (11, "nausea"),
    "vomiting": (12, "vomiting"),
    "joint_pain": (13, "joint pain"),
    "muscle_pain": (15, "muscle pain"),
    "chest_pain": (16, "chaist"),
    "back_pain": (17, "back pain"),
    "confusion": (18, "consciousness"),
    "loss_appetite": (19, "appetite"),
    "runny_nose": (23, "rhinorrhea"),
    "drowsy": (24, "drowsiness"),
    "dizzy": (25, "dizzy"),
    "abdominal_pain": (27, "stomac"),
    "cough": (30, "cough"),
    "diarrhea": (31, "diarrhea"),
    "chills": (34, "shiver"),
    "low_urine": (37, "oliguria"),
    "prostration": (39, "prostration"),
    "convulsions": (42, "convulsion"),
    "resp_distress": (54, "respiratory"),
}

# Model inputs, in the order the form/API must supply them.
MODEL_FEATURES = (
    ["age", "sex_male", "temp_c", "recurrent_fever"] + list(YES_NO_COLUMNS)
)

LABEL_COLUMNS = {"smear": (69, "goutte"), "rdt": (68, "tdr")}


def _check(df, pos, keyword):
    header = str(df.columns[pos]).lower()
    if keyword.lower() not in header:
        raise ValueError(
            f"Column {pos} is '{df.columns[pos]}', expected it to contain '{keyword}'. "
            "Is this the original data.csv from Mendeley?"
        )
    return df.iloc[:, pos]


def clean_temperature(raw):
    """Fix typing errors such as '36,4', '390', '3904', 'T3501', '19.76'."""
    t = raw.astype(str).str.replace(",", ".", regex=False).str.replace("T", "", regex=False)
    t = pd.to_numeric(t, errors="coerce")
    t = t.where(t < 100, t / 10)          # 390 -> 39.0, 3904 -> 390.4
    t = t.where(t < 100, t / 10)          # 390.4 -> 39.04
    return t.where(t.between(34, 43))     # anything still implausible becomes missing


def load_raw(path=DATA_PATH):
    return pd.read_csv(path, sep=";", encoding="utf-8-sig")


def build_features(df):
    X = pd.DataFrame(index=df.index)
    age = _check(df, 2, "age")
    X["age"] = pd.to_numeric(age.astype(str).str.replace(",", ".", regex=False), errors="coerce")
    X["sex_male"] = _check(df, 1, "gender").map({"Homme": 1, "Femme": 0})
    X["temp_c"] = clean_temperature(_check(df, 63, "axillary"))
    X["recurrent_fever"] = _check(df, 8, "type of fever").str.strip().map(
        {"Récurrente": 1, "Intermittente": 0}
    )
    for name, (pos, kw) in YES_NO_COLUMNS.items():
        X[name] = _check(df, pos, kw).map({"OUI": 1, "NON": 0})
    return X[MODEL_FEATURES]


def build_label(df, kind="smear"):
    """1 = malaria confirmed, 0 = test negative, NaN = not tested (row is dropped).

    smear  : thick blood smear (microscopy, the reference test)  <- default
    rdt    : rapid diagnostic test
    either : positive on either test; negative only if no test was positive
    """
    def one(pos_kw):
        col = _check(df, *pos_kw).astype(str).str.strip()
        return col.map({"Positif": 1, "Négatif": 0})

    if kind in LABEL_COLUMNS:
        return one(LABEL_COLUMNS[kind])
    if kind == "either":
        s, r = one(LABEL_COLUMNS["smear"]), one(LABEL_COLUMNS["rdt"])
        y = pd.Series(np.nan, index=df.index)
        y[(s == 0) | (r == 0)] = 0
        y[(s == 1) | (r == 1)] = 1
        return y
    raise ValueError("label must be 'smear', 'rdt' or 'either'")


def load_dataset(kind="smear", path=DATA_PATH):
    df = load_raw(path)
    X, y = build_features(df), build_label(df, kind)
    keep = y.notna() & X["age"].notna()
    return X[keep].reset_index(drop=True), y[keep].astype(int).reset_index(drop=True)


if __name__ == "__main__":
    X, y = load_dataset()
    print(f"{len(X)} patients, {y.sum()} malaria-positive ({y.mean():.0%}), {X.shape[1]} features")
    print(X.isna().mean().round(2)[lambda s: s > 0])