
import logging
from typing import Optional, List, Dict, Any
from .llm_client import LLMClient
from .google_client import GoogleClient
from .config import Config

logger = logging.getLogger("ORA.UnifiedClient")

class UnifiedClient:
    """
    Manages connections to multiple LLM providers (Lanes).
    Lane A: Gemini Trial (Burn) -> GoogleClient
    Lane B: OpenAI Shared (Stable) -> LLMClient (to OpenAI API)
    Lane C: Local (Private) -> LLMClient (to Local vLLM)
    """
    def __init__(self, config: Config, local_llm: LLMClient, google_client: Optional[GoogleClient]):
        self.config = config
        self.local_llm = local_llm
        self.google_client = google_client
        
        # Initialize OpenAI Client if Key exists
        self.openai_client: Optional[LLMClient] = None
        if self.config.openai_api_key:
            self.openai_client = LLMClient(
                base_url="https://api.openai.com/v1",
                api_key=self.config.openai_api_key,
                model="gpt-4o-mini" # Low cost / free tier target
            )
            logger.info("✅ UnifiedClient: OpenAI Adapter initialized.")
        else:
            logger.info("ℹ️ UnifiedClient: OpenAI API Key missing. OpenAI Lane disabled.")

    async def chat(self, provider: str, messages: List[Dict[str, Any]], **kwargs) -> Optional[str]:
        """
        Unified chat interface.
        provider: 'local', 'gemini_trial', 'openai', 'gemini_dev'
        """
        try:
            if provider == "local":
                return await self.local_llm.chat(messages, **kwargs)
            
            elif provider == "gemini_trial":
                if not self.google_client:
                    raise RuntimeError("Gemini Client not initialized.")
                # GoogleClient uses 'gemini-1.5-pro' by default or passed model_name
                # We force it here or let caller decide?
                # CostManager/Router logic dictates model usually.
                model_name = kwargs.get("model_name", "gemini-1.5-pro")
                return await self.google_client.chat(messages, model_name=model_name)

            elif provider == "openai":
                if not self.openai_client:
                    raise RuntimeError("OpenAI Client not initialized.")
                # OpenAI Shared Tier (Chat Only)
                # Model selection via kwargs (default handled in LLMClient if not passed)
                return await self.openai_client.chat(messages, **kwargs)
            
            # Add more providers here
            
            else:
                 logger.error(f"Unknown provider: {provider}")
                 return None

        except Exception as e:
            logger.error(f"UnifiedClient Error ({provider}): {e}")
            raise e
