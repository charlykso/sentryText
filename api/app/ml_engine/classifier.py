import os
import joblib
from app.ml_engine.preprocessor import clean_text

# Paths to serialized models
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models'))
vectorizer_path = os.path.join(MODELS_DIR, 'tfidf_vectorizer.joblib')
lr_path = os.path.join(MODELS_DIR, 'lr_model.joblib')
svm_path = os.path.join(MODELS_DIR, 'svm_model.joblib')

vectorizer = None
lr_model = None
svm_model = None
models_loaded = False

def load_models():
    """
    Dynamically loads the serialized models from disk.
    Returns True if loading is successful, False otherwise.
    """
    global vectorizer, lr_model, svm_model, models_loaded
    if models_loaded:
        return True
    try:
        if os.path.exists(vectorizer_path) and os.path.exists(lr_path) and os.path.exists(svm_path):
            vectorizer = joblib.load(vectorizer_path)
            lr_model = joblib.load(lr_path)
            svm_model = joblib.load(svm_path)
            models_loaded = True
            print("SentryText ML models loaded successfully.")
            return True
        else:
            print("SentryText model files not found. Active fallback keyword moderation will be used.")
            return False
    except Exception as e:
        print(f"Error loading models: {e}. Active fallback keyword moderation will be used.")
        return False

# Keyword list for fallback moderation
FALLBACK_TOXIC_KEYWORDS = {
    "mumu", "ode", "maga", "ashawo", "olodo", "ewu", "mgbeke", "comot",
    "thunder fire", "waka", "craze", "chinko", "basterd", "idiot", "stupid",
    "bastard", "loser", "hate you", "kill yourself", "trash user"
}

def fallback_moderation(text: str) -> dict:
    """
    A robust keyword-based safety net used when models are not yet trained.
    """
    text_lower = text.lower()
    flagged = any(word in text_lower for word in FALLBACK_TOXIC_KEYWORDS)
    
    if flagged:
        return {
            "classification": "Harmful",
            "confidence_score": 95.0,
            "moderation_status": "Blocked",
            "lr_classification": "Harmful",
            "lr_confidence": 95.0,
            "svm_classification": "Harmful",
            "svm_confidence": 95.0,
            "is_fallback": True
        }
    else:
        return {
            "classification": "Non-Harmful",
            "confidence_score": 100.0,
            "moderation_status": "Approved",
            "lr_classification": "Non-Harmful",
            "lr_confidence": 100.0,
            "svm_classification": "Non-Harmful",
            "svm_confidence": 100.0,
            "is_fallback": True
        }

def predict_comment(text: str) -> dict:
    """
    Predicts if a user input string contains cyberbullying using parallel Logistic Regression and SVM.
    Consensus Guardrail: If either model classifies text as harmful, it gets flagged as Blocked.
    """
    if not load_models():
        return fallback_moderation(text)
    
    # Preprocess text
    cleaned = clean_text(text)
    
    # If text is empty after cleaning, treat it as safe
    if not cleaned.strip():
        return {
            "classification": "Non-Harmful",
            "confidence_score": 100.0,
            "moderation_status": "Approved",
            "lr_classification": "Non-Harmful",
            "lr_confidence": 100.0,
            "svm_classification": "Non-Harmful",
            "svm_confidence": 100.0,
            "is_fallback": False
        }
        
    # Vectorize
    features = vectorizer.transform([cleaned])
    
    # 1. Logistic Regression Prediction
    lr_prob = lr_model.predict_proba(features)[0] # [prob_safe, prob_harmful]
    lr_pred_label = lr_model.predict(features)[0]  # 0 or 1
    lr_class = "Harmful" if lr_pred_label == 1 else "Non-Harmful"
    lr_conf = float(lr_prob[lr_pred_label] * 100.0)
    
    # 2. Support Vector Machine Prediction
    svm_prob = svm_model.predict_proba(features)[0] # [prob_safe, prob_harmful]
    svm_pred_label = svm_model.predict(features)[0]  # 0 or 1
    svm_class = "Harmful" if svm_pred_label == 1 else "Non-Harmful"
    svm_conf = float(svm_prob[svm_pred_label] * 100.0)
    
    # Consensus logic: Block if EITHER classifier flags as harmful
    is_harmful = (lr_pred_label == 1) or (svm_pred_label == 1)
    
    if is_harmful:
        final_class = "Harmful"
        final_status = "Blocked"
        # Average probability of the harmful (1) class across both models
        final_conf = float(((lr_prob[1] + svm_prob[1]) / 2.0) * 100.0)
    else:
        final_class = "Non-Harmful"
        final_status = "Approved"
        # Average probability of the safe (0) class across both models
        final_conf = float(((lr_prob[0] + svm_prob[0]) / 2.0) * 100.0)
        
    return {
        "classification": final_class,
        "confidence_score": round(final_conf, 2),
        "moderation_status": final_status,
        "lr_classification": lr_class,
        "lr_confidence": round(lr_conf, 2),
        "svm_classification": svm_class,
        "svm_confidence": round(svm_conf, 2),
        "is_fallback": False
    }
