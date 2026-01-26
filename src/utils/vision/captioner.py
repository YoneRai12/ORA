import logging

from src.utils.unified_client import UnifiedClient

logger = logging.getLogger(__name__)


class ImageCaptioner:
    """
    Handles Multi-Modal understanding (Image/Video) using the VLM (Qwen2.5-VL).
    """

    def __init__(self, llm_client: UnifiedClient):
        self.llm = llm_client
        # Read from Config
        self.provider = self.llm.config.vision_provider

        # Models
        self.vision_model_local = "mistral-14b-vision"
        self.vision_model_openai = "gpt-5-mini"  # Stable Lane (2.5M tokens/day)

    async def describe_media(self, url: str, media_type: str = "image") -> str:
        """
        Generates a description for the given media URL.
        media_type: "image" or "video"
        """
        prompt = "この画像を詳細に描写してください。何が映っていますか？"
        if media_type == "video":
            prompt = "この動画の内容を詳細に要約してください。何が起きていますか？"

        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": url}}],
            }
        ]

        # Select Model based on Provider
        if self.provider == "openai":
            if media_type == "video":
                # OpenAI API doesn't support video URLs in standard chat completions easily.
                # Usually requires frame extraction. For now, we prefer fallbacks.
                logger.warning("Vision Analysis: OpenAI provider does not support direct video URLs. Requesting fallback.")
                # We force trial gemini if available, or error out gracefully
                if self.llm.google_client:
                    model = "gemini-1.5-flash" # Use Flash for video
                    target_provider = "gemini_trial"
                else:
                    return "(認識エラー: OpenAI は現在動画 URL を直接解析できません。Google Gemini API を有効にしてください。)"
            else:
                model = self.vision_model_openai
                target_provider = "openai"
        else:
            model = self.vision_model_local
            target_provider = self.provider

        try:
            logger.info(f"Vision Analysis ({target_provider}): {model} for {media_type}")

            content, _, _ = await self.llm.chat(
                provider=target_provider, messages=messages, model=model, temperature=0.7, max_tokens=1000
            )
            
            # Robustness: Handle Google API 403 / Disabled errors specifically
            if content and "Generative Language API has not been used" in content:
                logger.error(f"Vision Analysis: Google API is disabled. {content}")
                return "(認識失敗: Google Cloud Console で Generative Language API を有効にする必要があります。)"

            return content if content else "(認識失敗: 応答なし)"
        except Exception as e:
            err_msg = str(e)
            if "SERVICE_DISABLED" in err_msg or "403" in err_msg:
                 return "(認識エラー: Google Gemini API が未有効です。Cloud Console で有効化してください。)"
            logger.error(f"Vision Analysis Failed ({target_provider}): {e}")
            return f"(認識エラー: {err_msg})"
