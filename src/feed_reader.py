import json
import os
import datetime
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from urllib.error import URLError

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDS_FILE = os.path.join(_PROJECT_ROOT, "feeds.json")


class FeedParser:
    """解析 RSS 2.0 和 Atom 1.0 格式的 Feed"""

    ATOM_NS = "{http://www.w3.org/2005/Atom}"

    @staticmethod
    def parse(xml_text: str) -> dict:
        """
        解析 XML 文本，返回 feed 信息和文章列表。
        返回格式:
        {
            "title": "Feed Title",
            "link": "https://...",
            "articles": [
                {"title": "...", "link": "...", "published": "...", "summary": "..."},
                ...
            ]
        }
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return {"title": "", "link": "", "articles": []}

        # 判断是 RSS 还是 Atom
        if root.tag == "rss" or root.find("channel") is not None:
            return FeedParser._parse_rss(root)
        elif root.tag == f"{FeedParser.ATOM_NS}feed" or root.tag == "feed":
            return FeedParser._parse_atom(root)
        else:
            return {"title": "", "link": "", "articles": []}

    @staticmethod
    def _parse_rss(root) -> dict:
        channel = root.find("channel")
        if channel is None:
            return {"title": "", "link": "", "articles": []}

        title = channel.findtext("title", "")
        link = channel.findtext("link", "")
        articles = []

        for item in channel.findall("item"):
            article = {
                "title": item.findtext("title", "No Title"),
                "link": item.findtext("link", ""),
                "published": item.findtext("pubDate", ""),
                "summary": item.findtext("description", ""),
            }
            articles.append(article)

        return {"title": title, "link": link, "articles": articles}

    @staticmethod
    def _parse_atom(root) -> dict:
        ns = FeedParser.ATOM_NS
        # 也尝试无命名空间
        title = root.findtext(f"{ns}title", "") or root.findtext("title", "")

        link_el = root.find(f"{ns}link[@rel='alternate']")
        if link_el is None:
            link_el = root.find(f"{ns}link")
        if link_el is None:
            link_el = root.find("link[@rel='alternate']")
        if link_el is None:
            link_el = root.find("link")
        link = link_el.get("href", "") if link_el is not None else ""

        articles = []
        for entry in root.findall(f"{ns}entry") or root.findall("entry"):
            a_title = entry.findtext(f"{ns}title", "") or entry.findtext(
                "title", "No Title"
            )

            a_link_el = entry.find(f"{ns}link[@rel='alternate']")
            if a_link_el is None:
                a_link_el = entry.find(f"{ns}link")
            if a_link_el is None:
                a_link_el = entry.find("link[@rel='alternate']")
            if a_link_el is None:
                a_link_el = entry.find("link")
            a_link = a_link_el.get("href", "") if a_link_el is not None else ""

            a_published = (
                entry.findtext(f"{ns}published", "")
                or entry.findtext(f"{ns}updated", "")
                or entry.findtext("published", "")
                or entry.findtext("updated", "")
            )

            a_summary = (
                entry.findtext(f"{ns}summary", "")
                or entry.findtext(f"{ns}content", "")
                or entry.findtext("summary", "")
                or entry.findtext("content", "")
            )

            articles.append(
                {
                    "title": a_title,
                    "link": a_link,
                    "published": a_published,
                    "summary": a_summary,
                }
            )

        return {"title": title, "link": link, "articles": articles}


class FeedManager:
    """管理 RSS/Atom 订阅源和文章状态，数据持久化到 feeds.json"""

    @staticmethod
    def load_feeds() -> list:
        """
        加载订阅源列表。
        格式: [
            {
                "url": "https://...",
                "title": "Feed Title",
                "link": "https://...",
                "articles": [...],
                "read_links": ["https://..."],
                "added_time": "2026-..."
            }, ...
        ]
        """
        if not os.path.exists(FEEDS_FILE):
            return []
        try:
            with open(FEEDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def save_feeds(feeds: list):
        """保存订阅源列表到文件"""
        try:
            with open(FEEDS_FILE, "w", encoding="utf-8") as f:
                json.dump(feeds, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print("Feeds save error:", e)

    @staticmethod
    def add_feed(url: str, title: str = "", link: str = "") -> list:
        """添加一个新的订阅源"""
        feeds = FeedManager.load_feeds()
        # 检查是否已存在
        for f in feeds:
            if f["url"] == url:
                return feeds  # 已存在，不重复添加
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        feeds.append(
            {
                "url": url,
                "title": title or url,
                "link": link,
                "articles": [],
                "read_links": [],
                "added_time": now,
            }
        )
        FeedManager.save_feeds(feeds)
        return feeds

    @staticmethod
    def remove_feed(url: str) -> list:
        """删除一个订阅源"""
        feeds = FeedManager.load_feeds()
        feeds = [f for f in feeds if f["url"] != url]
        FeedManager.save_feeds(feeds)
        return feeds

    @staticmethod
    def update_feed(url: str, parsed_data: dict) -> list:
        """用解析后的数据更新某个 feed 的文章列表和标题"""
        feeds = FeedManager.load_feeds()
        for f in feeds:
            if f["url"] == url:
                if parsed_data.get("title"):
                    f["title"] = parsed_data["title"]
                if parsed_data.get("link"):
                    f["link"] = parsed_data["link"]
                f["articles"] = parsed_data.get("articles", [])
                break
        FeedManager.save_feeds(feeds)
        return feeds

    @staticmethod
    def mark_article_read(feed_url: str, article_link: str) -> list:
        """标记某篇文章为已读"""
        feeds = FeedManager.load_feeds()
        for f in feeds:
            if f["url"] == feed_url:
                if article_link not in f.get("read_links", []):
                    f.setdefault("read_links", []).append(article_link)
                break
        FeedManager.save_feeds(feeds)
        return feeds

    @staticmethod
    def mark_all_read(feed_url: str) -> list:
        """标记某个 feed 的所有文章为已读"""
        feeds = FeedManager.load_feeds()
        for f in feeds:
            if f["url"] == feed_url:
                f["read_links"] = [
                    a["link"] for a in f.get("articles", []) if a.get("link")
                ]
                break
        FeedManager.save_feeds(feeds)
        return feeds

    @staticmethod
    def get_unread_count(feed: dict) -> int:
        """获取某个 feed 的未读文章数量"""
        read_links = set(feed.get("read_links", []))
        articles = feed.get("articles", [])
        return sum(1 for a in articles if a.get("link") and a["link"] not in read_links)

    @staticmethod
    def fetch_feed(url: str, timeout: int = 10) -> str:
        """从 URL 获取 feed XML 内容（同步方式，适合在线程中使用）"""
        headers = {"User-Agent": "NanoBrowser RSS Reader/1.0"}
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (URLError, OSError, UnicodeDecodeError) as e:
            print(f"Feed fetch error ({url}): {e}")
            return ""
