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

def validate_models() -> bool:
    """
    Validates that the loaded models are working and compatible.
    Returns True if valid, False otherwise.
    """
    global vectorizer, lr_model, svm_model
    if vectorizer is None or lr_model is None or svm_model is None:
        return False
    try:
        test_features = vectorizer.transform(["test comment"])
        lr_model.predict_proba(test_features)
        svm_model.predict_proba(test_features)
        return True
    except Exception as e:
        print(f"SentryText ML models validation failed: {e}")
        return False

def auto_train_models():
    """
    Trains the models in-memory on startup if they are missing or incompatible,
    and attempts to save them to disk.
    """
    global vectorizer, lr_model, svm_model, models_loaded
    print("SentryText: Attempting auto-training of ML models...")
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.svm import SVC
        
        # Import local training data
        import sys
        # Ensure the api directory is in sys.path
        api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if api_dir not in sys.path:
            sys.path.append(api_dir)
            
        from scripts.slang_dictionary import MOCK_HARMFUL, MOCK_SAFE
        
        texts = MOCK_HARMFUL + MOCK_SAFE
        labels = [1] * len(MOCK_HARMFUL) + [0] * len(MOCK_SAFE)
        
        cleaned_texts = [clean_text(t) for t in texts]
        
        # Train Vectorizer
        new_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
        X = new_vectorizer.fit_transform(cleaned_texts)
        y = labels
        
        # Train Logistic Regression
        new_lr = LogisticRegression(C=2.0, max_iter=1000, random_state=42)
        new_lr.fit(X, y)
        
        # Train SVM
        new_svm = SVC(C=2.0, kernel='linear', probability=True, random_state=42)
        new_svm.fit(X, y)
        
        # Assign to globals
        vectorizer = new_vectorizer
        lr_model = new_lr
        svm_model = new_svm
        models_loaded = True
        print("SentryText: Inline auto-training of ML models completed successfully.")
        
        # Attempt to save to disk for future fast loading
        try:
            os.makedirs(MODELS_DIR, exist_ok=True)
            joblib.dump(vectorizer, vectorizer_path)
            joblib.dump(lr_model, lr_path)
            joblib.dump(svm_model, svm_path)
            print(f"SentryText: Saved auto-trained models to {MODELS_DIR}.")
        except Exception as save_err:
            print(f"SentryText Warning: Could not save auto-trained models to disk: {save_err}")
            
        return True
    except Exception as train_err:
        print(f"SentryText: Inline auto-training failed: {train_err}")
        return False

def load_models():
    """
    Dynamically loads the serialized models from disk and validates them.
    If they are missing or incompatible, triggers inline auto-training.
    Returns True if models are ready (either loaded or trained), False otherwise.
    """
    global vectorizer, lr_model, svm_model, models_loaded
    if models_loaded and validate_models():
        return True
        
    # Reset state to force reload/retrain
    models_loaded = False
    
    # 1. Try loading from disk
    try:
        if os.path.exists(vectorizer_path) and os.path.exists(lr_path) and os.path.exists(svm_path):
            vectorizer = joblib.load(vectorizer_path)
            lr_model = joblib.load(lr_path)
            svm_model = joblib.load(svm_path)
            
            # Validate loaded models
            if validate_models():
                models_loaded = True
                print("SentryText ML models loaded and validated successfully.")
                return True
            else:
                print("SentryText ML models on disk are incompatible. Initiating auto-training...")
        else:
            print("SentryText ML models not found on disk. Initiating auto-training...")
    except Exception as e:
        print(f"SentryText error loading models from disk: {e}. Initiating auto-training...")
        
    # 2. Fall back to auto-training if disk loading or validation failed
    if auto_train_models():
        return True
        
    print("SentryText: Failed to load or train ML models. Active fallback keyword moderation will be used.")
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
    try:
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
    except Exception as e:
        print(f"Runtime error during ML prediction: {e}. Using active fallback keyword moderation.")
        return fallback_moderation(text)
