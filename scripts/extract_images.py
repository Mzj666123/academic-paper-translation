#!/usr/bin/env python3
"""
从 PDF 提取图片和公式区域，自动识别双列/单列排版
用法：
  python extract_images.py input.pdf output_dir/          # 提取所有图片
  python extract_images.py input.pdf output_dir/ --crop --page 4 --x0 100 --top 200 --x1 500 --bottom 250  # 裁剪指定区域
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("请先安装 pdfplumber: python -m pip install pdfplumber")
    sys.exit(1)


def detect_column_layout(page) -> dict:
    """检测页面是双列还是单列排版"""
    words = page.extract_words()
    if len(words) < 20:
        return {"layout": "unknown", "columns": 1}

    x_coords = [w['x0'] for w in words]
    page_mid = page.width / 2

    left_words = [w for w in words if w['x0'] < page_mid]
    right_words = [w for w in words if w['x0'] > page_mid]

    if len(left_words) > 50 and len(right_words) > 50:
        return {
            "layout": "two-column",
            "columns": 2,
            "mid_x": page_mid,
            "left_count": len(left_words),
            "right_count": len(right_words)
        }
    else:
        return {
            "layout": "single-column",
            "columns": 1,
            "mid_x": page_mid
        }


def get_column(img_x0: float, img_width: float, page_mid: float) -> str:
    """判断图片属于左列还是右列"""
    img_center = img_x0 + img_width / 2
    if img_center < page_mid:
        return "left"
    else:
        return "right"


def extract_images(pdf_path: str, output_dir: str):
    """从 PDF 提取图片，记录位置信息和列归属"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    img_dir = out / "images"
    img_dir.mkdir(exist_ok=True)

    images_info = []
    img_count = 0
    layout_info = {}

    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) >= 3:
            sample_page = pdf.pages[2]
            layout = detect_column_layout(sample_page)
            layout_info = layout
            print(f"排版检测: {layout['layout']} ({layout['columns']}列)")
            if layout['columns'] == 2:
                print(f"  列分界 x = {layout['mid_x']:.0f}pt")

        for page_num, page in enumerate(pdf.pages, 1):
            page_layout = detect_column_layout(page)
            page_mid = page_layout.get('mid_x', page.width / 2)

            for img_idx, img in enumerate(page.images):
                img_count += 1
                x0 = img["x0"]
                top = img["top"]
                w = img["width"]
                h = img["height"]

                column = get_column(x0, w, page_mid)

                bbox = (x0, top, x0 + w, top + h)
                cropped = page.within_bbox(bbox)

                if page_layout['columns'] == 2:
                    img_path = img_dir / f"page{page_num}_{column}_img{img_idx+1}.png"
                else:
                    img_path = img_dir / f"page{page_num}_img{img_idx+1}.png"

                try:
                    im = cropped.to_image(resolution=200)
                    im.save(img_path, format="PNG")

                    images_info.append({
                        "page": page_num,
                        "index": img_idx + 1,
                        "column": column,
                        "layout": page_layout['layout'],
                        "path": str(img_path),
                        "x0": round(x0, 1),
                        "top": round(top, 1),
                        "width": round(w, 1),
                        "height": round(h, 1),
                        "filename": img_path.name
                    })
                    col_tag = f"[{column}]" if page_layout['columns'] == 2 else ""
                    print(f"  ✓ Page {page_num} {col_tag} Image {img_idx+1}: {w:.0f}x{h:.0f}px")
                except Exception as e:
                    print(f"  ✗ Page {page_num}, Image {img_idx+1}: 保存失败 - {e}")

    info_path = out / "images_info.json"
    result = {
        "layout": layout_info,
        "images": images_info
    }
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n共提取 {len(images_info)} 张图片")
    print(f"排版: {layout_info.get('layout', 'unknown')}")
    print(f"图片信息已保存到: {info_path}")
    return images_info


def crop_region(pdf_path: str, output_path: str, page_num: int, x0: float, top: float, x1: float, bottom: float):
    """裁剪 PDF 指定页面的指定区域（用于提取复杂公式）"""
    with pdfplumber.open(pdf_path) as pdf:
        if page_num < 1 or page_num > len(pdf.pages):
            print(f"错误：页码超出范围，共 {len(pdf.pages)} 页")
            sys.exit(1)

        page = pdf.pages[page_num - 1]
        bbox = (x0, top, x1, bottom)
        cropped = page.within_bbox(bbox)
        im = cropped.to_image(resolution=200)
        im.save(output_path, format="PNG")
        print(f"✓ 已裁剪: Page {page_num}, 区域 ({x0:.0f},{top:.0f})-({x1:.0f},{bottom:.0f})")
        print(f"  保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="从 PDF 提取图片和公式")
    parser.add_argument("input", help="输入 PDF 文件路径")
    parser.add_argument("output", help="输出目录或图片文件路径")
    parser.add_argument("--crop", action="store_true", help="裁剪模式（提取公式用）")
    parser.add_argument("--page", type=int, help="裁剪的页码（从1开始）")
    parser.add_argument("--x0", type=float, help="裁剪区域左边界")
    parser.add_argument("--top", type=float, help="裁剪区域上边界")
    parser.add_argument("--x1", type=float, help="裁剪区域右边界")
    parser.add_argument("--bottom", type=float, help="裁剪区域下边界")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"错误：文件不存在 - {args.input}")
        sys.exit(1)

    if args.crop:
        if not all([args.page, args.x0, args.top, args.x1, args.bottom]):
            print("错误：裁剪模式需要指定 --page --x0 --top --x1 --bottom")
            sys.exit(1)
        crop_region(args.input, args.output, args.page, args.x0, args.top, args.x1, args.bottom)
    else:
        extract_images(args.input, args.output)


if __name__ == "__main__":
    main()
