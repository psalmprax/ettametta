"""
Self Optimizer — Learns and Improves Automatically

Analyzes performance data, identifies patterns, and adjusts strategies.
The system gets smarter over time by learning from what works.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/revenue_engine/optimization")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class OptimizationRule:
    rule_id: str
    category: str
    condition: str
    action: str
    confidence: float = 0.0
    success_rate: float = 0.0
    times_applied: int = 0
    times_succeeded: int = 0
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class LearningEntry:
    category: str
    observation: str
    action_taken: str
    outcome: str
    lesson: str
    learned_at: str = ""

    def __post_init__(self):
        if not self.learned_at:
            self.learned_at = datetime.now().isoformat()


class SelfOptimizer:
    """Learns from results and improves strategies over time."""

    def __init__(self):
        self.rules: list[OptimizationRule] = []
        self.learnings: list[LearningEntry] = []
        self._load_rules()

    def _load_rules(self):
        """Load existing optimization rules."""
        rules_file = DATA_DIR / "rules.json"
        if rules_file.exists():
            try:
                data = json.loads(rules_file.read_text())
                self.rules = [OptimizationRule(**r) for r in data]
            except Exception as e:
                logger.warning(f"Failed to load rules: {e}")

        learnings_file = DATA_DIR / "learnings.json"
        if learnings_file.exists():
            try:
                data = json.loads(learnings_file.read_text())
                self.learnings = [LearningEntry(**l) for l in data]
            except Exception as e:
                logger.warning(f"Failed to load learnings: {e}")

    def analyze_and_optimize(self, metrics_history: list) -> list[OptimizationRule]:
        """Analyze metrics and create/update optimization rules."""
        new_rules = []

        for metrics in metrics_history:
            if hasattr(metrics, 'conversion_rate') and hasattr(metrics, 'views'):
                if metrics.conversion_rate > 5 and metrics.views > 50:
                    rule = OptimizationRule(
                        rule_id=f"high_convert_{metrics.product_name}",
                        category="pricing",
                        condition=f"conversion_rate > 5% AND views > 50 for {metrics.product_name}",
                        action=f"Consider raising price for {metrics.product_name}",
                        confidence=0.7,
                    )
                    new_rules.append(rule)

                if metrics.views > 200 and metrics.sales < 5:
                    rule = OptimizationRule(
                        rule_id=f"low_convert_{metrics.product_name}",
                        category="listing",
                        condition=f"views > 200 AND sales < 5 for {metrics.product_name}",
                        action=f"Rewrite listing title and description for {metrics.product_name}",
                        confidence=0.8,
                    )
                    new_rules.append(rule)

        self.rules.extend(new_rules)
        self._save_rules()
        return new_rules

    def record_learning(self, learning: LearningEntry):
        """Record a new learning."""
        self.learnings.append(learning)
        self._save_learnings()

    def get_recommendations(self, context: str = "") -> list[str]:
        """Get recommendations based on learned patterns."""
        recommendations = []

        for rule in self.rules:
            if rule.confidence > 0.6 and rule.success_rate > 0.5:
                recommendations.append(f"[{rule.category}] {rule.action}")

        category_counts = {}
        for learning in self.learnings:
            cat = learning.category
            category_counts[cat] = category_counts.get(cat, 0) + 1

        if category_counts.get("pricing", 0) > 3:
            recommendations.append("Review pricing strategy based on accumulated learnings")

        if category_counts.get("listing", 0) > 3:
            recommendations.append("Update listing optimization based on what's working")

        return recommendations[:10]

    def calculate_rule_success(self):
        """Recalculate success rates for all rules."""
        for rule in self.rules:
            if rule.times_applied > 0:
                rule.success_rate = rule.times_succeeded / rule.times_applied
        self._save_rules()

    def export_knowledge(self) -> dict:
        """Export accumulated knowledge as a portable format."""
        return {
            "rules_count": len(self.rules),
            "learnings_count": len(self.learnings),
            "rules": [asdict(r) for r in self.rules],
            "learnings": [asdict(l) for l in self.learnings],
            "exported_at": datetime.now().isoformat(),
        }

    def _save_rules(self):
        """Save rules to file."""
        path = DATA_DIR / "rules.json"
        path.write_text(json.dumps([asdict(r) for r in self.rules], indent=2))

    def _save_learnings(self):
        """Save learnings to file."""
        path = DATA_DIR / "learnings.json"
        path.write_text(json.dumps([asdict(l) for l in self.learnings], indent=2))
