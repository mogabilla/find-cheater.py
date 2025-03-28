import asyncio
import time
import json
import random
import re
import subprocess
from playwright.async_api import async_playwright

# 🟢 Tor Proxy Details (Each request gets a new IP)
TOR_PROXY = "socks5://127.0.0.1:9050"

# 🟢 Maximum parallel tabs allowed
MAX_CONCURRENT_TABS = 5

# 🟢 Read URLs from file
def load_post_links(file_path):
    post_links = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"https?://\S+", line)  # Extract only the URL
            if match:
                post_links.append(match.group())
    return post_links

async def auto_scroll(page):
    """Scroll to load all comments"""
    last_height = await page.evaluate("document.body.scrollHeight")
    retries = 0

    while retries < 80:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(random.uniform(2, 3))  # Random sleep to avoid detection

        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            retries += 1
        else:
            retries = 0  # Reset retry if new content loads
        last_height = new_height

async def fetch_post_data(page, post_url):
    """Extract data from a post with retries"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🔵 Fetching: {post_url} (Attempt {attempt + 1})...")
            await page.goto(post_url, timeout=60000)
            await auto_scroll(page)  # Ensure all comments are loaded

            # **1️⃣ Post Author Username**
            author_element = await page.query_selector(".fullname-and-username .username")
            author_username = await author_element.inner_text() if author_element else "Unknown"

            # **2️⃣ Extract Commenters' Usernames**
            commenters = set()
            comment_elements = await page.query_selector_all(".tweet-body .username")
            for el in comment_elements:
                username = await el.inner_text()
                if username:
                    commenters.add(username.strip())

            # **3️⃣ Total Comments Count (Fetched)**
            fetched_comment_count = len(commenters)

            # **📌 Extracted Data**
            post_data = {
                "url": post_url,
                "author": author_username,
                "total_comments": fetched_comment_count,
                "commenters": list(commenters),
            }

            if fetched_comment_count > 0:
                print(f"✅ Done: {post_url} | Author: {author_username} | Comments: {fetched_comment_count}")
                return post_data
            else:
                print(f"⚠️ No comments found on {post_url}. Retrying...")
                await page.reload(wait_until="load")  # Refresh the page and retry

        except Exception as e:
            print(f"❌ Error in {post_url}: {e}")
    
    print(f"❌ Failed to fetch comments after {max_retries} attempts: {post_url}")
    return None

async def scrape_all_posts(post_links):
    """Scrape multiple posts in parallel"""
    start_time = time.time()
    collected_posts = []

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, proxy={"server": TOR_PROXY}, args=["--start-maximized"])

        # ✅ Tabs limit should be either the number of links OR the max limit
        actual_tabs = min(len(post_links), MAX_CONCURRENT_TABS)

        semaphore = asyncio.Semaphore(actual_tabs)

        async def process_url(url):
            async with semaphore:
                page = await browser.new_page()
                data = await fetch_post_data(page, url)
                if data:
                    collected_posts.append(data)
                await page.close()

        tasks = [process_url(url) for url in post_links]
        await asyncio.gather(*tasks)

        await browser.close()

    # 🟢 Save collected data to JSON
    with open("collected_posts.json", "w", encoding="utf-8") as f:
        json.dump(collected_posts, f, ensure_ascii=False, indent=2)

    # **📌 Execution Time**
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)

    print("\n📊 Summary:")
    print(f"✅ Total Posts Scraped: {len(collected_posts)}")
    print(f"⏳ Execution Time: {elapsed_time} seconds")
    print("📂 Data saved in collected_posts.json")

# **🔥 Run Script**
post_links = load_post_links("post_links.txt")  # Load URLs from file

if not post_links:
    print("❌ No URLs found in post_links.txt. Exiting...")
else:
    asyncio.run(scrape_all_posts(post_links))

    # **🚀 Run engagement.py after scraping completes**
    print("\n🚀 Running engagement analysis...")
    subprocess.run(["python", "engement.py"])  # Runs engagement.py
