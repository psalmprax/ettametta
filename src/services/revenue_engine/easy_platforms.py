"""
Easy Platform Listers — Gumroad, Lemonsqueezy, Payhip

These platforms have:
- No monthly fees (take % of sales)
- Instant setup
- No CAPTCHA/bot protection
- API access
- Built-in payment processing
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class PlatformListing:
    platform: str
    product_name: str
    price: float
    description: str
    url: str = ""
    status: str = "pending"
    listing_url: str = ""
    notes: str = ""


class GumroadLister:
    """
    Gumroad — Easiest platform to start.

    Setup:
    1. Go to gumroad.com
    2. Sign up (free)
    3. Create product
    4. Upload file
    5. Set price
    6. Share link

    Fees: 10% per sale
    """

    PLATFORM = "gumroad"
    URL = "https://gumroad.com"

    def create_listing(self, product_dir: str) -> PlatformListing:
        """Create listing data for Gumroad."""
        meta_path = Path(product_dir) / "metadata.json"
        meta = json.loads(meta_path.read_text())

        return PlatformListing(
            platform=self.PLATFORM,
            product_name=meta["name"],
            price=meta["price"],
            description=meta["description"],
            url=self.URL,
            status="ready_to_list",
            notes=(
                "Manual steps:\n"
                "1. Go to gumroad.com/products/new\n"
                "2. Enter product name\n"
                "3. Set price to $9.99\n"
                "4. Upload the .md file\n"
                "5. Add description\n"
                "6. Publish"
            )
        )

    def get_setup_checklist(self) -> list[str]:
        return [
            "Create Gumroad account",
            "Verify email",
            "Set up payment (Stripe connect)",
            "Create new product",
            "Upload files",
            "Set price and description",
            "Publish and share link"
        ]


class LemonsqueezyLister:
    """
    Lemonsqueezy — Modern alternative to Gumroad.

    Setup:
    1. Go to lemonsqueezy.com
    2. Sign up (free)
    3. Create store
    4. Add product
    5. Set price
    6. Share link

    Fees: 5% + 50¢ per sale
    """

    PLATFORM = "lemonsqueezy"
    URL = "https://lemonsqueezy.com"

    def create_listing(self, product_dir: str) -> PlatformListing:
        meta_path = Path(product_dir) / "metadata.json"
        meta = json.loads(meta_path.read_text())

        return PlatformListing(
            platform=self.PLATFORM,
            product_name=meta["name"],
            price=meta["price"],
            description=meta["description"],
            url=self.URL,
            status="ready_to_list",
            notes=(
                "Manual steps:\n"
                "1. Go to lemonsqueezy.com\n"
                "2. Create store\n"
                "3. Products > New Product\n"
                "4. Upload files\n"
                "5. Set price to $9.99\n"
                "6. Publish"
            )
        )

    def get_setup_checklist(self) -> list[str]:
        return [
            "Create Lemonsqueezy account",
            "Set up store",
            "Connect Stripe/PayPal",
            "Create product",
            "Upload files",
            "Set price",
            "Publish"
        ]


class PayhipLister:
    """
    Payhip — Zero fees on free plan (5% on pro).

    Setup:
    1. Go to payhip.com
    2. Sign up (free)
    3. Add product
    4. Upload file
    5. Set price
    6. Share link

    Fees: 5% on free plan
    """

    PLATFORM = "payhip"
    URL = "https://payhip.com"

    def create_listing(self, product_dir: str) -> PlatformListing:
        meta_path = Path(product_dir) / "metadata.json"
        meta = json.loads(meta_path.read_text())

        return PlatformListing(
            platform=self.PLATFORM,
            product_name=meta["name"],
            price=meta["price"],
            description=meta["description"],
            url=self.URL,
            status="ready_to_list",
            notes=(
                "Manual steps:\n"
                "1. Go to payhip.com\n"
                "2. Create account\n"
                "3. Products > Add Product\n"
                "4. Choose 'Digital Product'\n"
                "5. Upload file\n"
                "6. Set price to $9.99\n"
                "7. Publish"
            )
        )

    def get_setup_checklist(self) -> list[str]:
        return [
            "Create Payhip account",
            "Add new product",
            "Select digital product",
            "Upload files",
            "Set price and description",
            "Publish",
            "Share link"
        ]


def list_all_platforms(product_dir: str) -> list[PlatformListing]:
    """List product on all easy platforms."""
    listers = [
        GumroadLister(),
        LemonsqueezyLister(),
        PayhipLister(),
    ]

    listings = []
    for lister in listers:
        listing = lister.create_listing(product_dir)
        listings.append(listing)

        print(f"\n{'='*50}")
        print(f"Platform: {listing.platform.upper()}")
        print(f"Product: {listing.product_name}")
        print(f"Price: ${listing.price}")
        print(f"Status: {listing.status}")
        print("\nSetup Steps:")
        print(listing.notes)

    return listings


if __name__ == "__main__":
    product_dir = "/home/psalmprax/ALL_PROJECTS/ettametta/products/ai-prompts-business"
    listings = list_all_platforms(product_dir)

    print(f"\n{'='*50}")
    print("SUMMARY: Ready to list on 3 platforms")
    print("="*50)

    # Save listings
    output_path = Path(product_dir) / "listings.json"
    output_path.write_text(json.dumps([asdict(l) for l in listings], indent=2))
    print(f"\nListings saved to: {output_path}")
