"""
Generate PDF product for AI Prompts Business pack.
"""
from pathlib import Path

PRODUCT_DIR = Path("/home/psalmprax/ALL_PROJECTS/ettametta/products/ai-prompts-business")

# Create the product content as markdown (will be converted to PDF)
content = """# 50 AI Prompts for Business Owners

## Stop Wasting Hours on Content Creation

This prompt pack gives you **50 battle-tested AI prompts** to automate your business marketing, sales, and operations.

---

## What's Inside

### Marketing Prompts (10)

1. Generate a week of social media posts for [your business]
2. Write 5 email subject lines that get opened
3. Create a Google My Business description that ranks
4. Generate 10 Instagram captions for [niche]
5. Write a blog post outline on [topic]
6. Create 5 TikTok video scripts
7. Generate LinkedIn posts that get engagement
8. Write product descriptions that convert
9. Create ad copy for Facebook/Instagram
10. Generate a content calendar for [month]

### Sales Prompts (10)

11. Write a cold email that gets replies
12. Create a sales page headline
13. Generate objection-handling responses
14. Write a webinar registration page
15. Create upsell copy for [product]
16. Generate follow-up email sequences
17. Write a pitch deck script
18. Create a proposal template
19. Generate testimonial request emails
20. Write a sales script for cold calls

### Operations Prompts (10)

21. Create standard operating procedures
22. Write employee handbooks
23. Generate meeting agendas
24. Create project timelines
25. Write performance review templates
26. Generate customer service scripts
27. Create onboarding checklists
28. Write policy documents
29. Generate report templates
30. Create training materials

### Content Creation Prompts (10)

31. Write blog posts that rank on Google
32. Create YouTube video scripts
33. Generate podcast episode outlines
34. Write newsletter content
35. Create infographic text
36. Generate case study templates
37. Write white paper outlines
38. Create presentation decks
39. Generate webinar scripts
40. Write press releases

### Strategy Prompts (10)

41. Create a marketing strategy outline
42. Generate competitor analysis
43. Write a business plan summary
44. Create a pricing strategy
45. Generate customer personas
46. Write a SWOT analysis
47. Create growth hacking ideas
48. Generate partnership outreach
49. Write a fundraising pitch
50. Create a 90-day action plan

---

## How to Use

1. Copy any prompt
2. Paste into ChatGPT, Claude, or any AI tool
3. Replace [brackets] with your details
4. Get professional results in seconds

## Bonus: Prompt Formula

I am a [your role] who [what you do].
I need you to [what you want].
The output should be [format].
Tone: [professional/casual/friendly]
Length: [short/medium/detailed]

---

© 2026 All rights reserved.
"""

# Save as markdown (can be converted to PDF later)
readme_path = PRODUCT_DIR / "50-ai-prompts-for-business.md"
readme_path.write_text(content)
print(f"Created: {readme_path}")

# Create product metadata
import json
metadata = {
    "name": "50 AI Prompts for Business Owners",
    "slug": "50-ai-prompts-business",
    "price": 9.99,
    "currency": "USD",
    "description": "50 battle-tested AI prompts to automate your business marketing, sales, and operations. Save 10+ hours per week.",
    "tags": ["ai prompts", "business", "marketing", "chatgpt", "productivity"],
    "category": "Digital Product",
    "file": "50-ai-prompts-for-business.md",
    "platforms": {
        "gumroad": {"status": "ready"},
        "lemonsqueezy": {"status": "ready"},
        "payhip": {"status": "ready"},
    }
}

meta_path = PRODUCT_DIR / "metadata.json"
meta_path.write_text(json.dumps(metadata, indent=2))
print(f"Created: {meta_path}")

print("\nProduct ready for listing!")
