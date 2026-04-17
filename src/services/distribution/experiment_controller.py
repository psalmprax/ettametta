import random
import logging
from typing import Any

logger = logging.getLogger("ExperimentController")

class ExperimentController:
    """
    10/10 Autonomy: The Imperial Exploration vs Exploitation Engine.
    Decides when to follow a proven winner and when to risk a production cycle 
    on a new narrative frontier.
    """
    
    def __init__(self, epsilon: float = 0.2):
        self.epsilon = epsilon # 20% exploration by default

    def classify_mission(self) -> dict[str, Any]:
        """Classifies the next content mission."""
        
        is_experiment = random.random() < self.epsilon
        
        if is_experiment:
            mission = {
                "type": "EXPERIMENTAL",
                "goal": "Discover New Narrative Frontiers",
                "risk_tolerance": "HIGH",
                "exploration_weight": 1.0,
                "strategy": "HIGH_TENSION_EXTREME_GAP" # Example experimental strategy
            }
            logger.info("🧪 [Experiment] Classifying Mission: EXPERIMENTAL (Exploration High)")
        else:
            mission = {
                "type": "SAFE",
                "goal": "Consistent Retention Floor",
                "risk_tolerance": "LOW",
                "exploration_weight": 0.0,
                "strategy": "PROVEN_HERMES_PATTERN"
            }
            logger.info("🛡️ [Experiment] Classifying Mission: SAFE (Exploitation High)")
            
        return mission

    def update_epsilon(self, system_health_score: float):
        """Dynamic tuning: If system is performing poorly, increase exploration."""
        if system_health_score < 0.5:
            self.epsilon = min(0.5, self.epsilon + 0.05)
        else:
            self.epsilon = max(0.1, self.epsilon - 0.02)

base_experiment_controller = ExperimentController()
