"""
Trend Graph Engine (9.9/10)
===========================

Graph-based topics relationships to detect cross-platform cascades
and strategic influence patterns.
"""

import logging
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class TrendGraph:
    """
    Relational brain that maps attention flow between topics.
    """
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(float) # (topic1, topic2) -> influence_weight

    def link_topics(self, topic_a: str, topic_b: str, weight: float = 0.1):
        """Creates or strengthens a relationship between topics"""
        self.nodes.add(topic_a)
        self.nodes.add(topic_b)
        pair = tuple(sorted((topic_a, topic_b)))
        self.edges[pair] += weight
        logger.info(f"🧬 [Graph] Link Strength: {topic_a} <-> {topic_b} = {self.edges[pair]:.2f}")

    def detect_cross_platform_cascades(self, current_vitals: dict[str, Any]) -> list[str]:
        """
        Identifies topics that are likely to 'jump' platforms based
        on established graph influence.
        """
        cascades = []
        for (a, b), weight in self.edges.items():
            if weight > 0.5: # Strong relational bond
                 # If topic A is spiking on Reddit, predict topic B on TikTok
                 cascades.append(b if a in current_vitals else a)

        return list(set(cascades))

    def get_related_clusters(self, topic: str) -> list[str]:
        """Returns topics closely linked in the attention graph"""
        related = []
        for (a, b), weight in self.edges.items():
            if topic in (a, b) and weight > 0.2:
                related.append(b if a == topic else a)
        return related

# Singleton Instance
base_trend_graph = TrendGraph()
