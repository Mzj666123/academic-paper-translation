#!/usr/bin/env python3
"""
Markdown 转 PDF 脚本（学术论文标准排版）
用法：python md_to_pdf.py input.md output.pdf

排版规范：
- 正文：宋体 12号，1.5倍行距，首行缩进2字符，两端对齐
- 一级标题：黑体 16号，居中
- 二级标题：黑体 14号，左对齐
- 三级标题：黑体 12号，左对齐
- 表格：三线表，表头黑体，内容宋体
- 图表标注：居中，宋体 10号
- 公式：$$...$$ 标记，自动渲染为标准数学排版图片，居中
- 全文统一字体，无混排
"""

import argparse
import sys
import os
import re
import tempfile
from pathlib import Path


def check_dependencies():
    missing = []
    try:
        import docx
    except ImportError:
        missing.append("python-docx")
    try:
        import win32com.client
    except ImportError:
        missing.append("pywin32")
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")
    if missing:
        print(f"缺少依赖: {', '.join(missing)}")
        print(f"请运行: python -m pip install {' '.join(missing)}")
        sys.exit(1)


def render_formula(formula_latex: str, output_path: str):
    """将 LaTeX 公式渲染为 PNG 图片"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    formula_latex = formula_latex.strip().strip('$').strip()

    eq_num = None
    tag_match = re.search(r'\\tag\{([^}]+)\}\s*$', formula_latex)
    if tag_match:
        eq_num = f"({tag_match.group(1)})"
        formula_latex = formula_latex[:tag_match.start()].strip()
    else:
        eq_match = re.search(r'\((\d+)\)\s*$', formula_latex)
        if eq_match:
            eq_num = eq_match.group(0)
            formula_latex = formula_latex[:eq_match.start()].strip()

    fig = plt.figure(figsize=(8, 0.7))

    fig.text(0.42, 0.5, f'${formula_latex}$',
             ha='center', va='center', fontsize=15)

    if eq_num:
        fig.text(0.95, 0.5, eq_num, ha='right', va='center', fontsize=12)

    plt.axis('off')
    plt.savefig(output_path, dpi=200, bbox_inches='tight', pad_inches=0.05)
    plt.close()


def clean_inline_math(text: str) -> str:
    """清理行内 $...$ 数学符号，转换为规范的纯文本"""
    def replace_inline(match):
        inner = match.group(1)
        inner = inner.replace(r'\\times', '×')
        inner = inner.replace(r'\\cdot', '·')
        inner = inner.replace(r'\\pi', 'π')
        inner = inner.replace(r'\\mu', 'μ')
        inner = inner.replace(r'\\alpha', 'α')
        inner = inner.replace(r'\\theta', 'θ')
        inner = inner.replace(r'\\omega', 'ω')
        inner = re.sub(r'_\{([^}]+)\}', r'_\1', inner)
        inner = re.sub(r'\^\{([^}]+)\}', r'^\1', inner)
        inner = inner.replace('\\', '')
        return inner

    return re.sub(r'\$([^$]+)\$', replace_inline, text)


def add_paragraph_with_math(doc, text: str, font_name="宋体", size=12):
    """添加段落，自动识别 $...$ 变量并设置为斜体"""
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    text = text.replace("**", "")
    text = re.sub(r'^[-*]\s+', '', text)

    parts = re.split(r'(\$[^$]+\$)', text)

    for part in parts:
        if part.startswith('$') and part.endswith('$') and len(part) > 2:
            inner = part[1:-1]
            inner = inner.replace(r'\\times', '×')
            inner = inner.replace(r'\\cdot', '·')
            inner = inner.replace(r'\\pi', 'π')
            inner = inner.replace(r'\\mu', 'μ'
            inner = inner.replace(r'\\alpha', 'α')
            inner = inner.replace(r'\\theta', 'θ'
            inner = inner.replace('\\', '')

            sub_match = re.match(r'^([a-zA-Z]+)_\{([^}]+)\}$', inner)
            if sub_match:
                run = p.add_run(sub_match.group(1))
                set_font(run, font_name, size, bold=False)
                run.italic = True
                sub_run = p.add_run(sub_match.group(2))
                set_font(sub_run, font_name, size, bold=False)
                sub_run.italic = True
                sub_run.font.subscript = True
            else:
                run = p.add_run(inner)
                set_font(run, font_name, size, bold=False)
                run.italic = True
        else:
            run = p.add_run(part)
            set_font(run, font_name, size, bold=False)

    return p


def set_font(run, font_name="宋体", size=12, bold=False):
    """统一设置字体，解决中英文混排问题"""
    run.font.name = font_name
    run.font.size = size
    run.font.bold = bold
    from docx.oxml.ns import qn
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)


def md_to_docx(md_path: str, docx_path: str):
    """将 Markdown 转换为 Word 文档（标准学术排版）"""
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.8)
        section.right_margin = Cm(2.8)

    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(12)
    style._element.rPr.rFonts.set(qn('w:eastAsia'), "宋体")
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.first_line_indent = Cm(0.74)
    style.paragraph_format.space_after = Pt(0)

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            i += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row_line = lines[i].strip()
                if re.match(r'^\|[\s\-:|]+\|$', row_line):
                    i += 1
                    continue
                cells = [c.strip() for c in row_line.split("|")[1:-1]]
                table_rows.append(cells)
                i += 1

            if table_rows:
                n_cols = len(table_rows[0])
                table = doc.add_table(rows=len(table_rows), cols=n_cols)
                table.style = "Table Grid"
                table.alignment = WD_ALIGN_PARAGRAPH.CENTER

                for r_idx, row_data in enumerate(table_rows):
                    for c_idx in range(n_cols):
                        if c_idx < len(row_data):
                            cell = table.rows[r_idx].cells[c_idx]
                            cell.text = ""
                            p = cell.paragraphs[0]
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            p.paragraph_format.first_line_indent = Cm(0)
                            p.paragraph_format.line_spacing = 1.0
                            p.paragraph_format.space_after = Pt(0)

                            run = p.add_run(row_data[c_idx])
                            is_header = (r_idx == 0)
                            set_font(run, "宋体" if not is_header else "黑体", Pt(10), bold=is_header)

                doc.add_paragraph()
            continue

        if line.startswith("# ") and not line.startswith("## "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(12)
            text = stripped.lstrip("# ").strip()
            text = text.replace("**", "")
            run = p.add_run(text)
            set_font(run, "黑体", Pt(16), bold=True)
            i += 1
            continue

        if line.startswith("## ") and not line.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            text = stripped.lstrip("# ").strip()
            text = text.replace("**", "")
            run = p.add_run(text)
            set_font(run, "黑体", Pt(14), bold=True)
            i += 1
            continue

        if line.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            text = stripped.lstrip("# ").strip()
            text = text.replace("**", "")
            run = p.add_run(text)
            set_font(run, "黑体", Pt(12), bold=True)
            i += 1
            continue

        img_match = re.match(r'^!\[(.*?)\]\((.*?)\)\s*$', stripped)
        if img_match:
            img_desc = img_match.group(1)
            img_path = img_match.group(2)

            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(3)

            abs_img_path = os.path.join(os.path.dirname(md_path), img_path)
            if os.path.exists(abs_img_path):
                run = p.add_run()
                run.add_picture(abs_img_path, width=Cm(14))
            else:
                run = p.add_run(f"[图片缺失: {img_path}]")
                set_font(run, "宋体", Pt(10))

            if img_desc:
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.first_line_indent = Cm(0)
                p_cap.paragraph_format.space_after = Pt(8)
                run_cap = p_cap.add_run(img_desc)
                set_font(run_cap, "宋体", Pt(10), bold=False)

            i += 1
            continue

        if stripped.startswith("$$") and stripped.endswith("$$"):
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                render_formula(stripped, tmp_path)

                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(6)

                run = p.add_run()
                run.add_picture(tmp_path, width=Cm(12))
            except Exception as e:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.first_line_indent = Cm(0)
                run = p.add_run(stripped.replace('$$', ''))
                set_font(run, "宋体", Pt(12))
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            i += 1
            continue

        if stripped.startswith("[图") or stripped.startswith("[表"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            text = stripped.replace("[", "").replace("]", "")
            text = text.replace("**", "")
            run = p.add_run(text)
            set_font(run, "宋体", Pt(10), bold=False)
            i += 1
            continue

        if re.match(r'^[\s]*[a-zA-Z0-9_]+\s*=\s*.+\([0-9]+\)\s*$', stripped):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(stripped)
            set_font(run, "Times New Roman", Pt(12), bold=False)
            i += 1
            continue

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        text = stripped
        text = text.replace("**", "")
        text = clean_inline_math(text)
        text = re.sub(r'^[-*]\s+', '', text)

        run = p.add_run(text)
        set_font(run, "宋体", Pt(12), bold=False)

        i += 1

    doc.save(docx_path)
    print(f"  Word 文档已生成: {docx_path}")


def docx_to_pdf(docx_path: str, pdf_path: str):
    """使用 Word COM 接口转 PDF"""
    import win32com.client

    word = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False

        abs_docx = os.path.abspath(docx_path)
        abs_pdf = os.path.abspath(pdf_path)

        doc = word.Documents.Open(abs_docx)
        doc.SaveAs(abs_pdf, FileFormat=17)
        doc.Close()
        print(f"  PDF 已生成: {pdf_path}")
    finally:
        if word:
            word.Quit()


def main():
    parser = argparse.ArgumentParser(description="Markdown 转 PDF（学术论文标准排版）")
    parser.add_argument("input", help="输入 Markdown 文件路径")
    parser.add_argument("output", help="输出 PDF 文件路径")
    args = parser.parse_args()

    check_dependencies()

    if not Path(args.input).exists():
        print(f"错误：输入文件不存在 - {args.input}")
        sys.exit(1)

    docx_path = args.output.replace(".pdf", "_temp.docx")

    try:
        print("步骤1/2：Markdown → Word")
        md_to_docx(args.input, docx_path)

        print("步骤2/2：Word → PDF")
        docx_to_pdf(docx_path, args.output)

        if os.path.exists(docx_path):
            os.remove(docx_path)

        size_kb = os.path.getsize(args.output) / 1024
        print(f"\n✅ 完成！PDF 文件大小: {size_kb:.1f} KB")
        print(f"   排版规范：宋体正文/黑体标题/1.5倍行距/首行缩进2字符")

    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        print("提示：请确保系统已安装 Microsoft Word")
        if os.path.exists(docx_path):
            try:
                os.remove(docx_path)
            except:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
