
import google.generativeai as genai
import os
import logging
from typing import Optional, List, Dict, Any, Union
import asyncio
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class UsageStats:
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

class GoogleClient:
    """Wrapper for Google Gemini API."""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Google API Key is required.")
        
        genai.configure(api_key=api_key)
        self.api_key = api_key
        
        # Default Models
        self.model_fast = "gemini-1.5-flash"
        self.model_smart = "gemini-1.5-pro"
        
        # State
        self.histories: Dict[int, Any] = {} # ChatSession storage
        self.total_usage = UsageStats()

    async def generate_content(
        self, 
        prompt: Union[str, List[Any]], 
        model_name: str = "gemini-1.5-pro",
        temperature: float = 0.7
    ) -> str:
        """
        Generate content using Gemini.
        Prompt can be a string or a list (for multimodal: [text, image]).
        """
        try:
            model = genai.GenerativeModel(model_name)
            
            # Run in executor because genai is synchronous
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature
                )
            )
            
            # Track Usage
            self._update_usage(response.usage_metadata, model_name)
            
            return response.text
            
        except Exception as e:
            logger.error(f"GoogleClient Error: {e}")
            raise

    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        model_name: str = "gemini-1.5-pro"
    ) -> str:
        """
        Chat compatible (OpenAI style messages -> Gemini history).
        Note: Simple conversion.
        """
        # Convert OpenAI messages to Gemini history
        # Limitation: Multi-turn history management in pure API is complex.
        # For now, we condense previous context or just send the last Prompt with context?
        # Better: Use generate_content with full string context for statelessness, 
        # or implement true ChatSession if needed.
        # Given "Hybrid" nature, we often use Cloud for ONE-SHOT heavy tasks.
        
        prompt_text = ""
        for m in messages:
            prompt_text += f"{m['role']}: {m['content']}\n"
        
        return await self.generate_content(prompt_text, model_name)

    def _update_usage(self, metadata, model_name: str):
        """Estimate cost and update stats."""
        if not metadata: return
        
        in_tok = metadata.prompt_token_count
        out_tok = metadata.candidates_token_count
        
        self.total_usage.input_tokens += in_tok
        self.total_usage.output_tokens += out_tok
        
        # Approx Pricing (Dec 2025)
        # Pro: $1.25/1M in, $5.00/1M out
        # Flash: $0.075/1M in, $0.30/1M out
        
        price_in = 1.25 if "pro" in model_name else 0.075
        price_out = 5.00 if "pro" in model_name else 0.30
        
        cost = (in_tok / 1_000_000 * price_in) + (out_tok / 1_000_000 * price_out)
        self.total_usage.estimated_cost_usd += cost
        
        logger.info(f"Gemini Usage: {in_tok}in/{out_tok}out (~${cost:.4f})")

    def get_credits_used(self) -> float:
        return self.total_usage.estimated_cost_usd

