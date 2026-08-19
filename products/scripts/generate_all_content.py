"""
Copy-Paste Content Generator
Generates all content ready to paste into platforms.
"""
import json
from pathlib import Path

PRODUCT_DIR = Path("/home/psalmprax/ALL_PROJECTS/ettametta/products/ai-prompts-business")

# Load metadata
meta = json.loads((PRODUCT_DIR / "metadata.json").read_text())

# === GUMROAD CONTENT ===
gumroad = {
    "name": meta["name"],
    "description": meta["description"],
    "price": meta["price"],
    "tags": ", ".join(meta["tags"]),
    "long_description": """
## What You Get

**50 battle-tested AI prompts** organized into 5 categories:

### Marketing (10 prompts)
- Social media content
- Email campaigns
- SEO optimization
- Ad copy
- Content calendars

### Sales (10 prompts)
- Cold outreach
- Sales pages
- Objection handling
- Follow-up sequences
- Proposals

### Operations (10 prompts)
- SOPs and processes
- Meeting templates
- Training materials
- Reports
- Onboarding

### Content (10 prompts)
- Blog posts
- Video scripts
- Newsletters
- Case studies
- Presentations

### Strategy (10 prompts)
- Business planning
- Competitor analysis
- Growth strategies
- Pricing
- Customer personas

## How It Works

1. Copy any prompt
2. Paste into ChatGPT, Claude, or any AI
3. Replace [brackets] with your details
4. Get professional results in seconds

## Who This Is For

- Small business owners
- Freelancers and solopreneurs
- Marketing managers
- Content creators
- Agency owners

## Why These Prompts?

I tested hundreds of prompts. These 50 consistently produce the best results across different AI tools and business types.

**Instant download. No subscription. Use forever.**
""",
}

# === REDDIT POSTS ===
reddit_posts = [
    {
        "subreddit": "r/SideProject",
        "title": "I created 50 AI prompts for business owners — free sample inside",
        "body": """Hey everyone,

I spent the last month testing AI prompts for business tasks. I found 50 that consistently produce great results.

Here are 3 free ones:

**Prompt 1: Social Media Content**
"I am a [your business] owner. Generate 7 days of social media posts for [platform]. Include hooks, content, and CTAs. Tone: [professional/casual]."

**Prompt 2: Cold Email**
"Write a cold email to [target customer] about [your product/service]. Focus on their pain point: [problem]. Keep it under 100 words. Include one clear CTA."

**Prompt 3: Sales Page**
"Create a sales page headline and 3 bullet points for [product]. Target audience: [who]. Main benefit: [what they get]. Price: [price]."

I packaged all 50 into a PDF with examples and formulas. It's $9.99 on Gumroad.

Link: [YOUR LINK]

Happy to answer questions about any of the prompts!"""
    },
    {
        "subreddit": "r/EntrepreneurRideAlong",
        "title": "These 50 AI prompts save me 10+ hours/week on marketing",
        "body": """Been using AI for my business for 6 months. Finally organized my best prompts into a pack.

**What's inside:**
- 10 marketing prompts (social, email, SEO)
- 10 sales prompts (outreach, proposals, follow-ups)
- 10 operations prompts (SOPs, reports, training)
- 10 content prompts (blogs, videos, newsletters)
- 10 strategy prompts (planning, analysis, growth)

**Results so far:**
- Social media posts: 5 min instead of 2 hours
- Cold emails: 3 min instead of 30 min
- Blog outlines: 2 min instead of 1 hour

**Cost:** $9.99 (one-time, no subscription)

Link: [YOUR LINK]

Ask me anything about using AI for business!"""
    },
    {
        "subreddit": "r/smallbusiness",
        "title": "Free AI prompt template for small business owners",
        "body": """Here's a prompt formula that works for any small business:

**The Formula:**
"I am a [role] at a [business type] that [what you do]. I need you to [task]. Target audience: [who]. Tone: [style]. Format: [output format]."

**Example:**
"I am a marketing manager at a local bakery that makes custom cakes. I need you to write 5 Instagram captions for our wedding cake showcase. Target audience: engaged couples aged 25-35. Tone: warm and professional. Format: caption + hashtags."

This is one of 50 prompts I compiled into a pack. Each one is tested and ready to use.

Full pack: $9.99 — Link in my profile

What prompts do you use for your business?"""
    },
]

# === TWEET THREADS ===
tweet_thread = """🧵 Thread: 5 AI prompts that transformed my business (save this)

1/ The Social Media Prompt:
"I am a [business owner]. Generate 7 days of content for [platform]. Include hooks, body, and CTAs. Tone: [professional/casual]."

2/ The Cold Email Prompt:
"Write a cold email to [customer] about [product]. Focus on [pain point]. Under 100 words. One CTA."

3/ The Sales Page Prompt:
"Create headline + 3 bullets for [product]. Audience: [who]. Benefit: [what]. Price: [$]."

4/ The Blog Post Prompt:
"Write a 1000-word blog post about [topic]. Target keyword: [keyword]. Include intro, 3 sections, and CTA."

5/ The Report Prompt:
"Create a [monthly/quarterly] report template for [department]. Include: metrics, insights, action items."

I compiled 50 prompts like these into a pack.

Link in bio 👆

Which one would you use first?"""

# === LINKEDIN POST ===
linkedin_post = """I just released something I've been working on for months:

50 AI Prompts for Business Owners

After testing hundreds of prompts, I found the 50 that actually work.

Here's what's inside:

📧 Marketing (10)
→ Social media, emails, SEO, ads, content calendars

💰 Sales (10)
→ Cold outreach, sales pages, objections, follow-ups

⚙️ Operations (10)
→ SOPs, meetings, training, reports, onboarding

📝 Content (10)
→ Blogs, videos, newsletters, case studies, decks

🎯 Strategy (10)
→ Planning, competitors, growth, pricing, personas

The result?
- Social posts: 5 min instead of 2 hours
- Cold emails: 3 min instead of 30 min
- Blog outlines: 2 min instead of 1 hour

Each prompt is tested across ChatGPT, Claude, and Gemini.

$9.99. Instant download. No subscription.

Link in comments 👇

#AI #Productivity #Business #Marketing"""

# Save everything
output = {
    "gumroad": gumroad,
    "reddit_posts": reddit_posts,
    "tweet_thread": tweet_thread,
    "linkedin_post": linkedin_post,
}

output_path = PRODUCT_DIR / "all_content.json"
output_path.write_text(json.dumps(output, indent=2))

print("Generated all copy-paste content:")
print(f"  - Gumroad listing content")
print(f"  - {len(reddit_posts)} Reddit posts")
print(f"  - Tweet thread (5 tweets)")
print(f"  - LinkedIn post")
print(f"\nSaved to: {output_path}")

# Also save individual files
(PRODUCT_DIR / "gumroad_description.txt").write_text(gumroad["long_description"])
(PRODUCT_DIR / "reddit_posts.md").write_text("\n\n---\n\n".join([
    f"## {p['subreddit']}\n\n**Title:** {p['title']}\n\n{p['body']}"
    for p in reddit_posts
]))
(PRODUCT_DIR / "tweet_thread.txt").write_text(tweet_thread)
(PRODUCT_DIR / "linkedin_post.txt").write_text(linkedin_post)

print("\nIndividual files saved:")
print("  - gumroad_description.txt")
print("  - reddit_posts.md")
print("  - tweet_thread.txt")
print("  - linkedin_post.txt")
