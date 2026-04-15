#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海政策RSS聚合器 - 主入口

抓取上海市多个政府部门的政策通知页面，
聚合输出为统一的 RSS 2.0 XML 文件和交互式 HTML 预览页。
"""

import sys
import argparse
from typing import List

from sh_policy_rss.models import FetchResult, PolicyItem
from sh_policy_rss.build_rss import build_rss
from sh_policy_rss.build_index import build_index
from sh_policy_rss.fetchers.sh_sheitc_zcfg_fetcher import ShSheitcZcfgFetcher
from sh_policy_rss.fetchers.sh_sheitc_zxzj_fetcher import ShSheitcZxzjFetcher
from sh_policy_rss.fetchers.sh_fgw_fetcher import ShFgwFetcher
from sh_policy_rss.fetchers.sh_stcsm_fetcher import ShStcsmFetcher


SOURCES = [
    {"id": "sh-sheitc-zcfg", "name": "上海市经信委", "fetcher": ShSheitcZcfgFetcher()},
    {"id": "sh-sheitc-zxzj", "name": "上海市经信委专项资金", "fetcher": ShSheitcZxzjFetcher()},
    {"id": "sh-fgw", "name": "上海市发改委", "fetcher": ShFgwFetcher()},
    {"id": "sh-stcsm", "name": "上海市科委", "fetcher": ShStcsmFetcher()},
]

DEFAULT_OUTPUT = "上海政策rss.xml"
DEFAULT_HTML_OUTPUT = "sh_index.html"


def run_fetchers(max_items: int = 20, verbose: bool = False) -> List[FetchResult]:
    results: List[FetchResult] = []

    for src in SOURCES:
        name = src["name"]
        if verbose:
            print(f"[抓取] {name} ...")
        result = src["fetcher"].fetch(max_items=max_items)

        # 注入 source_id 和 city
        for item in result.items:
            item.source_id = src["id"]
            item.source = src["name"]
            item.city = "shanghai"

        results.append(result)

        if verbose:
            if result.success:
                print(f"  ✓ 成功，获取 {result.fetched_count} 条")
            else:
                print(f"  ✗ 失败: {result.error_message}")

    return results


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="上海政策RSS聚合器")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help="输出RSS文件路径")
    parser.add_argument("--html-output", default=DEFAULT_HTML_OUTPUT, help="输出HTML预览页路径")
    parser.add_argument("--max-items", "-n", type=int, default=20, help="每个源最大抓取条数")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")
    args = parser.parse_args()

    print("=" * 60)
    print("上海政策RSS聚合器 - 开始运行")
    print("=" * 60)

    results = run_fetchers(max_items=args.max_items, verbose=args.verbose)

    # 汇总统计
    success_count = sum(1 for r in results if r.success)
    total_items = sum(len(r.items) for r in results)

    print("\n" + "=" * 60)
    print("抓取汇总")
    print("=" * 60)
    for r in results:
        status = "✓" if r.success else "✗"
        print(f"{status} {r.source_name}: {len(r.items)} 条")
        if not r.success:
            print(f"   错误: {r.error_message}")

    print(f"\n总计: {success_count}/{len(results)} 个源成功，共 {total_items} 条政策")

    # 聚合所有条目
    all_items: List[PolicyItem] = []
    for r in results:
        if r.success:
            all_items.extend(r.items)

    # 生成RSS
    rss_content = build_rss(all_items, title="上海政策RSS聚合")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(rss_content)

    print(f"\n[OK] RSS 已保存到: {args.output}")

    # 生成HTML预览页
    index_content = build_index(all_items)
    with open(args.html_output, "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"[OK] 预览页已保存到: {args.html_output}")

    # 预览前10条
    if all_items:
        print("\n── 最新政策预览（前10条）──")
        for i, item in enumerate(sorted(all_items, key=lambda x: x.pub_date, reverse=True)[:10], 1):
            date_str = item.pub_date.strftime("%Y-%m-%d")
            print(f"{i:2}. [{date_str}] [{item.source}] {item.title}")
    else:
        print("\n[警告] 未抓取到任何政策条目。")


if __name__ == "__main__":
    main()
