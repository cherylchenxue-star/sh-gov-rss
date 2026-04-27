#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数：HTTP请求、日期解析、URL处理
"""

import subprocess
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List


def curl_fetch(url: str, timeout: int = 20, follow_redirects: bool = True) -> str:
    """使用curl获取URL内容（绕过Python SSL问题）"""
    cmd = [
        "curl", "-s", "-k", "--max-time", str(timeout), "--connect-timeout", "10",
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    if follow_redirects:
        cmd.append("-L")
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    # HTTPS 失败时降级到 HTTP
    if result.returncode != 0 and url.startswith("https://"):
        http_url = url.replace("https://", "http://", 1)
        cmd[-1] = http_url
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "unknown error")[:300]
        raise RuntimeError(f"curl failed ({result.returncode}): {err}")
    return result.stdout


def curl_fetch_json(url: str, timeout: int = 20) -> Dict[str, Any]:
    """使用curl获取JSON数据"""
    text = curl_fetch(url, timeout=timeout)
    return json.loads(text)


def parse_chinese_date(date_str: str) -> Optional[datetime]:
    """解析多种中文日期格式，支持带时间"""
    if not date_str:
        return None

    date_str = date_str.strip()

    # 优先匹配带时间的格式: 2026-04-24 02:04:17 或 2026-04-24T02:04:17
    # 支持全角冒号 ":" (U+FF1A) 和半角冒号 ":"
    time_match = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2})[:：∶](\d{2})[:：∶](\d{2})", date_str)
    if time_match:
        try:
            return datetime(
                int(time_match.group(1)), int(time_match.group(2)), int(time_match.group(3)),
                int(time_match.group(4)), int(time_match.group(5)), int(time_match.group(6)),
            )
        except ValueError:
            pass

    # 匹配 HH:MM 不带秒的情况（支持全角冒号）
    time_match2 = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2})[:：∶](\d{2})", date_str)
    if time_match2:
        try:
            return datetime(
                int(time_match2.group(1)), int(time_match2.group(2)), int(time_match2.group(3)),
                int(time_match2.group(4)), int(time_match2.group(5)),
            )
        except ValueError:
            pass

    patterns = [
        (r"(\d{4})-(\d{2})-(\d{2})", lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r"(\d{4})/(\d{2})/(\d{2})", lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r"(\d{4})年(\d{1,2})月(\d{1,2})日", lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r"(\d{4})\.(\d{2})\.(\d{2})", lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    ]

    for pattern, builder in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                return builder(match)
            except ValueError:
                continue
    return None


def build_absolute_url(base_url: str, href: str) -> str:
    """构建绝对URL"""
    from urllib.parse import urljoin
    return urljoin(base_url, href)


def sanitize_text(text: str) -> str:
    """清理文本中的多余空白"""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def truncate_text(text: str, max_len: int = 300) -> str:
    """截断文本到指定长度，保留完整句子"""
    if not text:
        return ""
    text = sanitize_text(text)
    if len(text) <= max_len:
        return text
    # 尝试在句号、问号、叹号后截断
    for punct in "。！？":
        idx = text.rfind(punct, 0, max_len)
        if idx > max_len * 0.5:
            return text[: idx + 1]
    return text[:max_len] + "…"


# 行业关键词映射，用于自动标签识别
INDUSTRY_KEYWORDS = {
    "生物医药": ["生物医药", "医疗器械", "药品", "疫苗", "医疗健康", "公共卫生", "医院", "医药"],
    "集成电路": ["集成电路", "半导体", "芯片", "晶圆", "EDA", "封测"],
    "人工智能": ["人工智能", "AI", "大模型", "算法", "智能算力", "机器学习", "深度学习"],
    "新能源汽车": ["新能源汽车", "电动汽车", "动力电池", "充电桩", "智能网联汽车", "氢燃料电池"],
    "汽车": ["汽车", "整车", "零部件", "车联网", "自动驾驶"],
    "航空航天": ["航空航天", "大飞机", "航空发动机", "航天器", "卫星"],
    "新材料": ["新材料", "先进材料", "复合材料", "化工材料", "高性能纤维", "稀土"],
    "新能源": ["新能源", "光伏", "风电", "太阳能", "储能", "氢能", "核能", "清洁能源"],
    "智能制造": ["智能制造", "工业互联网", "智能工厂", "数字化转型", "工业软件", "机器人", "高端装备", "制造业"],
    "数字经济": ["数字经济", "大数据", "云计算", "区块链", "元宇宙", "数据要素", "平台经济", "电子商务", "电商"],
    "金融科技": ["金融科技", "数字金融", "普惠金融", "绿色金融", "金融"],
    "节能环保": ["节能环保", "绿色低碳", "节能减排", "循环经济", "碳达峰", "碳中和", "双碳", "生态环境", "污染治理"],
    "房地产": ["房地产", "住房", "城市建设", "建筑", "物业管理", "老旧小区", "保障房"],
    "教育": ["教育", "学校", "幼儿园", "中小学", "高校", "职业教育", "产学研"],
    "农业": ["农业", "乡村振兴", "粮食安全", "种业", "农村", "农产品"],
    "商贸消费": ["商贸", "消费", "零售", "会展", "免税店", "首发经济", "夜间经济", "商圈"],
    "文化旅游": ["文化", "旅游", "文旅", "文创", "体育产业", "博物馆", "演艺"],
    "科技创新": ["科技创新", "科研机构", "实验室", "研发", "技术攻关", "科技成果转化", "高新技术企业"],
    "中小企业": ["中小企业", "民营经济", "专精特新", "小微企业", "孵化器", "众创空间"],
    "能源电力": ["电力", "电网", "煤电", "气电", "天然气", "成品油", "能源", "输配电"],
    "交通物流": ["交通", "物流", "航运", "港口", "机场", "轨道交通", "快递", "供应链"],
    "养老服务": ["养老", "老龄", "银发经济", "托育", "儿童友好"],
}


def extract_industry_tags(text: str) -> List[str]:
    """基于关键词匹配提取行业标签"""
    if not text:
        return []
    text_lower = text.lower()
    tags = []
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                tags.append(industry)
                break
    return tags
