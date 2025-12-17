import time
import random
import json
import os
import sys

# Configuration
TOTAL_STEPS = 100
DATA_DIR = "data"
CHECKPOINT_DIR = "checkpoints"

def load_data():
    """Simulate loading data from data/ directory."""
    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' not found.")
        sys.exit(1)
        
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.jsonl')]
    if not files:
        print(f"Warning: No .jsonl files found in '{DATA_DIR}'. Using dummy data.")
        return ["dummy_sample"] * 100
        
    print(f"Loading data from {len(files)} files...")
    data = []
    for f in files:
        with open(os.path.join(DATA_DIR, f), 'r', encoding='utf-8') as fh:
            for line in fh:
                try:
                    data.append(json.loads(line))
                except:
                    pass
    return data

def train():
    print("Starting training...")
    data = load_data()
    print(f"Loaded {len(data)} samples.")
    
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    
    loss = 2.0
    for step in range(1, TOTAL_STEPS + 1):
        # Simulate training work
        time.sleep(0.1)
        
        # Simulate loss decreasing
        loss *= 0.99
        loss += random.uniform(-0.05, 0.05)
        if loss < 0: loss = 0.01
        
        # Log progress (Phoenix watches this)
        print(f"Step {step}/{TOTAL_STEPS} - loss: {loss:.4f}")
        
        # Simulate Validation every 10 steps
        if step % 10 == 0:
            val_loss = loss * 1.1 # Slightly higher than train loss
            print(f"Validation - val_loss: {val_loss:.4f}")
            
            # Simulate saving checkpoint
            with open(os.path.join(CHECKPOINT_DIR, f"checkpoint-{step}.pt"), 'w') as f:
                f.write("dummy checkpoint")
                
    print("Training complete.")

if __name__ == "__main__":
    train()
