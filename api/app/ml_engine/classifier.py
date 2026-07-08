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
transformer_load_attempted = False

# Google Gemini API Configurations (production LLM-based classification)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash-lite")
USE_LLM_API = bool(GEMINI_API_KEY)  # Auto-enabled when API key is present

# Classification prompt engineered for sarcasm, negation, and Nigerian Pidgin understanding
GEMINI_SYSTEM_PROMPT = """You are SentryText, a cyberbullying and harmful content detection system.
Classify the following user message as either "Harmful" or "Non-Harmful".

IMPORTANT RULES:
- Understand Nigerian Pidgin English slang: "mumu"=fool, "ode"=stupid, "maga"=victim/fool, "ashawo"=prostitute, "olodo"=dunce, "ewu"=goat(insult), "thunder fire"=curse, "craze"=crazy, "chinko"=derogatory, "comot"=get out(dismissive)
- Detect sarcasm used to bully (e.g., "Wow, you must be a genius to make such a dumb mistake" IS Harmful)
- Understand negation properly (e.g., "I don't think you are stupid, you are actually smart" is NOT Harmful)
- Casual conversation, friendly banter, jokes among friends, and constructive criticism are Non-Harmful
- Direct insults, threats, slurs, derogatory language, and cyberbullying are Harmful

Respond with ONLY a JSON object with exactly two fields:
- "classification": either "Harmful" or "Non-Harmful"
- "confidence": a number from 0 to 100"""

def query_gemini_api(text: str) -> dict:
    """
    Sends a classification request to the Google Gemini API.
    Returns prediction label and confidence score.
    """
    import requests
    import json
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_ID}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": f'{GEMINI_SYSTEM_PROMPT}\n\nMessage to classify: "{text}"'}]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 100,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "object",
                "properties": {
                    "classification": {"type": "string", "enum": ["Harmful", "Non-Harmful"]},
                    "confidence": {"type": "number"}
                },
                "required": ["classification", "confidence"]
            }
        }
    }
    
    # Retry with backoff for 429 rate limit errors (free tier: 15 RPM)
    import time
    max_retries = 2
    for attempt in range(max_retries + 1):
        response = requests.post(api_url, json=payload, timeout=10.0)
        if response.status_code == 429 and attempt < max_retries:
            wait_time = 2 ** attempt  # 1s, 2s backoff
            time.sleep(wait_time)
            continue
        response.raise_for_status()
        break
    
    result = response.json()
    
    # Parse Gemini response: candidates[0].content.parts[0].text contains JSON
    response_text = result["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(response_text)
    
    classification = parsed.get("classification", "Non-Harmful")
    confidence = float(parsed.get("confidence", 50.0))
    
    if classification not in ("Harmful", "Non-Harmful"):
        classification = "Non-Harmful"
    
    return {
        "classification": classification,
        "confidence": round(confidence, 2)
    }


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
        from sklearn.calibration import CalibratedClassifierCV
        
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
        base_svm = SVC(C=2.0, kernel='linear', random_state=42)
        new_svm = CalibratedClassifierCV(base_svm, ensemble=False)
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
    global transformer_load_attempted
    if not transformer_loaded and not transformer_load_attempted:
        transformer_load_attempted = True
        try:
            weights_exist = False
            if os.path.exists(transformer_path):
                files = os.listdir(transformer_path)
                has_config = any(f.startswith('config.json') for f in files)
                has_weights = any(f in ('model.safetensors', 'pytorch_model.bin') for f in files)
                if has_config and has_weights:
                    weights_exist = True
            
            if weights_exist:
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
                print("SentryText Transformer model weights not found on disk. Will use baseline models as primary/fallback.")
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
    Predicts if a user input string contains cyberbullying using either the Google Gemini API
    (primary LLM) or a local fine-tuned Transformer (fallback) with baseline SVM/LR telemetry.
    """
    try:
        global USE_LLM_API
        # Load baseline models and local transformer if available
        # Note: True is returned if baseline models are ready
        baselines_ok = load_models()
        
        # 1. Evaluate baseline models if they are loaded (for comparative research/telemetry)
        lr_class = "Non-Harmful"
        lr_conf = 100.0
        svm_class = "Non-Harmful"
        svm_conf = 100.0
        lr_pred_label = 0
        svm_pred_label = 0
        
        cleaned = clean_text(text)
        
        if baselines_ok and cleaned.strip() and vectorizer and lr_model and svm_model:
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
            
        # 2. Evaluate Transformer model (Primary engine: API preferred, local fallback)
        transformer_class = "Non-Harmful"
        transformer_conf = 100.0
        transformer_pred_label = 0
        transformer_active = False
        
        # Attempt Google Gemini LLM API first (understands sarcasm, negation, Nigerian Pidgin)
        if USE_LLM_API:
            try:
                api_result = query_gemini_api(text)
                transformer_class = api_result["classification"]
                transformer_conf = api_result["confidence"]
                transformer_pred_label = 1 if transformer_class == "Harmful" else 0
                transformer_active = True
            except Exception as api_err:
                import requests as _req
                is_rate_limit = isinstance(api_err, _req.exceptions.HTTPError) and hasattr(api_err, 'response') and api_err.response is not None and api_err.response.status_code == 429
                if is_rate_limit:
                    # Rate limit is temporary — don't disable API, just fall back for this request
                    print(f"SentryText: Gemini API rate limited (429). Falling back to baseline for this request.")
                else:
                    # Permanent failure (DNS, auth, server error) — disable API for session
                    USE_LLM_API = False
                    print(f"SentryText: Gemini API error, auto-disabled for this session. Using baseline models. ({type(api_err).__name__})")
                
        # Attempt Local Model fallback if API is disabled or failed, and local model is loaded
        if not transformer_active and transformer_loaded and transformer_tokenizer and transformer_model:
            try:
                import torch
                inputs = transformer_tokenizer(
                    text,
                    truncation=True,
                    padding="max_length",
                    max_length=128,
                    return_tensors="pt"
                )
                
                with torch.no_grad():
                    outputs = transformer_model(**inputs)
                    logits = outputs.logits
                    probabilities = torch.softmax(logits, dim=-1).squeeze(0)
                    
                transformer_pred_label = int(torch.argmax(probabilities).item())
                transformer_class = "Harmful" if transformer_pred_label == 1 else "Non-Harmful"
                transformer_conf = float(probabilities[transformer_pred_label].item() * 100.0)
                transformer_active = True
            except Exception as tr_err:
                print(f"SentryText: Error during local Transformer inference: {tr_err}")
                
        # 3. Determine final moderation status (Consensus / Primary logic)
        if transformer_active:
            is_harmful = (transformer_pred_label == 1)
            final_class = transformer_class
            final_status = "Blocked" if is_harmful else "Approved"
            final_conf = transformer_conf
        elif baselines_ok:
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
        else:
            return fallback_moderation(text)

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
            "is_fallback": not transformer_active
        }
    except Exception as e:
        print(f"Runtime error during ML prediction: {e}. Using active fallback keyword moderation.")
        return fallback_moderation(text)


