#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取器抽象基类
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from .models import PolicyItem, FetchResult


class BaseFetcher(ABC):
    """政策抓取器基类"""

    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url

    @abstractmethod
    def fetch(self, max_items: int = 20) -> FetchResult:
        """抓取政策列表"""
        pass

    def build_absolute_url(self, href: str) -> str:
        """构建绝对URL"""
        from urllib.parse import urljoin
        return urljoin(self.base_url, href)

    def extract_summary(self, html: str, selectors: List[str]) -> str:
        """从HTML中提取正文摘要"""
        from bs4 import BeautifulSoup
        from .utils import truncate_text, sanitize_text

        soup = BeautifulSoup(html, "html.parser")
        for sel in selectors:
            elem = soup.select_one(sel)
            if elem:
                text = sanitize_text(elem.get_text(separator=" ", strip=True))
                return truncate_text(text, max_len=300)
        return ""

    def fetch_summary(self, url: str, selectors: List[str], timeout: int = 8) -> str:
        """访问详情页并提取摘要"""
        from .utils import curl_fetch

        try:
            html = curl_fetch(url, timeout=timeout)
            return self.extract_summary(html, selectors)
        except Exception:
            return ""

    def extract_pub_date(self, html: str) -> Optional[datetime]:
        """从详情页 HTML 中提取准确的发布时间"""
        from bs4 import BeautifulSoup
        from .utils import parse_chinese_date

        soup = BeautifulSoup(html, "html.parser")

        # 1. 尝试 meta 标签（大小写不敏感）
        for meta in soup.find_all("meta"):
            meta_property = (meta.get("property") or "").lower()
            meta_name = (meta.get("name") or "").lower()
            if meta_property in {"article:published_time", "pubdate", "publishdate", "date"} or \
               meta_name in {"pubdate", "publishdate", "date"}:
                content = meta.get("content")
                if content:
                    dt = parse_chinese_date(content)
                    if dt:
                        return dt

        # 2. 尝试常见的发布时间选择器
        time_selectors = [
            "span.time",
            ".pub-time",
            ".publish-time",
            ".article-time",
            ".release-time",
            ".date",
            "span.pd",
            "span.time-source",
            "#pubTime",
            ".info-source span",
            ".article-info span",
            ".news-info span",
            ".meta span",
        ]
        for sel in time_selectors:
            elem = soup.select_one(sel)
            if elem:
                text = elem.get_text(strip=True)
                dt = parse_chinese_date(text)
                if dt:
                    return dt

        # 3. 尝试正则匹配 "发布时间：2026-04-24 09:30" 或 "2026-04-24"
        import re
        patterns = [
            r"发布时间[:：]\s*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)",
            r"发布日期[:：]\s*(\d{4}-\d{2}-\d{2})",
            r"(\d{4}年\d{1,2}月\d{1,2}日\s*\d{2}:\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, soup.get_text())
            if match:
                dt = parse_chinese_date(match.group(1))
                if dt:
                    return dt

        return None

    def enrich_items(self, items: List[PolicyItem], selectors: List[str]) -> None:
        """为每个条目获取详情页摘要并提取行业标签，同时补全准确时间戳"""
        from .utils import extract_industry_tags, curl_fetch

        for item in items:
            if item.link:
                try:
                    html = curl_fetch(item.link, timeout=6)
                    # 提取摘要
                    summary = self.extract_summary(html, selectors)
                    if summary:
                        item.summary = summary
                    # 补全准确时间戳（仅当当前时间戳是午夜 00:00:00 时）
                    if item.pub_date.hour == 0 and item.pub_date.minute == 0:
                        precise = self.extract_pub_date(html)
                        if precise:
                            item.pub_date = precise
                except Exception:
                    pass
            # 基于标题和摘要提取行业标签
            combined_text = f"{item.title} {item.summary}"
            item.tags = extract_industry_tags(combined_text)
            # 如果没有识别到行业标签，但标题中含有专项资金、申报等，可标记为"专项资金"
            if not item.tags and ("专项资金" in item.title or "资金项目" in item.title):
                item.tags.append("专项资金")
