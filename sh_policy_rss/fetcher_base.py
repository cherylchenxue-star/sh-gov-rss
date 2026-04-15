#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取器抽象基类
"""

from abc import ABC, abstractmethod
from typing import List
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

    def enrich_items(self, items: List[PolicyItem], selectors: List[str]) -> None:
        """为每个条目获取详情页摘要并提取行业标签"""
        from .utils import extract_industry_tags

        for item in items:
            if item.link:
                summary = self.fetch_summary(item.link, selectors, timeout=6)
                if summary:
                    item.summary = summary
            # 基于标题和摘要提取行业标签
            combined_text = f"{item.title} {item.summary}"
            item.tags = extract_industry_tags(combined_text)
            # 如果没有识别到行业标签，但标题中含有专项资金、申报等，可标记为"专项资金"
            if not item.tags and ("专项资金" in item.title or "资金项目" in item.title):
                item.tags.append("专项资金")
