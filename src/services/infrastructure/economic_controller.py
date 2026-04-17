import logging
import json
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger("EconomicController")

class EconomicController:
    """
    10/10 Production: The Imperial Treasury.
    Tracks virtual credits and enforces economic constraints on production.
    """
    
    def __init__(self, daily_budget: float = 1000.0, data_path: str = "data/infrastructure/treasury.json"):
        self.daily_budget = daily_budget
        self.data_path = data_path
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        if not os.path.exists(self.data_path):
            return {"date": str(datetime.now().date()), "credits_spent": 0.0}
        try:
            with open(self.data_path, "r") as f:
                state = json.load(f)
                if state.get("date") != str(datetime.now().date()):
                    return {"date": str(datetime.now().date()), "credits_spent": 0.0}
                return state
        except:
            return {"date": str(datetime.now().date()), "credits_spent": 0.0}

    def _save_state(self):
        with open(self.data_path, "w") as f:
            json.dump(self.state, f, indent=4)

    def authorize_spend(self, action: str, amount: float) -> bool:
        """Checks if the budget allows for the requested action."""
        if self.state["credits_spent"] + amount > self.daily_budget:
            logger.warning(f"💸 [Treasury] Budget Exceeded! Refusing to authorize '{action}' (Cost: {amount})")
            return False
            
        self.state["credits_spent"] += amount
        self._save_state()
        logger.info(f"💰 [Treasury] Authorized '{action}' (Cost: {amount}). Total Spent: {self.state['credits_spent']}/{self.daily_budget}")
        return True

    def get_vitals(self) -> dict[str, Any]:
        return {
            "daily_budget": self.daily_budget,
            "spent": self.state["credits_spent"],
            "remaining": self.daily_budget - self.state["credits_spent"],
            "efficiency": 1.0 - (self.state["credits_spent"] / self.daily_budget) if self.daily_budget > 0 else 0
        }

base_economic_controller = EconomicController()
