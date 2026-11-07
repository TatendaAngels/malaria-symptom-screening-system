# MalariaAI: Symptom-Based Malaria Screening

MalariaAI is a web-based screening tool designed to assess the risk of malaria based on patient-reported symptoms. It uses a Machine Learning model trained on real clinical data from Burkina Faso to provide triage advice and encourage prompt testing.

**Important Disclaimer:** This tool is a screening aid, **not a diagnostic tool**. It does not replace a blood test (RDT or microscopy). If a patient has severe symptoms or danger signs, they should seek immediate medical attention regardless of the model's output.

## Team
*CS 414: Artificial Intelligence and Intelligent Systems - Group Project*
- **Tatenda** (Backend / ML)
- **Wilford** (Backend / ML)
- **Modester** (Frontend)
- **trae-code** (Frontend)

## The Model
- **Algorithm:** Random Forest Classifier (selected after comparing against Logistic Regression and Gradient Boosting).
- **Dataset:** [Mendeley Data - Tabular dataset for AI-based vector-borne disease prediction](https://data.mendeley.com/datasets/cf49v47z4c/1) (CC BY 4.0). 299 patients from Burkina Faso, 268 usable (212 malaria-positive, 56 negative).
- **Features:** 28 inputs strictly limited to what a patient can answer (age, sex, temperature, duration of fever, and 24 yes/no symptoms). Lab values and clinical exam findings were excluded to prevent data leakage.
- **Performance:** 
  - Cross-validated ROC-AUC: **0.65** (5 folds × 10 repeats).
  - At the "Moderate or Higher" threshold: Sensitivity **90%**, Specificity **16%**.
  - At the "Higher" threshold: Sensitivity **36%**, Specificity **80%**.

## How to Run Locally (For Teammates)

**Prerequisites:** Python 3.13+ and Git installed.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/TatendaAngels/malaria-symptom-screening-system.git
   cd malaria-symptom-screening-system
