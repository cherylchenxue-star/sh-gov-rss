#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海市经信委政策法规抓取器
该页面存在字体反爬，需使用 GBK 解码原始响应体
"""

import subprocess
import re
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup

from sh_policy_rss.fetcher_base import BaseFetcher
from sh_policy_rss.models import PolicyItem, FetchResult
from sh_policy_rss.utils import parse_chinese_date, sanitize_text


class ShSheitcZcfgFetcher(BaseFetcher):
    """
    上海市经济和信息化委员会 - 政策法规
    URL: https://www.sheitc.sh.gov.cn/zcfg/
    """

    LIST_URL = "https://www.sheitc.sh.gov.cn/zcfg/"

    def __init__(self):
        super().__init__("上海市经信委", self.LIST_URL)

    def fetch(self, max_items: int = 20) -> FetchResult:
        try:
            html = self._fetch_with_gbk()
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

    def _fetch_with_gbk(self) -> str:
        """使用 curl 获取原始字节并用 UTF-8 解码（该站实际返回 UTF-8）"""
        cmd = ["curl", "-s", "-k", "-L", "--max-time", "20", "-A", "Mozilla/5.0", self.LIST_URL]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"curl failed")
        return result.stdout.decode("utf-8", errors="ignore")

    def _clean_pua(self, text: str) -> str:
        """清理字体反爬注入的 PUA 私用区字符，并压缩多余空白"""
        # 移除 Unicode 私用区字符 (U+E000 ~ U+F8FF) 和替换字符
        text = re.sub(r"[\ue000-\uf8ff\ufffd]", "", text)
        # 压缩连续空白和换行
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _parse_html(self, html: str, max_items: int) -> List[PolicyItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: List[PolicyItem] = []

        container = soup.find(id="zl2")
        if not container:
            container = soup

        for a in container.find_all("a", href=True):
            href = a.get("href", "").strip()
            # 过滤导航和无效链接
            if not href or "javascript" in href or "index" in href:
                continue
            if not (href.startswith("/sjxwxgwj/") or href.startswith("/sjxwxgzcjd/") or href.startswith("/sxwjql/")):
                continue

            text = a.get_text(strip=True)
            title = self._clean_pua(text)
            if len(title) < 5:
                continue

            # 从文本中提取日期
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
            date_str = date_match.group(1) if date_match else ""
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
                    source_id="sh-sheitc-zcfg",
                )
            )

            if len(items) >= max_items:
                break

        return items
