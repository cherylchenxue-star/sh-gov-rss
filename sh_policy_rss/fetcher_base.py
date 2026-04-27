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

    def _clean_gov_summary(self, text: str) -> str:
        """清理政府公文正文，去掉套话和无效信息，提取核心政策要点"""
        import re

        # 去掉多余的空白
        text = re.sub(r"\s+", " ", text.strip())

        # 1. 去掉开头常见的公文称谓（"各有关单位："、"各区...："等）
        salutation_patterns = [
            r"^.*?各有关.*?(单位|企业|部门|机构)：\s*",
            r"^.*?各区.*?(局|委|办|政府|单位)：\s*",
            r"^.*?各.*?(单位|部门|机构|公司|企业)：\s*",
            r"^.*?各有关单位，.*?(局|委|办)：\s*",
            r"^.*?国网.*?公司，.*?(企业|公司)：\s*",
        ]
        for pattern in salutation_patterns:
            text = re.sub(pattern, "", text, count=1)

        # 2. 去掉 "现将有关事项通知如下" 等过渡语句
        transition_patterns = [
            r"现将有关事项通知如下[：。]?\s*",
            r"现(将|就).*?通知如下[：。]?\s*",
            r"现就.*?(有关|相关)事项通知如下[：。]?\s*",
            r"决定.*?现将有关事项通知如下[：。]?\s*",
            r"现将有关事项(通知|公告|通告)如下[：。]?\s*",
            r"现将有关事项通知如下[：。]?\s*",
        ]
        for pattern in transition_patterns:
            text = re.sub(pattern, "", text, count=1)

        # 3. 去掉号召性语句（"请广大市民..."、"建议优先..."等）
        appeal_patterns = [
            r"请广大.*?合理安排.*?[。！]?\s*",
            r"建议优先通过.*?[。！]?\s*",
            r"请.*?(关注|留意|注意|了解).*?[。！]?\s*",
            r"欢迎.*?参与.*?[。！]?\s*",
        ]
        for pattern in appeal_patterns:
            text = re.sub(pattern, "", text)

        # 4. 去掉申请细节、联系方式等无效信息
        detail_patterns = [
            r"截止时间为[^。！]*[。！]\s*",
            r"受理时间为[^。！]*[。！]\s*",
            r"书面材料[^。！]*[。！]\s*",
            r"双面打印[^。！]*[。！]\s*",
            r"请填写[^。！]*[。！]\s*",
            r"申请人需[^。！]*[。！]\s*",
            r"提交[^。！]*申请材料[^。！]*[。！]\s*",
            r"发送[^。！]*电子版[^。！]*[。！]\s*",
        ]
        for pattern in detail_patterns:
            text = re.sub(pattern, "", text)

        # 4b. 去掉联系方式区块（含电话、邮箱、地址、联系人等）
        contact_patterns = [
            r"申报联系方式[：:]\s*.*?\d{4}年\d{1,2}月\d{1,2}日\s*",
            r"联系方式[：:]\s*.*?(?=【|$)",
            r"联系电话[：:]\s*\d[\d\-，,、]+\s*",
            r"联系地址[：:]\s*[^。！\n]*[。！]?\s*",
            r"电子邮箱[：:]\s*[^\s]*\s*",
            r"联系人[：:]\s*[^。！\n]*[。！]?\s*",
            r"通讯地址[：:]\s*[^。！\n]*[。！]?\s*",
            r"邮政编码[：:]\s*\d+\s*",
            r"传真[：:]\s*\d[\d\-]+\s*",
            r"电话[：:]\s*\d[\d\-]+\s*",
        ]
        for pattern in contact_patterns:
            text = re.sub(pattern, "", text)

        # 4c. 去掉附件相关
        text = re.sub(r"\d+\.\s*[^\s]+\.(pdf|doc|docx|xls|xlsx)\s*", "", text)
        text = re.sub(r"(附件下载|下载附件)[^。！]*[。！]?\s*", "", text)
        text = re.sub(r"【相关附件】.*", "", text)
        text = re.sub(r"附件[：:]\s*.*?\.(pdf|doc|docx|xls|xlsx)\s*", "", text)

        # 4d. 去掉推广渠道名称（"一网通办"、App名称等）
        text = re.sub(r"建议优先通过.*?[。！]\s*", "", text)
        text = re.sub(r"通过[\"'\"].*?[\"'\"].*?等渠道.*?[。！]\s*", "", text)
        text = re.sub(r"一网通办.*?[。！]\s*", "", text)
        text = re.sub(r"随申办.*?APP.*?[。！]\s*", "", text)

        # 4e. 去掉具体地址信息（含路名、号、楼层等）
        text = re.sub(r"[（(].*?路\d+号.*?[）)]\s*", "", text)
        text = re.sub(r"位于.*?[。！]\s*", "", text)
        text = re.sub(r"地址[：:]\s*[^。！]*[。！]?\s*", "", text)

        # 4f. 去掉服务时间详情
        text = re.sub(r"服务时间[：:]\s*[^。！]*[。！]\s*", "", text)
        text = re.sub(r"营业时间[：:]\s*[^。！]*[。！]\s*", "", text)
        text = re.sub(r"对外接待时间[：:]\s*[^。！]*[。！]\s*", "", text)
        text = re.sub(r"（最晚取号时间[^）]*）\s*", "", text)

        # 5. 去掉结尾套话（"特此通知"、"以上通知"等）
        closing_patterns = [
            r"特此通知[。！]?\s*",
            r"以上通知[。！]?\s*",
            r"特此(公告|通告|函告|函复)[。！]?\s*",
            r"以上(公告|通告)[。！]?\s*",
            r"此复[。！]?\s*",
            r"请.*?(遵照执行|认真执行|遵照办理|认真贯彻|贯彻执行)[。！]?\s*",
        ]
        for pattern in closing_patterns:
            text = re.sub(pattern + r"$", "", text)
            text = re.sub(pattern, "", text)

        # 6. 去掉落款信息（只在文本末尾匹配，避免误删正文中的单位名称）
        # 先去掉末尾的日期
        text = re.sub(r"\d{4}年\d{1,2}月\d{1,2}日\s*$", "", text)
        # 再去掉末尾的单位名称（单独一行或在末尾）
        signature_patterns = [
            r"(上海市科学技术委员会|上海市发展和改革委员会|上海市经济和信息化委员会|上海市人民政府办公厅)\s*$",
            r"(上海市|市)(科委|发改委|发展和改革委员会|经济和信息化委员会|人民政府办公厅|科学技术委员会)\s*$",
        ]
        for pattern in signature_patterns:
            text = re.sub(pattern, "", text)

        # 7. 去掉文号行（如"沪发改价管〔2019〕36号"）
        text = re.sub(r"[沪京粤浙苏].*?〔\d{4}〕\d+号\s*", "", text)
        # 去掉空括号（文号删除后留下的）
        text = re.sub(r"\s*（）\s*", "", text)

        # 8. 去掉价格表/数据表格
        # 检测1：带"元"的价格（如"0.6434元"）
        price_with_unit = re.findall(r"\d+\.\d+\s*元", text)
        # 检测2：表格中的价格数字（如"3.28"后面跟着中文或空格）
        price_numbers = re.findall(r"\d+\.\d+(?:\s+|$)", text)
        # 检测3：明确的价格表标记
        has_price_marker = any(marker in text for marker in ["见下表", "如下表", "价格表", "单位：元", "单价", "基准价格"])
        # 检测4：价格列表直接嵌在正文中（如"每千瓦时0.6434元"出现多次）
        price_in_text = re.findall(r"(?:每|为|至|按|增加|减少)[^。；]*\d+\.\d+\s*元", text)

        should_truncate = (
            len(price_with_unit) >= 3
            or (has_price_marker and len(price_numbers) >= 3)
            or len(price_in_text) >= 3
        )

        if should_truncate:
            # 尝试在表格提示词之前截断
            for marker in ["见下表", "如下表", "具体如下", "价格表", "单位：", "见附表", "附表"]:
                idx = text.find(marker)
                if idx > 30:
                    text = text[:idx]
                    break
            else:
                # 截断到第一个价格数字之前（保留前面的政策说明）
                # 匹配 "每千瓦时0.6434元"、"为0.15元"、"：3.28" 等
                m = re.search(r"([。；：]\s*)(?:\d+\.\s)?[^。；：]*?\d+\.\d+\s*元", text)
                if m:
                    text = text[:m.start() + 1]
                else:
                    # 兜底：截断到第一个编号列表项（如"1."、"（1）"）之前
                    list_start = re.search(r"[。；]\s*(?:\d+\.\s|（\d+）)", text)
                    if list_start and list_start.start() > 40:
                        text = text[:list_start.start() + 1]

        # 9. 去掉过多的数字列表（如 "1. xxx 2. xxx 3. xxx" 格式的详细列举）
        # 检测 "1."、"2."、"3." 等编号（注意排除年份如 "2026."）
        numbered_items = re.findall(r"(?:^|[。；])\s*[1-9]\d*\.[\d\D]*?(?=[1-9]\d*\.|$)", text)
        if len(numbered_items) >= 3:
            first_num = re.search(r"[1-9]\d*\.\s", text)
            if first_num and first_num.start() > 60:
                text = text[:first_num.start()]

        # 去掉多余的空白
        text = re.sub(r"\s+", " ", text.strip())

        return text

    def extract_summary(self, html: str, selectors: List[str]) -> str:
        """从HTML中提取正文摘要（清理公文套话后截断）"""
        from bs4 import BeautifulSoup
        from .utils import truncate_text, sanitize_text

        soup = BeautifulSoup(html, "html.parser")
        for sel in selectors:
            elem = soup.select_one(sel)
            if elem:
                raw_text = sanitize_text(elem.get_text(separator=" ", strip=True))
                cleaned = self._clean_gov_summary(raw_text)
                return truncate_text(cleaned, max_len=300)
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
