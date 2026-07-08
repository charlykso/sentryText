import os
import sys

# Add api directory to path to allow importing app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml_engine.classifier import predict_comment
from app.ml_engine.preprocessor import clean_text

def test_system():
    print("=== SENTRYTEXT SYSTEM VERIFICATION ===")
    
    # 1. Test preprocessor
    raw_text = "Who is ready for some Jollof rice? Abeg come over!"
    cleaned = clean_text(raw_text)
    print(f"\n1. Preprocessing Test:")
    print(f"  Raw:     '{raw_text}'")
    print(f"  Cleaned: '{cleaned}'")
    
    # 2. Test ML classification predictions (Consensus Guardrails)
    test_cases = [
        # Safe cases (standard and slang)
        {"text": "Good morning my friends. Keep up the correct work on this app!", "expected": "Approved"},
        {"text": "This jollof recipe is ogbonge, i want to eat it. No shaking!", "expected": "Approved"},
        
        # Sarcastic and negation cases to contrast Transformer vs. Baseline models
        {"text": "I don't think you are stupid, you are actually quite smart.", "expected": "Approved"},
        {"text": "This is not a bad design at all.", "expected": "Approved"},
        {"text": "Wow, you must be a genius to make such a dumb mistake.", "expected": "Blocked"},
        {"text": "Oh great, the clown is talking again.", "expected": "Blocked"},
        
        # Toxic cases (standard and slang)
        {"text": "shut up you complete idiot, you don't know anything", "expected": "Blocked"},
        {"text": "look at this maga, craze dey worry that mumu boy. thunder fire you", "expected": "Blocked"}
    ]
    
    print("\n2. ML Classifier Comparative Consensus Tests:")
    all_passed = True
    for tc in test_cases:
        verdict = predict_comment(tc["text"])
        status = verdict["moderation_status"]
        passed = (status == tc["expected"])
        if not passed:
            all_passed = False
            
        print(f"  Input:   '{tc['text']}'")
        print(f"  Verdict:  {status} (Classification: {verdict['classification']}, Confidence: {verdict['confidence_score']}%)")
        print(f"  Model Breakdown:")
        print(f"    Transformer: {verdict.get('transformer_classification', 'N/A')} ({verdict.get('transformer_confidence', 0.0)}%)")
        print(f"    LR Baseline: {verdict['lr_classification']} ({verdict['lr_confidence']}%)")
        print(f"    SVM Baseline:{verdict['svm_classification']} ({verdict['svm_confidence']}%)")
        print(f"  Passed:  {'[PASS]' if passed else '[FAIL]'}")
        print("-" * 50)
        
    if all_passed:
        print("\nAll SentryText ML comparative consensus verification assertions passed successfully!")
    else:
        print("\nSome verification assertions failed. Please verify model files.")

if __name__ == '__main__':
    test_system()
