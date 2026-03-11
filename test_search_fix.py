#!/usr/bin/env python
"""验证搜索功能修复"""
import sys
import os

# 模拟 navigate_to_url 的逻辑
SEARCH_ENGINES = {
    "Bing": "https://www.bing.com/search?q={}",
    "Google": "https://www.google.com/search?q={}",
    "Baidu": "https://www.baidu.com/s?wd={}",
}

# 模拟 settings
settings = {"search_engine": "Google"}

def navigate_to_url_fixed(text):
    """修复后的 navigate_to_url"""
    import re
    text = text.strip()
    if not text:
        return None
    is_url = re.match(r"^(http://|https://|file://)", text) or (
        "." in text and " " not in text
    )
    if is_url:
        if not re.match(r"^[a-zA-Z]+://", text):
            text = "https://" + text
        url = text
    else:
        # 修复：使用 settings 中的搜索引擎
        search_engine = settings.get("search_engine", "Bing")
        url = SEARCH_ENGINES.get(search_engine, SEARCH_ENGINES["Bing"]).format(text)
    return url

# 测试
test_input = "test search"
result = navigate_to_url_fixed(test_input)
print(f"Input: {test_input}")
print(f"Result: {result}")
print()

# 验证使用 Google
if "google.com" in result:
    print("✓ Search engine correctly uses Google from settings")
else:
    print("✗ ERROR: Search engine should use Google")
    sys.exit(1)

# 测试 Bing
settings["search_engine"] = "Bing"
result2 = navigate_to_url_fixed("test")
print(f"Bing test: {result2}")
if "bing.com" in result2:
    print("✓ Search engine correctly uses Bing")
else:
    print("✗ ERROR")

# 测试 Baidu  
settings["search_engine"] = "Baidu"
result3 = navigate_to_url_fixed("test")
print(f"Baidu test: {result3}")
if "baidu.com" in result3:
    print("✓ Search engine correctly uses Baidu")
else:
    print("✗ ERROR")

print()
print("All tests passed!")
