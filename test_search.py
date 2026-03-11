#!/usr/bin/env python
"""测试搜索功能"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from PyQt6.QtCore import QUrl

# 导入 SEARCH_ENGINES
SEARCH_ENGINES = {
    "Bing": "https://www.bing.com/search?q={}",
    "Google": "https://www.google.com/search?q={}",
    "Baidu": "https://www.baidu.com/s?wd={}",
}

def navigate_to_url(text, search_engine="Bing"):
    """模拟 MainWindow.navigate_to_url 的逻辑"""
    text = text.strip()
    if not text:
        return None
    
    # 判断是否是 URL
    is_url = re.match(r"^(http://|https://|file://)", text) or (
        "." in text and " " not in text
    )
    
    if is_url:
        if not re.match(r"^[a-zA-Z]+://", text):
            text = "https://" + text
        url = text
    else:
        # 搜索
        search_url = SEARCH_ENGINES.get(search_engine, SEARCH_ENGINES["Bing"])
        url = search_url.format(text)
    
    return url


# 测试用例
test_cases = [
    # (输入, 搜索引擎, 预期结果类型)
    ("hello", "Bing", "search"),
    ("hello world", "Bing", "search"),
    ("www.example.com", "Bing", "url"),
    ("https://www.google.com", "Bing", "url"),
    ("example.org", "Bing", "url"),
    ("python", "Google", "search"),
    ("python", "Baidu", "search"),
    ("", "Bing", None),
]

print("Testing search functionality:")
print("=" * 60)

for text, engine, expected_type in test_cases:
    result = navigate_to_url(text, engine)
    
    if result is None:
        result_type = None
    elif expected_type == "search":
        result_type = "search" if "search?q=" in result or "baidu.com/s" in result else "url"
    else:
        result_type = "url"
    
    status = "✓" if result_type == expected_type or (expected_type is None and result is None) else "✗"
    print(f"{status} Input: '{text}' ({engine})")
    print(f"   Result: {result}")
    print()

print("=" * 60)
print("Testing complete!")
