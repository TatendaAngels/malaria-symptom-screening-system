"""Train, evaluate and save the malaria risk model.

Run from the project root:   python model/train_model.py
Options:                     --label smear|rdt|either   (default: smear)

Outputs (in model/): model.joblib, metrics.json and, in reports/, roc_curve.png and
feature_importance.png for the project report.
"""
import argparse
import json
import warnings
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from data_preprocessing import MODEL_FEATURES, load_dataset

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
REPORTS = HERE.parent / "reports"


def make_models():
    impute = lambda: SimpleImputer(strategy="median")
    return {
        "Baseline (always 'malaria')": DummyClassifier(strategy="prior"),
        "Logistic regression": make_pipeline(
            impute(), StandardScaler(),
            LogisticRegression(C=0.3, class_weight="balanced", max_iter=2000)),
        "Random forest": make_pipeline(
            impute(),
            RandomForestClassifier(300, min_samples_leaf=3,
                                   class_weight="balanced_subsample", random_state=0)),
        "Gradient boosting": HistGradientBoostingClassifier(
            max_depth=3, learning_rate=0.05, max_iter=150,
            l2_regularization=1.0, random_state=0),
    }


def compare_models(X, y):
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=1)
    rows = {}
    for name, model in make_models().items():
        auc, ap, brier = [], [], []
        for tr, te in cv.split(X, y):
            model.fit(X.iloc[tr], y.iloc[tr])
            p = model.predict_proba(X.iloc[te])[:, 1]
            auc.append(roc_auc_score(y.iloc[te], p))
            ap.append(average_precision_score(y.iloc[te], p))
            brier.append(brier_score_loss(y.iloc[te], p))
        rows[name] = {"roc_auc": np.mean(auc), "roc_auc_sd": np.std(auc),
                      "pr_auc": np.mean(ap), "brier": np.mean(brier)}
    return rows


def out_of_fold_scores(model, X, y, repeats=5):
    """Average the cross-validated score of every patient over several shuffles."""
    return np.mean([
        cross_val_predict(model, X, y, method="predict_proba",
                          cv=StratifiedKFold(5, shuffle=True, random_state=s))[:, 1]
        for s in range(repeats)], axis=0)


def operating_point(y, scores, threshold):
    flagged = scores >= threshold
    sens = flagged[y == 1].mean()
    spec = (~flagged)[y == 0].mean()
    return {"threshold": float(threshold), "sensitivity": float(sens), "specificity": float(spec)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="smear", choices=["smear", "rdt", "either"])
    args = ap.parse_args()

    X, y = load_dataset(args.label)
    print(f"Label '{args.label}': {len(y)} patients, {y.sum()} positive ({y.mean():.0%}), "
          f"{y.eq(0).sum()} negative\n")

    print("Cross-validation (5 folds x 10 repeats)")
    table = compare_models(X, y)
    for name, r in table.items():
        print(f"  {name:30s} ROC-AUC {r['roc_auc']:.2f} (+/-{r['roc_auc_sd']:.2f})  "
              f"PR-AUC {r['pr_auc']:.2f}  Brier {r['brier']:.2f}")

    model = make_models()["Random forest"]
    scores = out_of_fold_scores(model, X, y)

    fpr, tpr, thr = roc_curve(y, scores)
    t_low = thr[np.argmax(tpr >= 0.90)]            # catches >= 90% of malaria cases
    t_high = thr[np.argmax(fpr > 0.20) - 1]        # <= 20% of non-malaria flagged "higher"
    low, high = operating_point(y, scores, t_low), operating_point(y, scores, t_high)
    print(f"\nAt the 'moderate or higher' threshold: sensitivity {low['sensitivity']:.0%}, "
          f"specificity {low['specificity']:.0%}")
    print(f"At the 'higher' threshold:             sensitivity {high['sensitivity']:.0%}, "
          f"specificity {high['specificity']:.0%}")

    model.fit(X, y)
    joblib.dump({"model": model, "features": MODEL_FEATURES, "label": args.label,
                 "thresholds": {"moderate": float(t_low), "higher": float(t_high)},
                 "sklearn_version": sklearn.__version__}, HERE / "model.joblib")
    (HERE / "metrics.json").write_text(json.dumps(
        {"label": args.label, "n": int(len(y)), "positives": int(y.sum()),
         "model_comparison": {k: {a: float(b) for a, b in v.items()} for k, v in table.items()},
         "moderate_or_higher": low, "higher": high}, indent=2))

    REPORTS.mkdir(exist_ok=True)
    plt.figure(figsize=(5, 5))
    plt.plot(fpr, tpr, label=f"Random forest (AUC {roc_auc_score(y, scores):.2f})")
    plt.plot([0, 1], [0, 1], "--", color="grey", label="Chance")
    plt.xlabel("1 - specificity"); plt.ylabel("Sensitivity")
    plt.title("Cross-validated ROC curve"); plt.legend(); plt.tight_layout()
    plt.savefig(REPORTS / "roc_curve.png", dpi=150); plt.close()

    rf = model.named_steps["randomforestclassifier"]
    order = np.argsort(rf.feature_importances_)[-12:]
    plt.figure(figsize=(6, 4.5))
    plt.barh([MODEL_FEATURES[i] for i in order], rf.feature_importances_[order])
    plt.title("Most influential inputs"); plt.tight_layout()
    plt.savefig(REPORTS / "feature_importance.png", dpi=150); plt.close()
    print("\nSaved model/model.joblib, model/metrics.json, reports/*.png")


if __name__ == "__main__":
    main()