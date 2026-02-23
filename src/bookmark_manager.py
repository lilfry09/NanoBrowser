import json
import os

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKMARKS_FILE = os.path.join(_PROJECT_ROOT, "bookmarks.json")

class BookmarkManager:
    @staticmethod
    def load_bookmarks():
        if not os.path.exists(BOOKMARKS_FILE):
            return []
        try:
            with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def add_bookmark(url, title):
        bookmarks = BookmarkManager.load_bookmarks()
        
        # 检查是否已存在
        for bm in bookmarks:
            if bm["url"] == url:
                return False
                
        bookmarks.append({"url": url, "title": title})
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(bookmarks, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print("Bookmark save error:", e)
            return False

    @staticmethod
    def remove_bookmark(url):
        """删除指定 URL 的书签"""
        bookmarks = BookmarkManager.load_bookmarks()
        bookmarks = [bm for bm in bookmarks if bm["url"] != url]
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(bookmarks, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print("Bookmark remove error:", e)
            return False
