import logging
import requests
from api.config import settings
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)

class ChatSalesSkill(OpenClawBaseSkill):
    """
    CashClaw Official Skill: Chat Sales
    Handles 2-way conversational sales via Social DMs and WhatsApp.
    """
    def execute(self, action: str = "reply", platform: str = "", target_identifier: str = "", context: str = "", **kwargs) -> str:
        """
        Executes the Chat Sales mission.
        """
        plt = platform or kwargs.get("platform")
        target = target_identifier or kwargs.get("target_identifier")
        ctx = context or kwargs.get("context")
        
        if not plt or not target or not ctx:
            return "⚠️ Chat Sales failed: Missing platform, target_identifier, or context"

        self.logger.info(f"[Chat Sales] Initiating conversational sales on {plt} for {target}")
        
        try:
            # Simulated Groq/LLM call for Chat Sales Agent
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Social Selling closer. Your goal is to convert "
                            "the user based on their context and intent. Keep the response short, "
                            "friendly, and end with a clear Call to Action (CTA)."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Platform: {plt}\nUser ID: {target}\nContext: {ctx}",
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.7,
                "max_tokens": 300,
            }
            
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15,
            )
            
            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"]
                return f"💬 **Chat Sales Generated Response**\n\n{reply}"
            else:
                return f"⚠️ Chat Sales failed: Status {resp.status_code}"
                
        except Exception as e:
            self.logger.error(f"Chat Sales Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

chat_sales_skill = ChatSalesSkill()
