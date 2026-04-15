#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海市科委政策文件抓取器
"""

from datetime import datetime
from typing import List

from bs4 import BeautifulSoup

from sh_policy_rss.fetcher_base import BaseFetcher
from sh_policy_rss.models import PolicyItem, FetchResult
from sh_policy_rss.utils import curl_fetch, parse_chinese_date, sanitize_text


class ShStcsmFetcher(BaseFetcher):
    """
    上海市科学技术委员会 - 政务公开
    URL: https://stcsm.sh.gov.cn/zwgk/
    """

    LIST_URL = "https://stcsm.sh.gov.cn/zwgk/"

    def __init__(self):
        super().__init__("上海市科委", self.LIST_URL)

    def fetch(self, max_items: int = 20) -> FetchResult:
        try:
            html = curl_fetch(self.LIST_URL, timeout=20)
            items = self._parse_html(html, max_items)
            selectors = [
                ".xxgk_content_nr",
                ".xwnr_content",
                ".content",
                ".article",
                "#content",
            ]
            self.enrich_items(items, selectors)
            return FetchResult(
                source_name=self.source_name,
                items=items,
                success=True,
                fetched_count=len(items),
            )
        except Exception as e:
            return FetchResult(
                source_name=self.source_name,
                success=False,
                error_message=str(e),
            )

    def _parse_html(self, html: str, max_items: int) -> List[PolicyItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: List[PolicyItem] = []

        # 最新公开区域
        container = soup.find("div", class_="m-zxgk")
        if not container:
            return items

        ul = container.find("ul", class_="common")
        if not ul:
            return items

        for li in ul.find_all("li"):
            a = li.find("a", class_="a-hvr", href=True)
            if not a:
                continue

            href = a.get("href", "").strip()
            title = sanitize_text(a.get("title", "")) or sanitize_text(a.get_text(strip=True))
            if not href or not title:
                continue

            # 提取日期
            date_span = li.find("span", class_="date")
            date_str = sanitize_text(date_span.get_text(strip=True)) if date_span else ""

            pub_date = parse_chinese_date(date_str)
            if pub_date is None:
                pub_date = datetime.now()

            link = self.build_absolute_url(href)

            items.append(
                PolicyItem(
                    title=title,
                    link=link,
                    pub_date=pub_date,
                    source=self.source_name,
                    source_id="sh-stcsm",
                )
            )

            if len(items) >= max_items:
                break

        return items
