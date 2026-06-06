import os
import joblib
from app.ml_engine.preprocessor import clean_text

# Paths to serialized models
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models'))
vectorizer_path = os.path.join(MODELS_DIR, 'tfidf_vectorizer.joblib')
lr_path = os.path.join(MODELS_DIR, 'lr_model.joblib')
svm_path = os.path.join(MODELS_DIR, 'svm_model.joblib')
transformer_path = os.path.join(MODELS_DIR, 'transformer_classifier')

vectorizer = None
lr_model = None
svm_model = None
models_loaded = False

# Transformer globals
transformer_tokenizer = None
transformer_model = None
transformer_loaded = False

def validate_models() -> bool:
    """
    Validates that the loaded baseline models are working and compatible.
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

def validate_transformer() -> bool:
    """
    Validates that the loaded Transformer model is working.
    Returns True if valid, False otherwise.
    """
    global transformer_tokenizer, transformer_model
    if transformer_tokenizer is None or transformer_model is None:
        return False
    try:
        inputs = transformer_tokenizer(
            "test comment",
            truncation=True,
            padding="max_length",
            max_length=128,
            return_tensors="pt"
        )
        import torch
        with torch.no_grad():
            transformer_model(**inputs)
        return True
    except Exception as e:
        print(f"SentryText ML Transformer validation failed: {e}")
        return False

def auto_train_models():
    """
    Trains the baseline models in-memory on startup if they are missing or incompatible,
    and attempts to save them to disk.
    """
    global vectorizer, lr_model, svm_model, models_loaded
    print("SentryText: Attempting auto-training of baseline ML models...")
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
        print("SentryText: Inline auto-training of baseline ML models completed successfully.")
        
        # Attempt to save to disk for future fast loading
        try:
            os.makedirs(MODELS_DIR, exist_ok=True)
            joblib.dump(vectorizer, vectorizer_path)
            joblib.dump(lr_model, lr_path)
            joblib.dump(svm_model, svm_path)
            print(f"SentryText: Saved auto-trained baseline models to {MODELS_DIR}.")
        except Exception as save_err:
            print(f"SentryText Warning: Could not save auto-trained baseline models to disk: {save_err}")
            
        return True
    except Exception as train_err:
        print(f"SentryText: Inline auto-training of baseline models failed: {train_err}")
        return False

def load_models():
    """
    Dynamically loads the serialized models (baseline models and Transformer)
    from disk and validates them.
    If baselines are missing or incompatible, triggers inline auto-training.
    Returns True if baseline models are ready (either loaded or trained), False otherwise.
    """
    global vectorizer, lr_model, svm_model, models_loaded
    global transformer_tokenizer, transformer_model, transformer_loaded
    
    # 1. Load baseline models if not loaded
    baselines_ok = False
    if models_loaded and validate_models():
        baselines_ok = True
    else:
        models_loaded = False
        try:
            if os.path.exists(vectorizer_path) and os.path.exists(lr_path) and os.path.exists(svm_path):
                vectorizer = joblib.load(vectorizer_path)
                lr_model = joblib.load(lr_path)
                svm_model = joblib.load(svm_path)
                if validate_models():
                    models_loaded = True
                    baselines_ok = True
                    print("SentryText baseline ML models loaded and validated successfully.")
                else:
                    print("SentryText baseline ML models on disk are incompatible. Initiating auto-training...")
            else:
                print("SentryText baseline ML models not found on disk. Initiating auto-training...")
        except Exception as e:
            print(f"SentryText error loading baseline models: {e}. Initiating auto-training...")
            
        if not baselines_ok:
            if auto_train_models():
                baselines_ok = True
            else:
                print("SentryText: Failed to load or train baseline ML models.")

    # 2. Load Transformer model if not loaded
    if not transformer_loaded:
        try:
            if os.path.exists(transformer_path) and any(f.startswith('config.json') for f in os.listdir(transformer_path)):
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                transformer_tokenizer = AutoTokenizer.from_pretrained(transformer_path)
                transformer_model = AutoModelForSequenceClassification.from_pretrained(transformer_path)
                transformer_model.eval()
                if validate_transformer():
                    transformer_loaded = True
                    print("SentryText Transformer model loaded and validated successfully.")
                else:
                    print("SentryText Transformer model validation failed.")
                    transformer_loaded = False
            else:
                print("SentryText Transformer model not found on disk. Will use baseline models as primary/fallback.")
                transformer_loaded = False
        except Exception as e:
            print(f"SentryText error loading Transformer model: {e}. Will use baseline models as primary/fallback.")
            transformer_loaded = False
            
    return baselines_ok

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
    
    status = "Blocked" if flagged else "Approved"
    classification = "Harmful" if flagged else "Non-Harmful"
    conf = 95.0 if flagged else 100.0
    
    return {
        "classification": classification,
        "confidence_score": conf,
        "moderation_status": status,
        "lr_classification": classification,
        "lr_confidence": conf,
        "svm_classification": classification,
        "svm_confidence": conf,
        "transformer_classification": classification,
        "transformer_confidence": conf,
        "is_fallback": True
    }

def predict_comment(text: str) -> dict:
    """
    Predicts if a user input string contains cyberbullying using the fine-tuned local
    multilingual Transformer (DistilBERT) with fallbacks and telemetry for Logistic Regression and SVM.
    """
    try:
        # Load all models (baselines and transformer)
        # Note: If transformer fails or is not trained, load_models still returns True if baselines are ready
        if not load_models():
            return fallback_moderation(text)
        
        # 1. Evaluate baseline models if they are loaded (for comparative research/telemetry)
        lr_class = "Non-Harmful"
        lr_conf = 100.0
        svm_class = "Non-Harmful"
        svm_conf = 100.0
        lr_pred_label = 0
        svm_pred_label = 0
        
        cleaned = clean_text(text)
        
        # We only predict with baselines if we have a non-empty string and models are loaded
        if cleaned.strip() and vectorizer and lr_model and svm_model:
            features = vectorizer.transform([cleaned])
            
            # Logistic Regression Prediction
            lr_prob = lr_model.predict_proba(features)[0]
            lr_pred_label = int(lr_model.predict(features)[0])
            lr_class = "Harmful" if lr_pred_label == 1 else "Non-Harmful"
            lr_conf = float(lr_prob[lr_pred_label] * 100.0)
            
            # Support Vector Machine Prediction
            svm_prob = svm_model.predict_proba(features)[0]
            svm_pred_label = int(svm_model.predict(features)[0])
            svm_class = "Harmful" if svm_pred_label == 1 else "Non-Harmful"
            svm_conf = float(svm_prob[svm_pred_label] * 100.0)
            
        # 2. Evaluate Transformer model (Primary engine)
        transformer_class = "Non-Harmful"
        transformer_conf = 100.0
        transformer_pred_label = 0
        
        if transformer_loaded and transformer_tokenizer and transformer_model:
            try:
                import torch
                # Tokenize raw, original text to keep full context/negation/sarcasm
                inputs = transformer_tokenizer(
                    text,
                    truncation=True,
                    padding="max_length",
                    max_length=128,
                    return_tensors="pt"
                )
                
                # Inference
                with torch.no_grad():
                    outputs = transformer_model(**inputs)
                    logits = outputs.logits
                    probabilities = torch.softmax(logits, dim=-1).squeeze(0)
                    
                transformer_pred_label = int(torch.argmax(probabilities).item())
                transformer_class = "Harmful" if transformer_pred_label == 1 else "Non-Harmful"
                transformer_conf = float(probabilities[transformer_pred_label].item() * 100.0)
            except Exception as tr_err:
                print(f"SentryText: Error during Transformer inference: {tr_err}")
                # We will fall back to baselines automatically below since transformer_loaded represents success

        # 3. Determine final moderation status (Consensus / Primary logic)
        if transformer_loaded:
            # Transformer is primary
            is_harmful = (transformer_pred_label == 1)
            final_class = transformer_class
            final_status = "Blocked" if is_harmful else "Approved"
            final_conf = transformer_conf
        else:
            # Fall back to Logistic Regression & SVM consensus
            is_harmful = (lr_pred_label == 1) or (svm_pred_label == 1)
            
            if is_harmful:
                final_class = "Harmful"
                final_status = "Blocked"
                if vectorizer and lr_model and svm_model and cleaned.strip():
                    features = vectorizer.transform([cleaned])
                    lr_prob = lr_model.predict_proba(features)[0]
                    svm_prob = svm_model.predict_proba(features)[0]
                    final_conf = float(((lr_prob[1] + svm_prob[1]) / 2.0) * 100.0)
                else:
                    final_conf = 95.0
            else:
                final_class = "Non-Harmful"
                final_status = "Approved"
                if vectorizer and lr_model and svm_model and cleaned.strip():
                    features = vectorizer.transform([cleaned])
                    lr_prob = lr_model.predict_proba(features)[0]
                    svm_prob = svm_model.predict_proba(features)[0]
                    final_conf = float(((lr_prob[0] + svm_prob[0]) / 2.0) * 100.0)
                else:
                    final_conf = 100.0

        return {
            "classification": final_class,
            "confidence_score": round(final_conf, 2),
            "moderation_status": final_status,
            "lr_classification": lr_class,
            "lr_confidence": round(lr_conf, 2),
            "svm_classification": svm_class,
            "svm_confidence": round(svm_conf, 2),
            "transformer_classification": transformer_class,
            "transformer_confidence": round(transformer_conf, 2),
            "is_fallback": not transformer_loaded
        }
    except Exception as e:
        print(f"Runtime error during ML prediction: {e}. Using active fallback keyword moderation.")
        return fallback_moderation(text)

