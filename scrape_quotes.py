import asyncio
import logging
import random
import sys
from datetime import date
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

BASE_URL = "https://quotes.toscrape.com"
START_PATH = "/js"
USER_AGENT = "QuoteScraper/1.0 (educational use)"


def load_robots(base_url: str) -> RobotFileParser:
    rp = RobotFileParser()
    robots_url = urljoin(base_url, "/robots.txt")
    rp.set_url(robots_url)
    try:
        resp = requests.get(robots_url, timeout=10)
        if resp.status_code == 404:
            # robots.txt が存在しない場合はすべて許可
            rp.parse([])
            logger.info("robots.txt が存在しません（すべてのパスを許可）")
        else:
            resp.raise_for_status()
            rp.parse(resp.text.splitlines())
            logger.info("robots.txt を読み込みました")
    except requests.RequestException as e:
        rp.parse([])
        logger.warning(f"robots.txt の読み込みに失敗しました（続行します）: {e}")
    return rp


def save_markdown(quotes: list[dict], filepath: str, screenshot_path: str) -> None:
    today = date.today().strftime("%Y-%m-%d")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Quotes Scraping Results\n\n")
        f.write(f"- 収集日: {today}\n")
        f.write(f"- 収集元: {BASE_URL}{START_PATH}\n")
        f.write(f"- 合計: {len(quotes)} 件\n")
        f.write(f"- スクリーンショット: [{screenshot_path}]({screenshot_path})\n\n")
        f.write("| # | 名言 | 著者 |\n")
        f.write("|---|---|---|\n")
        for i, q in enumerate(quotes, 1):
            text = q["text"].replace("|", "\\|")
            author = q["author"].replace("|", "\\|")
            f.write(f"| {i} | {text} | {author} |\n")


async def main() -> None:
    logger.info("スクレイピングを開始します")

    rp = load_robots(BASE_URL)
    start_url = BASE_URL + START_PATH

    if not rp.can_fetch(USER_AGENT, start_url):
        logger.error(f"robots.txt によりアクセスが禁止されています: {start_url}")
        sys.exit(1)

    today = date.today().strftime("%Y-%m-%d")
    screenshot_path = f"quotes_{today}.png"
    markdown_path = f"quotes_{today}.md"
    all_quotes: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()

        current_url: str | None = start_url
        page_num = 1
        first_page = True

        while current_url:
            if not rp.can_fetch(USER_AGENT, current_url):
                logger.warning(f"robots.txt によりアクセスが禁止されています: {current_url}")
                break

            logger.info(f"ページ {page_num} を取得中: {current_url}")

            try:
                await page.goto(current_url, timeout=30000)
                await page.wait_for_selector(".quote", timeout=15000)
            except PlaywrightTimeoutError as e:
                logger.error(f"ページ読み込みタイムアウト: {e}")
                await browser.close()
                sys.exit(1)
            except Exception as e:
                logger.error(f"接続エラー: {e}")
                await browser.close()
                sys.exit(1)

            # 最初のページのみスクリーンショットを撮影
            if first_page:
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"スクリーンショットを保存しました: {screenshot_path}")
                first_page = False

            # 名言を取得
            quote_elements = await page.query_selector_all(".quote")
            page_quotes: list[dict] = []
            for elem in quote_elements:
                text_elem = await elem.query_selector(".text")
                author_elem = await elem.query_selector(".author")
                text = (await text_elem.inner_text()).strip() if text_elem else ""
                author = (await author_elem.inner_text()).strip() if author_elem else ""
                page_quotes.append({"text": text, "author": author})

            all_quotes.extend(page_quotes)
            logger.info(f"  → {len(page_quotes)} 件取得（累計: {len(all_quotes)} 件）")

            # 次ページの確認
            next_btn = await page.query_selector("li.next > a")
            if next_btn:
                next_href = await next_btn.get_attribute("href")
                current_url = urljoin(BASE_URL, next_href)
                page_num += 1
                wait = random.uniform(1, 3)
                logger.info(f"  {wait:.1f} 秒待機中...")
                await asyncio.sleep(wait)
            else:
                current_url = None

        await browser.close()

    save_markdown(all_quotes, markdown_path, screenshot_path)
    logger.info(f"完了: {len(all_quotes)} 件の名言を {markdown_path} に保存しました")


if __name__ == "__main__":
    asyncio.run(main())
