import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import sys
from datetime import date
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com/"
USER_AGENT = "BookScraper/1.0 (educational use)"


def load_robots(base_url: str) -> RobotFileParser:
    rp = RobotFileParser()
    rp.set_url(urljoin(base_url, "/robots.txt"))
    try:
        rp.read()
        logger.info("robots.txt を読み込みました")
    except Exception as e:
        logger.warning(f"robots.txt の読み込みに失敗しました（続行します）: {e}")
    return rp


def fetch(session: requests.Session, url: str) -> str:
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.ConnectionError as e:
        logger.error(f"接続エラー: {e}")
        sys.exit(1)
    except requests.Timeout as e:
        logger.error(f"タイムアウト: {e}")
        sys.exit(1)
    except requests.HTTPError as e:
        logger.error(f"HTTPエラー: {e}")
        sys.exit(1)


def parse_books(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for article in soup.select("article.product_pod"):
        title = article.h3.a["title"]
        price = article.select_one("p.price_color").text.strip()
        availability = article.select_one("p.availability").text.strip()
        books.append({"title": title, "price": price, "availability": availability})
    return books


def next_page_url(html: str, current_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    next_btn = soup.select_one("li.next > a")
    if next_btn:
        return urljoin(current_url, next_btn["href"])
    return None


def save_markdown(books: list[dict], filepath: str) -> None:
    today = date.today().strftime("%Y-%m-%d")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Books Scraping Results\n\n")
        f.write(f"- 収集日: {today}\n")
        f.write(f"- 収集元: {BASE_URL}\n")
        f.write(f"- 合計: {len(books)} 冊\n\n")
        f.write("| タイトル | 価格 | 在庫状況 |\n")
        f.write("|---|---|---|\n")
        for book in books:
            title = book["title"].replace("|", "\\|")
            price = book["price"].replace("|", "\\|")
            avail = book["availability"].replace("|", "\\|")
            f.write(f"| {title} | {price} | {avail} |\n")


def main() -> None:
    logger.info("スクレイピングを開始します")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    rp = load_robots(BASE_URL)

    all_books: list[dict] = []
    url: str | None = BASE_URL
    page = 1

    while url:
        if not rp.can_fetch(USER_AGENT, url):
            logger.warning(f"robots.txt によりアクセス禁止のためスキップ: {url}")
            break

        logger.info(f"ページ {page} を取得中: {url}")
        html = fetch(session, url)

        books = parse_books(html)
        all_books.extend(books)
        logger.info(f"  → {len(books)} 冊取得（累計: {len(all_books)} 冊）")

        url = next_page_url(html, url)
        page += 1

        if url:
            wait = random.uniform(1, 3)
            logger.info(f"  {wait:.1f} 秒待機中...")
            time.sleep(wait)

    today = date.today().strftime("%Y-%m-%d")
    output_path = f"books_{today}.md"
    save_markdown(all_books, output_path)
    logger.info(f"完了: {len(all_books)} 冊の情報を {output_path} に保存しました")


if __name__ == "__main__":
    main()
