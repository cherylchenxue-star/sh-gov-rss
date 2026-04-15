#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海市经信委专项资金通知公告抓取器
"""

from datetime import datetime
from typing import List

from bs4 import BeautifulSoup

from sh_policy_rss.fetcher_base import BaseFetcher
from sh_policy_rss.models import PolicyItem, FetchResult
from sh_policy_rss.utils import curl_fetch, parse_chinese_date, sanitize_text


class ShSheitcZxzjFetcher(BaseFetcher):
    """
    上海市经济和信息化委员会 - 专项资金项目管理与服务平台通知公告
    URL: https://www.sheitc.sh.gov.cn/zxzjtzgg/index.html
    """

    LIST_URL = "https://www.sheitc.sh.gov.cn/zxzjtzgg/index.html"

    def __init__(self):
        super().__init__("上海市经信委专项资金", self.LIST_URL)

    def fetch(self, max_items: int = 20) -> FetchResult:
        try:
            html = curl_fetch(self.LIST_URL, timeout=20)
            items = self._parse_html(html, max_items)
            selectors = [
                ".text-main",
                ".view-main",
                ".TRS_Editor",
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

        container = soup.find("ul", class_="j-list-ul")
        if not container:
            return items

        for li in container.find_all("li"):
            a = li.find("a", href=True)
            if not a:
                continue

            href = a.get("href", "").strip()
            if not href:
                continue

            # 提取标题
            h2 = a.find("h2")
            title = sanitize_text(h2.get_text(strip=True)) if h2 else sanitize_text(a.get_text(strip=True))

            # 提取日期
            date_str = ""
            span = a.find("span")
            if span:
                date_str = sanitize_text(span.get_text(strip=True))

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
                    source_id="sh-sheitc-zxzj",
                )
            )

            if len(items) >= max_items:
                break

        return items
