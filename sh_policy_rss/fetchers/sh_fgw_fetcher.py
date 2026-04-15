#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海市发改委政策文件抓取器
"""

import re
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup

from sh_policy_rss.fetcher_base import BaseFetcher
from sh_policy_rss.models import PolicyItem, FetchResult
from sh_policy_rss.utils import curl_fetch, parse_chinese_date, sanitize_text


class ShFgwFetcher(BaseFetcher):
    """
    上海市发展和改革委员会 - 政策文件
    URL: https://fgw.sh.gov.cn/fgw_zcwjfl/index.html
    """

    LIST_URL = "https://fgw.sh.gov.cn/fgw_zcwjfl/index.html"

    def __init__(self):
        super().__init__("上海市发改委", self.LIST_URL)

    def fetch(self, max_items: int = 20) -> FetchResult:
        try:
            html = curl_fetch(self.LIST_URL, timeout=20)
            items = self._parse_html(html, max_items)
            selectors = [
                ".Article_content",
                ".trout-region-content",
                ".content_detail",
                ".detail",
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

        container = soup.find("ul", class_="zzwj-list")
        if not container:
            return items

        for li in container.find_all("li"):
            a = li.find("a", href=True)
            if not a:
                continue

            href = a.get("href", "").strip()
            title = sanitize_text(a.get("title", "")) or sanitize_text(a.get_text(strip=True))
            if not href or not title:
                continue

            # 提取发布日期
            date_str = ""
            p = li.find("p", class_="clearfix")
            if p:
                for span in p.find_all("span"):
                    text = span.get_text(strip=True)
                    if "发布日期" in text:
                        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
                        if date_match:
                            date_str = date_match.group(1)
                        break

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
                    source_id="sh-fgw",
                )
            )

            if len(items) >= max_items:
                break

        return items
