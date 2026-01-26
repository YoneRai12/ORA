import io
import logging
import time

# ruff: noqa: E402, B008, I001, F401

import torch
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import Response
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VisualCortex")

import os

# Configuration
# Default to PaliGemma/T5Gemma based models
MODEL_PATH = "google/paligemma-3b-pt-224" 
if os.path.exists(r"models/VisualCortex"):
    MODEL_PATH = r"models/VisualCortex"
elif os.path.exists(r"L:\AI_Models\T5Gemma\VisualCortex") and os.name == "nt":
    MODEL_PATH = r"L:\AI_Models\T5Gemma\VisualCortex"
elif os.path.exists(r"models/paligemma-3b-pt-224"):
    MODEL_PATH = r"models/paligemma-3b-pt-224"

DEVICE = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
DTYPE = torch.bfloat16 if DEVICE != "cpu" else torch.float32

# Global State
model = None
processor = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, processor
    try:
        logger.info(f"Loading Visual Cortex from {MODEL_PATH}...")
        start_time = time.time()

        # Fix for certain tokenizers (e.g. Gemma/Mistral regex warnings)
        processor = AutoProcessor.from_pretrained(
            MODEL_PATH, 
            trust_remote_code=True
        )
        
        # Ensure image_token_id is present if expected by model
        if hasattr(processor, "tokenizer"):
            if not hasattr(processor.tokenizer, "image_token_id"):
                # Multimodal models usually have an image token. 
                # If the tokenizer is missing it but the processor has it, sync them.
                if hasattr(processor, "image_token_id"):
                    processor.tokenizer.image_token_id = processor.image_token_id
                    logger.info(f"Patched tokenizer with image_token_id: {processor.image_token_id}")
                else:
                    # Fallback to a common value if still missing (specific to T5Gemma/PaliGemma)
                    # For T5Gemma, if not found, we might need to find it from the config or 
                    # use a known ID. Let's try to find it in special_tokens_map if possible.
                    pass
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH, 
            device_map=DEVICE, 
            torch_dtype=DTYPE, 
            trust_remote_code=True
        ).eval()

        logger.info(f"Visual Cortex Loaded in {time.time() - start_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to load Visual Cortex: {e}")
    
    yield
    # Shutdown logic (optional)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

app = FastAPI(title="ORA Visual Cortex", version="1.0", lifespan=lifespan)


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...), prompt: str = Form("Describe this image in detail.")):
    """
    Analyzes an image using T5Gemma 2 4B.
    """
    if not model or not processor:
        return {"error": "Visual Cortex model not loaded."}

    try:
        # Load Image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Prepare Inputs
        # Note: T5Gemma 2 usage might vary slightly based on "Aratako" vs "Google" implementation details.
        # Assuming standard Paligemma/Florence/T5Gemma prompting style if applicable.
        # For general multimodal:
        inputs = processor(text=prompt, images=image, return_tensors="pt").to(DEVICE)

        # Improvements: Add generation config for JSON/OCR if needed
        with torch.inference_mode():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,  # Deterministic for OCR/Description
            )

        # Decode
        result_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # Specific T5Gemma Cleanup (Input echo removal often needed)
        if result_text.startswith(prompt):
            result_text = result_text[len(prompt) :].strip()

        return {"status": "success", "analysis": result_text}

    except Exception as e:
        logger.error(f"Inference Error: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    try:
        from src.utils.logging_config import get_privacy_log_config
        log_config = get_privacy_log_config()
    except ImportError:
        log_config = None

    # visual cortex runs on port 8004
    uvicorn.run(app, host="127.0.0.1", port=8004, log_config=log_config)
