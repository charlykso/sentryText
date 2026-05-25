import os
import sys
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Add api directory to path to allow importing app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml_engine.preprocessor import clean_text
from scripts.slang_dictionary import MOCK_HARMFUL, MOCK_SAFE

def train():
    print("Preparing training data...")
    # Label 1 for Cyberbullying (Harmful), 0 for Non-Cyberbullying (Safe)
    texts = MOCK_HARMFUL + MOCK_SAFE
    labels = [1] * len(MOCK_HARMFUL) + [0] * len(MOCK_SAFE)
    
    print(f"Total training samples: {len(texts)} ({len(MOCK_HARMFUL)} Harmful, {len(MOCK_SAFE)} Safe)")
    
    # Preprocess texts
    print("Cleaning and preprocessing texts...")
    cleaned_texts = [clean_text(t) for t in texts]
    
    # Vectorization
    print("Vectorizing text using TF-IDF...")
    # Use sublinear TF scaling and unigrams+bigrams. Min document frequency of 1 as dataset is small
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    X = vectorizer.fit_transform(cleaned_texts)
    y = labels
    
    # Train Logistic Regression
    print("Training Logistic Regression model...")
    lr_model = LogisticRegression(C=2.0, max_iter=1000, random_state=42)
    lr_model.fit(X, y)
    
    # Train Support Vector Machine (SVM)
    # probability=True is needed to output confidence probabilities
    print("Training Support Vector Machine (SVM) model...")
    svm_model = SVC(C=2.0, kernel='linear', probability=True, random_state=42)
    svm_model.fit(X, y)
    
    # Evaluate models on training data
    lr_preds = lr_model.predict(X)
    svm_preds = svm_model.predict(X)
    
    print("\n--- Evaluation Metrics on Bootstrap Training Data ---")
    print("Logistic Regression:")
    print(f"  Accuracy:  {accuracy_score(y, lr_preds):.4f}")
    print(f"  Precision: {precision_score(y, lr_preds):.4f}")
    print(f"  Recall:    {recall_score(y, lr_preds):.4f}")
    print(f"  F1-Score:  {f1_score(y, lr_preds):.4f}")
    
    print("Support Vector Machine (SVM):")
    print(f"  Accuracy:  {accuracy_score(y, svm_preds):.4f}")
    print(f"  Precision: {precision_score(y, svm_preds):.4f}")
    print(f"  Recall:    {recall_score(y, svm_preds):.4f}")
    print(f"  F1-Score:  {f1_score(y, svm_preds):.4f}")
    
    # Save models
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
    os.makedirs(models_dir, exist_ok=True)
    
    vectorizer_path = os.path.join(models_dir, 'tfidf_vectorizer.joblib')
    lr_path = os.path.join(models_dir, 'lr_model.joblib')
    svm_path = os.path.join(models_dir, 'svm_model.joblib')
    
    print(f"\nSaving vectorizer and models to: {models_dir}...")
    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(lr_model, lr_path)
    joblib.dump(svm_model, svm_path)
    print("Model training and serialization completed successfully!")

if __name__ == '__main__':
    train()
