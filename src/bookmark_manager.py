import json
import os

BOOKMARKS_FILE = "bookmarks.json"

class BookmarkManager:
    @staticmethod
    def load_bookmarks():
        if not os.path.exists(BOOKMARKS_FILE):
            return []
        try:
            with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
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
        except Exception as e:
            print("Bookmark save error:", e)
            return False
