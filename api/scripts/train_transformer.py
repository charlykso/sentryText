import os
import sys
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_scheduler
from torch.optim import AdamW

# Add api directory to path to allow importing app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml_engine.preprocessor import clean_text
from scripts.slang_dictionary import MOCK_HARMFUL, MOCK_SAFE

# Augmented dataset for sarcasm, negation, and pidgin nuance to highlight attention capabilities
AUGMENTED_HARMFUL = [
    "Wow, you must be a genius to make such a dumb mistake.",
    "Oh great, the clown is talking again.",
    "Oh, look who decided to show up, the absolute failure.",
    "You must think you are very smart, but you're just an idiot.",
    "Love how you try to act cool when everyone hates you.",
    "Such a brilliant explanation, too bad it makes no sense at all.",
    "Look at this big fool, thinking he is a champion. You be complete mumu.",
    "Nice one, olodo. You failed again.",
    "Oh yes, keep talking, we love listening to your trash opinions.",
]

AUGMENTED_SAFE = [
    "I don't think you are stupid, you are actually quite smart.",
    "You are not a loser, don't believe what they say.",
    "This is not a bad design at all.",
    "I don't hate you, you are my friend.",
    "Do not go kill yourself, seek help instead.",
    "I am not saying you are a mumu, you are correct.",
    "It is not true that she is an ashawo.",
    "He is not an olodo, he passed all his exams.",
    "No shaking, you are not stupid.",
    "No shaking, this guy is correct and funny.",
]

class CommentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(label, dtype=torch.long)
        }

def train_transformer():
    print("Preparing data for Transformer training...")
    
    # Standard dataset augmented with sarcasm and negation examples
    texts = MOCK_HARMFUL + MOCK_SAFE + AUGMENTED_HARMFUL + AUGMENTED_SAFE
    labels = (
        [1] * len(MOCK_HARMFUL) + 
        [0] * len(MOCK_SAFE) + 
        [1] * len(AUGMENTED_HARMFUL) + 
        [0] * len(AUGMENTED_SAFE)
    )
    
    print(f"Total training samples: {len(texts)} ({len(MOCK_HARMFUL) + len(AUGMENTED_HARMFUL)} Harmful, {len(MOCK_SAFE) + len(AUGMENTED_SAFE)} Safe)")
    
    # Initialize tokenizer and model
    model_name = "distilbert-base-multilingual-cased"
    print(f"Loading pre-trained tokenizer and model for '{model_name}'...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    
    # Device configuration (MPS support for Apple Silicon, CPU as default fallback)
    device = torch.device("cpu")
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Using MPS acceleration for training.")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("Using CUDA acceleration for training.")
    else:
        print("Using CPU for training.")
        
    model.to(device)
    
    # Prepare DataLoader
    dataset = CommentDataset(texts, labels, tokenizer)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    # Optimizer & Scheduler
    optimizer = AdamW(model.parameters(), lr=5e-5)
    num_epochs = 5
    num_training_steps = num_epochs * len(dataloader)
    lr_scheduler = get_scheduler(
        "linear",
        optimizer=optimizer,
        num_warmup_steps=0,
        num_training_steps=num_training_steps
    )
    
    print("Starting fine-tuning...")
    model.train()
    for epoch in range(num_epochs):
        total_loss = 0
        correct_predictions = 0
        total_samples = 0
        
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            batch_labels = batch["labels"].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=batch_labels)
            loss = outputs.loss
            logits = outputs.logits
            
            loss.backward()
            optimizer.step()
            lr_scheduler.step()
            
            total_loss += loss.item()
            predictions = torch.argmax(logits, dim=-1)
            correct_predictions += torch.sum(predictions == batch_labels).item()
            total_samples += batch_labels.size(0)
            
        epoch_loss = total_loss / len(dataloader)
        epoch_acc = correct_predictions / total_samples
        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {epoch_loss:.4f} - Accuracy: {epoch_acc:.4f}")
        
    # Save the fine-tuned model and tokenizer
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
    save_path = os.path.join(models_dir, "transformer_classifier")
    os.makedirs(save_path, exist_ok=True)
    
    print(f"Saving fine-tuned model to {save_path}...")
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    print("Transformer model training and serialization completed successfully!")

if __name__ == "__main__":
    train_transformer()
