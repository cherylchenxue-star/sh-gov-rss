#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class PolicyItem:
    """政策条目"""
    title: str
    link: str
    pub_date: datetime
    source: str
    source_id: str
    city: str = "shanghai"
    summary: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class FetchResult:
    """抓取结果"""
    source_name: str
    items: List[PolicyItem] = field(default_factory=list)
    success: bool = False
    error_message: str = ""
    fetched_count: int = 0
