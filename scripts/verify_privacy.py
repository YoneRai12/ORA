import logging
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.utils.privacy import PrivacyFilter

def test_privacy_filter():
    print("--- Privacy Filter Test ---")
    
    # Setup test logger
    logger = logging.getLogger("test_privacy")
    logger.setLevel(logging.INFO)
    
    # Handler with Filter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    handler.addFilter(PrivacyFilter())
    logger.addHandler(handler)
    
    test_messages = [
        "Connecting to 127.0.0.1:8008...",
        "Failed to reach host='192.168.1.100' on port 443",
        "Error: Cannot connect to host 1.2.3.4:8188 ssl:default",
        "Local service at localhost is down.",
        "DEBUG: API_URL=http://127.0.0.1:8000/v1",
    ]
    
    for msg in test_messages:
        print(f"Original: {msg}")
        logger.info(msg)
        print("-" * 20)

if __name__ == "__main__":
    test_privacy_filter()
