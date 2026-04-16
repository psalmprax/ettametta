import asyncio
import sys
import os
import traceback

sys.path.insert(0, "/app")

from playwright.async_api import async_playwright


async def test():
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        )
        page = await context.new_page()
        page.set_default_timeout(120000)

        base_url = "https://leonardo.ai"
        prompt = "cyberpunk city"

        print("Step 1: Navigate")
        await page.goto(f"{base_url}/platform/ai-video", timeout=30000)
        print("Page loaded:", await page.title())

        await asyncio.sleep(2)

        print("Step 2: Find prompt area")
        prompt_area = page.get_by_role("textbox")
        count = await prompt_area.count()
        print("Textbox count:", count)

        if count > 0:
            print("Step 3: Click and type")
            await prompt_area.first.click()
            await prompt_area.first.type(prompt, delay=50)
            print("Typed prompt")

        print("Step 4: Find generate button")
        generate_btn = page.get_by_role(
            "button", name=lambda x: "Generate" in x or "Create" in x
        )
        btn_count = await generate_btn.count()
        print("Button count:", btn_count)

        if btn_count > 0:
            print("Step 5: Click generate")
            await generate_btn.click()
            print("Clicked generate")

        print("Step 6: Wait for render")
        await page.wait_for_timeout(10000)

        print("Step 7: Find video")
        video_element = await page.query_selector("video")
        print("Video element:", video_element)

        if video_element:
            video_url = await video_element.get_attribute("src")
            print("Video URL:", video_url[:80] if video_url else "N/A")

        await browser.close()
        await playwright.stop()
        print("Done!")

    except Exception as e:
        print("Error:", str(e))
        traceback.print_exc()


asyncio.run(test())
