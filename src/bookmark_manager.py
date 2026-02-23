import json
import os
import time
import html as html_module
import re

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKMARKS_FILE = os.path.join(_PROJECT_ROOT, "bookmarks.json")


class BookmarkManager:
    """
    书签管理器 - 支持文件夹、排序、导入导出。

    数据结构 (bookmarks.json):
    [
        {"type": "bookmark", "url": "...", "title": "...", "added": "..."},
        {"type": "folder", "name": "Work", "children": [
            {"type": "bookmark", "url": "...", "title": "...", "added": "..."},
            ...
        ]},
        ...
    ]

    为向后兼容，旧格式 [{"url": "...", "title": "..."}] 在加载时自动迁移。
    """

    @staticmethod
    def load_bookmarks():
        """加载书签数据，返回列表"""
        if not os.path.exists(BOOKMARKS_FILE):
            return []
        try:
            with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 自动迁移旧格式
            data = BookmarkManager._migrate(data)
            return data
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def save_bookmarks(bookmarks):
        """保存书签数据"""
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(bookmarks, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print("Bookmark save error:", e)
            return False

    @staticmethod
    def _migrate(data):
        """将旧格式 [{"url":..., "title":...}] 迁移为新格式"""
        if not data:
            return data
        migrated = False
        result = []
        for item in data:
            if "type" not in item:
                # 旧格式条目
                result.append(
                    {
                        "type": "bookmark",
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "added": item.get("added", ""),
                    }
                )
                migrated = True
            else:
                result.append(item)
        if migrated:
            BookmarkManager.save_bookmarks(result)
        return result

    @staticmethod
    def add_bookmark(url, title, folder_name=None):
        """
        添加书签。如果 folder_name 指定，则添加到对应文件夹中。
        返回 True 表示添加成功，False 表示已存在或失败。
        """
        bookmarks = BookmarkManager.load_bookmarks()

        new_item = {
            "type": "bookmark",
            "url": url,
            "title": title,
            "added": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 检查是否已存在（递归搜索）
        if BookmarkManager._find_bookmark(bookmarks, url):
            return False

        if folder_name:
            # 在指定文件夹中添加
            folder = BookmarkManager._find_folder(bookmarks, folder_name)
            if folder:
                folder["children"].append(new_item)
            else:
                # 文件夹不存在，创建一个
                bookmarks.append(
                    {
                        "type": "folder",
                        "name": folder_name,
                        "children": [new_item],
                    }
                )
        else:
            bookmarks.append(new_item)

        return BookmarkManager.save_bookmarks(bookmarks)

    @staticmethod
    def remove_bookmark(url):
        """删除指定 URL 的书签（递归搜索所有文件夹）"""
        bookmarks = BookmarkManager.load_bookmarks()
        modified = BookmarkManager._remove_from_list(bookmarks, url)
        if modified:
            return BookmarkManager.save_bookmarks(bookmarks)
        return False

    @staticmethod
    def add_folder(name, parent_folder_name=None):
        """添加一个文件夹"""
        bookmarks = BookmarkManager.load_bookmarks()

        # 检查同名文件夹是否已存在
        if BookmarkManager._find_folder(bookmarks, name):
            return False

        new_folder = {
            "type": "folder",
            "name": name,
            "children": [],
        }

        if parent_folder_name:
            parent = BookmarkManager._find_folder(bookmarks, parent_folder_name)
            if parent:
                parent["children"].append(new_folder)
            else:
                bookmarks.append(new_folder)
        else:
            bookmarks.append(new_folder)

        return BookmarkManager.save_bookmarks(bookmarks)

    @staticmethod
    def remove_folder(name):
        """删除指定名称的文件夹"""
        bookmarks = BookmarkManager.load_bookmarks()
        modified = BookmarkManager._remove_folder_from_list(bookmarks, name)
        if modified:
            return BookmarkManager.save_bookmarks(bookmarks)
        return False

    @staticmethod
    def rename_folder(old_name, new_name):
        """重命名文件夹"""
        bookmarks = BookmarkManager.load_bookmarks()
        folder = BookmarkManager._find_folder(bookmarks, old_name)
        if folder:
            folder["name"] = new_name
            return BookmarkManager.save_bookmarks(bookmarks)
        return False

    @staticmethod
    def edit_bookmark(old_url, new_url, new_title):
        """编辑书签的 URL 和标题"""
        bookmarks = BookmarkManager.load_bookmarks()
        item = BookmarkManager._find_bookmark(bookmarks, old_url)
        if item:
            item["url"] = new_url
            item["title"] = new_title
            return BookmarkManager.save_bookmarks(bookmarks)
        return False

    @staticmethod
    def move_bookmark(url, target_folder_name=None):
        """
        将书签移动到指定文件夹 (target_folder_name=None 表示移到根目录)。
        """
        bookmarks = BookmarkManager.load_bookmarks()
        # 先找到并移除
        item = BookmarkManager._find_bookmark(bookmarks, url)
        if not item:
            return False
        BookmarkManager._remove_from_list(bookmarks, url)

        if target_folder_name:
            folder = BookmarkManager._find_folder(bookmarks, target_folder_name)
            if folder:
                folder["children"].append(item)
            else:
                bookmarks.append(item)
        else:
            bookmarks.append(item)

        return BookmarkManager.save_bookmarks(bookmarks)

    @staticmethod
    def get_folder_names(bookmarks=None):
        """获取所有文件夹名称列表"""
        if bookmarks is None:
            bookmarks = BookmarkManager.load_bookmarks()
        names = []
        for item in bookmarks:
            if item.get("type") == "folder":
                names.append(item["name"])
                # 递归获取子文件夹
                names.extend(BookmarkManager.get_folder_names(item.get("children", [])))
        return names

    @staticmethod
    def get_all_bookmarks_flat(bookmarks=None):
        """获取所有书签的扁平列表 (不含文件夹结构)"""
        if bookmarks is None:
            bookmarks = BookmarkManager.load_bookmarks()
        result = []
        for item in bookmarks:
            if item.get("type") == "bookmark":
                result.append(item)
            elif item.get("type") == "folder":
                result.extend(
                    BookmarkManager.get_all_bookmarks_flat(item.get("children", []))
                )
        return result

    # ---- HTML 导出 (兼容主流浏览器格式) ----

    @staticmethod
    def export_to_html(filepath):
        """
        将书签导出为 Netscape Bookmark File Format (HTML)。
        该格式兼容 Chrome, Firefox, Edge 等主流浏览器的导入功能。
        """
        bookmarks = BookmarkManager.load_bookmarks()

        lines = [
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
            "<!-- This is an automatically generated file. -->",
            "<!--     It will be read and overwritten. -->",
            "<!--     DO NOT EDIT! -->",
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            "<TITLE>Bookmarks</TITLE>",
            "<H1>Bookmarks</H1>",
            "<DL><p>",
        ]

        BookmarkManager._export_items(bookmarks, lines, indent=1)

        lines.append("</DL><p>")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except IOError as e:
            print("Export error:", e)
            return False

    @staticmethod
    def _export_items(items, lines, indent=1):
        """递归导出书签项"""
        prefix = "    " * indent
        for item in items:
            if item.get("type") == "folder":
                lines.append(f"{prefix}<DT><H3>{html_module.escape(item['name'])}</H3>")
                lines.append(f"{prefix}<DL><p>")
                BookmarkManager._export_items(
                    item.get("children", []), lines, indent + 1
                )
                lines.append(f"{prefix}</DL><p>")
            elif item.get("type") == "bookmark":
                url = html_module.escape(item.get("url", ""))
                title = html_module.escape(item.get("title", ""))
                lines.append(f'{prefix}<DT><A HREF="{url}">{title}</A>')

    # ---- HTML 导入 ----

    @staticmethod
    def import_from_html(filepath):
        """
        从 Netscape Bookmark File Format (HTML) 导入书签。
        兼容 Chrome, Firefox, Edge 等导出的书签文件。
        返回导入的书签数量。
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            print("Import error:", e)
            return 0

        imported_items = BookmarkManager._parse_bookmark_html(content)
        if not imported_items:
            return 0

        # 合并到现有书签
        bookmarks = BookmarkManager.load_bookmarks()
        count = BookmarkManager._merge_imported(bookmarks, imported_items)
        BookmarkManager.save_bookmarks(bookmarks)
        return count

    @staticmethod
    def _parse_bookmark_html(content):
        """解析 Netscape Bookmark HTML 格式"""
        items = []
        stack = [items]  # 栈结构追踪当前层级

        # 逐行解析
        for line in content.split("\n"):
            stripped = line.strip()

            # 匹配文件夹标题 <DT><H3...>FolderName</H3>
            folder_match = re.search(
                r"<DT><H3[^>]*>(.*?)</H3>", stripped, re.IGNORECASE
            )
            if folder_match:
                folder_name = html_module.unescape(folder_match.group(1))
                folder = {
                    "type": "folder",
                    "name": folder_name,
                    "children": [],
                }
                stack[-1].append(folder)
                stack.append(folder["children"])
                continue

            # 匹配书签链接 <DT><A HREF="...">Title</A>
            link_match = re.search(
                r'<DT><A\s+HREF="([^"]*)"[^>]*>(.*?)</A>', stripped, re.IGNORECASE
            )
            if link_match:
                url = html_module.unescape(link_match.group(1))
                title = html_module.unescape(link_match.group(2))
                stack[-1].append(
                    {
                        "type": "bookmark",
                        "url": url,
                        "title": title,
                        "added": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
                continue

            # 匹配 </DL> - 退出当前层级
            if re.search(r"</DL>", stripped, re.IGNORECASE):
                if len(stack) > 1:
                    stack.pop()

        return items

    @staticmethod
    def _merge_imported(existing, imported):
        """将导入的书签合并到已有书签列表中，跳过重复的 URL"""
        count = 0
        existing_urls = set()
        BookmarkManager._collect_urls(existing, existing_urls)

        for item in imported:
            if item.get("type") == "bookmark":
                if item["url"] not in existing_urls:
                    existing.append(item)
                    existing_urls.add(item["url"])
                    count += 1
            elif item.get("type") == "folder":
                # 查找同名文件夹
                target_folder = BookmarkManager._find_folder(existing, item["name"])
                if target_folder:
                    count += BookmarkManager._merge_imported(
                        target_folder["children"], item.get("children", [])
                    )
                else:
                    # 创建新文件夹，递归处理子项
                    new_folder = {
                        "type": "folder",
                        "name": item["name"],
                        "children": [],
                    }
                    sub_count = BookmarkManager._merge_imported(
                        new_folder["children"], item.get("children", [])
                    )
                    existing.append(new_folder)
                    count += sub_count

        return count

    @staticmethod
    def _collect_urls(items, url_set):
        """递归收集所有已有书签 URL"""
        for item in items:
            if item.get("type") == "bookmark":
                url_set.add(item.get("url", ""))
            elif item.get("type") == "folder":
                BookmarkManager._collect_urls(item.get("children", []), url_set)

    # ---- 内部辅助方法 ----

    @staticmethod
    def _find_bookmark(items, url):
        """递归查找指定 URL 的书签条目并返回引用"""
        for item in items:
            if item.get("type") == "bookmark" and item.get("url") == url:
                return item
            elif item.get("type") == "folder":
                found = BookmarkManager._find_bookmark(item.get("children", []), url)
                if found:
                    return found
        return None

    @staticmethod
    def _find_folder(items, name):
        """递归查找指定名称的文件夹并返回引用"""
        for item in items:
            if item.get("type") == "folder" and item.get("name") == name:
                return item
            elif item.get("type") == "folder":
                found = BookmarkManager._find_folder(item.get("children", []), name)
                if found:
                    return found
        return None

    @staticmethod
    def _remove_from_list(items, url):
        """递归从列表中移除指定 URL 的书签，返回是否成功"""
        for i, item in enumerate(items):
            if item.get("type") == "bookmark" and item.get("url") == url:
                items.pop(i)
                return True
            elif item.get("type") == "folder":
                if BookmarkManager._remove_from_list(item.get("children", []), url):
                    return True
        return False

    @staticmethod
    def _remove_folder_from_list(items, name):
        """递归从列表中移除指定名称的文件夹，返回是否成功"""
        for i, item in enumerate(items):
            if item.get("type") == "folder" and item.get("name") == name:
                items.pop(i)
                return True
            elif item.get("type") == "folder":
                if BookmarkManager._remove_folder_from_list(
                    item.get("children", []), name
                ):
                    return True
        return False
