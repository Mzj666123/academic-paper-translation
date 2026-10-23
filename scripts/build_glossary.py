#!/usr/bin/env python3
"""
学术翻译全局术语库管理脚本
功能：读取已有术语库，合并新抽取的术语（去重、频次累加），写回文件。

用法：
  1. 初始化空库：python build_glossary.py --init --output 学术翻译术语库.xlsx
  2. 合并更新：python build_glossary.py --merge --existing 学术翻译术语库.xlsx --new new_terms.json --output 学术翻译术语库.xlsx
  3. 导出查看：python build_glossary.py --read 学术翻译术语库.xlsx

新术语 JSON 格式：
[
  {"english": "finite element analysis", "chinese": "有限元分析", "frequency": 15, "category": "方法", "source": "论文A"},
  {"english": "magnetic field", "chinese": "磁场", "frequency": 12, "category": "核心概念", "source": "论文A"}
]
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    print("请先安装 openpyxl: python -m pip install openpyxl")
    sys.exit(1)

HEADERS = ["英文术语", "中文译名", "累计出现频次", "术语类别", "首次来源"]
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


def create_empty_book():
    """创建空的术语库工作簿"""
    wb = Workbook()
    ws = wb.active
    ws.title = "学术翻译术语库"

    for col, header in enumerate(HEADERS, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER

    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 25
    ws.freeze_panes = "A2"
    return wb


def read_existing_terms(filepath):
    """读取已有术语库，返回 dict: english -> {chinese, frequency, category, source}"""
    wb = load_workbook(filepath)
    ws = wb.active
    terms = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        eng = str(row[0]).strip()
        terms[eng] = {
            "chinese": str(row[1]).strip() if row[1] else "",
            "frequency": int(row[2]) if row[2] else 0,
            "category": str(row[3]).strip() if row[3] else "",
            "source": str(row[4]).strip() if row[4] else "",
        }
    return terms


def merge_terms(existing, new_terms):
    """合并新术语到已有库，返回合并后的列表"""
    merged = dict(existing)  # copy

    for term in new_terms:
        eng = term["english"].strip()
        if eng in merged:
            # 已有：频次累加，保留原有译名和来源
            merged[eng]["frequency"] += term.get("frequency", 1)
        else:
            # 新增
            merged[eng] = {
                "chinese": term.get("chinese", ""),
                "frequency": term.get("frequency", 1),
                "category": term.get("category", ""),
                "source": term.get("source", ""),
            }

    # 按频次降序排序
    sorted_terms = sorted(merged.items(), key=lambda x: x[1]["frequency"], reverse=True)
    return sorted_terms


def write_terms(filepath, sorted_terms):
    """将术语列表写入 Excel"""
    wb = create_empty_book()
    ws = wb.active

    for idx, (eng, data) in enumerate(sorted_terms, 2):
        ws.cell(row=idx, column=1, value=eng).border = THIN_BORDER
        ws.cell(row=idx, column=2, value=data["chinese"]).border = THIN_BORDER
        ws.cell(row=idx, column=3, value=data["frequency"]).border = THIN_BORDER
        ws.cell(row=idx, column=4, value=data["category"]).border = THIN_BORDER
        ws.cell(row=idx, column=5, value=data["source"]).border = THIN_BORDER
        for col in range(1, 6):
            ws.cell(row=idx, column=col).alignment = Alignment(vertical="center")

    wb.save(filepath)
    print(f"✅ 术语库已更新: {filepath}")
    print(f"   共 {len(sorted_terms)} 条术语")


def cmd_init(args):
    wb = create_empty_book()
    wb.save(args.output)
    print(f"✅ 空术语库已创建: {args.output}")


def cmd_merge(args):
    # 读取已有库
    if Path(args.existing).exists():
        existing = read_existing_terms(args.existing)
        print(f"读取已有术语库: {len(existing)} 条")
    else:
        existing = {}
        print("已有术语库不存在，将创建新库")

    # 读取新术语
    with open(args.new, "r", encoding="utf-8-sig") as f:
        new_terms = json.load(f)
    print(f"本次新抽取术语: {len(new_terms)} 条")

    # 合并
    merged = merge_terms(existing, new_terms)
    print(f"合并后总计: {len(merged)} 条")

    # 写回
    write_terms(args.output, merged)


def cmd_read(args):
    terms = read_existing_terms(args.read)
    print(f"术语库共 {len(terms)} 条：")
    print(f"{'英文术语':<35} {'中文译名':<25} {'频次':<6} {'类别'}")
    print("-" * 80)
    for eng, data in sorted(terms.items(), key=lambda x: x[1]["frequency"], reverse=True):
        print(f"{eng:<35} {data['chinese']:<25} {data['frequency']:<6} {data['category']}")


def main():
    parser = argparse.ArgumentParser(description="学术翻译全局术语库管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init
    p_init = subparsers.add_parser("init", help="创建空术语库")
    p_init.add_argument("--output", required=True, help="输出文件路径")

    # merge
    p_merge = subparsers.add_parser("merge", help="合并新术语到已有库")
    p_merge.add_argument("--existing", required=True, help="已有术语库路径")
    p_merge.add_argument("--new", required=True, help="新术语 JSON 文件路径")
    p_merge.add_argument("--output", required=True, help="输出文件路径")

    # read
    p_read = subparsers.add_parser("read", help="读取并打印术语库")
    p_read.add_argument("read", help="术语库文件路径")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "merge":
        cmd_merge(args)
    elif args.command == "read":
        cmd_read(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()