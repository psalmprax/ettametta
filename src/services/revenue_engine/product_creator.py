"""
Product Creator — Automated Digital Product Generation

Creates digital products (templates, guides, checklists, prompt packs)
based on market research insights.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/revenue_engine")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Product:
    name: str
    niche: str
    product_type: str  # template, guide, checklist, prompt_pack, bundle
    description: str = ""
    price: float = 9.99
    files: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    target_audience: str = ""
    problem_solved: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


PRODUCT_TEMPLATES = {
    "template": {
        "types": ["Canva template", "Notion template", "Google Docs template", "spreadsheet"],
        "price_range": (7, 29),
    },
    "guide": {
        "types": ["PDF guide", "checklist", "step-by-step tutorial", "resource list"],
        "price_range": (9, 19),
    },
    "prompt_pack": {
        "types": ["ChatGPT prompts", "AI prompt templates", "automation scripts"],
        "price_range": (9, 29),
    },
    "bundle": {
        "types": ["template bundle", "resource kit", "starter pack"],
        "price_range": (19, 49),
    },
    "checklist": {
        "types": ["action checklist", "audit checklist", "planning checklist"],
        "price_range": (5, 15),
    },
}


class ProductCreator:
    """Creates digital products based on market research."""

    def generate_product(self, niche: str, product_type: str = "template") -> Product:
        """Generate a product concept for a niche."""
        template = PRODUCT_TEMPLATES.get(product_type, PRODUCT_TEMPLATES["template"])
        price_range = template["price_range"]
        suggested_type = template["types"][0]

        name = self._generate_name(niche, suggested_type)
        description = self._generate_description(niche, suggested_type)
        tags = self._generate_tags(niche)
        target_audience = self._infer_audience(niche)
        problem = self._infer_problem(niche)

        return Product(
            name=name,
            niche=niche,
            product_type=product_type,
            description=description,
            price=round((price_range[0] + price_range[1]) / 2, 2),
            tags=tags,
            target_audience=target_audience,
            problem_solved=problem,
        )

    def generate_multiple(
        self, niche: str, types: Optional[list[str]] = None
    ) -> list[Product]:
        """Generate multiple product variations for a niche."""
        if types is None:
            types = ["template", "guide", "checklist"]
        return [self.generate_product(niche, t) for t in types]

    def _generate_name(self, niche: str, product_type: str) -> str:
        niche_title = niche.title()
        return f"{niche_title} {product_type.title()} Pack"

    def _generate_description(self, niche: str, product_type: str) -> str:
        niche_title = niche.title()
        return (
            f"Professional {product_type} designed for {niche_title}. "
            f"Instant download, easy to customize, and ready to use. "
            f"Save hours of work with this premium {product_type}."
        )

    def _generate_tags(self, niche: str) -> list[str]:
        base = niche.lower().split()
        tags = base.copy()
        tags.extend(["digital download", "template", "instant download", "editable"])
        return tags[:13]

    def _infer_audience(self, niche: str) -> str:
        words = niche.lower().split()
        if any(w in words for w in ["real estate", "property", "rental"]):
            return "Real estate professionals"
        if any(w in words for w in ["business", "marketing", "sales"]):
            return "Business owners and marketers"
        if any(w in words for w in ["freelance", "creator", "designer"]):
            return "Freelancers and creators"
        if any(w in words for w in ["teacher", "education", "school"]):
            return "Educators"
        return "Small business owners"

    def _infer_problem(self, niche: str) -> str:
        return f"Spending too much time creating {niche} materials from scratch"


class ProductFileManager:
    """Manages product file creation and organization."""

    def __init__(self, output_dir: str = "data/revenue_engine/products"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_product_manifest(self, product: Product) -> Path:
        """Create a product manifest file."""
        product_dir = self.output_dir / product.name.lower().replace(" ", "_")
        product_dir.mkdir(exist_ok=True)

        manifest_path = product_dir / "manifest.json"
        manifest_path.write_text(json.dumps(asdict(product), indent=2))

        readme_path = product_dir / "README.md"
        readme_path.write_text(
            f"# {product.name}\n\n"
            f"{product.description}\n\n"
            f"## Details\n"
            f"- Niche: {product.niche}\n"
            f"- Type: {product.product_type}\n"
            f"- Price: ${product.price}\n"
            f"- Target: {product.target_audience}\n"
            f"- Problem: {product.problem_solved}\n\n"
            f"## Tags\n{', '.join(product.tags)}\n"
        )

        logger.info(f"Created product manifest at {manifest_path}")
        return product_dir
