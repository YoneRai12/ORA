import logging
import json
import os
from typing import List, Dict, Any, Optional
from src.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

class ToolSelector:
    """
    RAG-style Tool Selector (Router).
    Analyzes user prompt and selects relevant tools based on intent and platform context.
    """
    
    def __init__(self, bot):
        self.bot = bot
        # Use a lightweight model for routing to keep latency low
        self.model_name = "gpt-4o-mini" 
        
        # Access key from bot config
        api_key = self.bot.config.openai_api_key or os.getenv("OPENAI_API_KEY")
        
        self.llm_client = LLMClient(
            base_url="https://api.openai.com/v1",
            api_key=api_key,
            model=self.model_name
        )

    async def select_tools(
        self, 
        prompt: str, 
        available_tools: List[Dict[str, Any]], 
        platform: str = "discord"
    ) -> List[Dict[str, Any]]:
        """
        Selects the most relevant tools for the given prompt and platform.
        """
        if not available_tools:
            return []

        # 1. Filter tools by platform constraints first (Hard Logic)
        # This is already partially done by get_context_tools, but we reinforce it here if needed.
        # For now, we assume available_tools is already platform-filtered by the caller.
        
        # 2. Construct System Prompt for the Router
        tool_names = [t["name"] for t in available_tools]
        tool_descriptions = []
        for t in available_tools:
            desc = t.get("description", "No description")
            # Include tags if available for better matching
            tags = t.get("tags", [])
            tag_str = f" [Tags: {', '.join(tags)}]" if tags else ""
            tool_descriptions.append(f"- {t['name']}: {desc}{tag_str}")

        system_prompt = (
            f"You are an AI Tool Router for the ORA System.\n"
            f"Current Platform: {platform.upper()}\n"
            f"Analyze the User Prompt and select the necessary tools to fulfill the request.\n"
            f"Return a list of tool names found in the provided Available Tools list.\n"
            f"Rules:\n"
            f"1. Only select tools that are directly relevant.\n"
            f"2. If the user just wants to chat (no specific action), return an empty list.\n"
            f"3. For Voice requests (join, leave, speak), maximize recall of voice tools.\n"
            f"4. OUTPUT FORMAT: JSON Array of strings. Example: [\"tool_a\", \"tool_b\"]\n\n"
            f"Available Tools:\n" + "\n".join(tool_descriptions)
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Prompt: {prompt}"}
        ]

        try:
            # 3. Call LLM
            # We use a low temperature for deterministic routing
            response_text, _, _ = await self.llm_client.chat(messages, temperature=0.0)
            
            if not response_text:
                logger.warning("Router returned empty response.")
                return []

            # 4. Parse JSON
            # Clean up potential markdown code blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            selected_names = json.loads(clean_text)
            
            if not isinstance(selected_names, list):
                logger.warning(f"Router returned invalid format: {selected_names}")
                return []

            # 5. Map back to tool objects
            selected_tools = []
            for name in selected_names:
                for tool in available_tools:
                    if tool["name"] == name:
                        selected_tools.append(tool)
                        break
            
            logger.info(f"🧩 Router Selected {len(selected_tools)}/{len(available_tools)} tools: {selected_names}")
            return selected_tools

        except Exception as e:
            logger.error(f"Router Selection Failed: {e}")
            # Fallback: Return ALL tools or NO tools?
            # Safe Fallback: Return ALL tools to ensure functionality (though higher cost)
            # Or EMPTY to prevent hallucination?
            # Given the user wants RAG, fallback to ALL might defeat purpose, but ensures it works.
            # user said "AIを使ってツールをRAGする", implies filtering is key.
            # Let's return empty, forcing simple chat if router fails? 
            # No, safer to return all so standard agent can try.
            logger.warning("Falling back to ALL tools.")
            return available_tools
