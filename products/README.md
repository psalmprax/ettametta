# Ettametta Products

Digital products for sale on Gumroad, LemonSqueezy, Payhip, and Etsy.

## Structure

```
products/
├── prompts/           # AI prompt packs
│   └── ai-prompts-business/
├── templates/         # Notion templates, social media kits
│   ├── notion-business-templates/
│   └── social-media-kit/
├── business/          # Business tools (contracts, legal)
│   └── freelancer-contracts/
├── scripts/           # Product creation automation
│   ├── create_product.py
│   └── generate_all_content.py
└── docs/              # Setup guides and listings
    ├── SETUP_GUIDE.md
    └── gumroad_listings.md
```

## Adding New Products

1. Create folder in appropriate category (prompts/templates/business)
2. Add `metadata.json` with product details
3. Run `scripts/generate_all_content.py` to create marketing materials
4. Upload to Gumroad automatically:

```bash
# First time - save login cookies
python3 scripts/quick_gumroad.py --save-cookies

# Setup product (opens browser, auto-fills everything)
python3 scripts/gumroad_setup.py prompts/ai-prompts-business
```

Or manual upload using `docs/SETUP_GUIDE.md`

## Product Checklist

- [ ] Product file (PDF, MD, or ZIP)
- [ ] Cover image (1280x720 recommended)
- [ ] Description (sales-focused, no markdown headers)
- [ ] Price set
- [ ] Tags added
- [ ] Listed on: Gumroad, LemonSqueezy, Payhip, Etsy