import logging
import random
import sys
import time
from datetime import date
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com/"
TARGET_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
USER_AGENT = "BookDetailScraper/1.0 (educational use)"


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


def parse_book(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1").text.strip()
    price = soup.select_one("p.price_color").text.strip()
    availability = soup.select_one("p.availability").text.strip()
    return {"title": title, "price": price, "availability": availability}


def save_markdown(book: dict, filepath: str) -> None:
    today = date.today().strftime("%Y-%m-%d")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Book Detail Scraping Results\n\n")
        f.write(f"- 収集日: {today}\n")
        f.write(f"- 収集元: {TARGET_URL}\n\n")
        f.write("| タイトル | 価格 | 在庫状況 |\n")
        f.write("|---|---|---|\n")
        title = book["title"].replace("|", "\\|")
        price = book["price"].replace("|", "\\|")
        avail = book["availability"].replace("|", "\\|")
        f.write(f"| {title} | {price} | {avail} |\n")


def main() -> None:
    logger.info("スクレイピングを開始します")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    rp = load_robots(BASE_URL)

    if not rp.can_fetch(USER_AGENT, TARGET_URL):
        logger.error(f"robots.txt によりアクセスが禁止されています: {TARGET_URL}")
        sys.exit(1)

    logger.info(f"取得中: {TARGET_URL}")
    html = fetch(session, TARGET_URL)

    # リクエスト間の待機（複数リクエストを行う場合の作法として実施）
    wait = random.uniform(1, 3)
    logger.info(f"{wait:.1f} 秒待機中...")
    time.sleep(wait)

    book = parse_book(html)
    logger.info(f"取得完了: {book['title']}")

    today = date.today().strftime("%Y-%m-%d")
    output_path = f"books_{today}.md"
    save_markdown(book, output_path)
    logger.info(f"完了: 書籍情報を {output_path} に保存しました")


if __name__ == "__main__":
    main()
