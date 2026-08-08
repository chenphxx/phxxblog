"""Markdown 渲染服务。"""
import markdown as md


def render_markdown(text: str) -> str:
    """将 Markdown 原文渲染为 HTML。

    启用常用扩展: 围栏代码块、表格、列表、自动换行、属性、目录。
    代码高亮由前端 Vditor 负责, 后端只产出带 class 的 HTML。
    """
    return md.markdown(
        text or "",
        extensions=[
            "fenced_code",
            "tables",
            "sane_lists",
            "nl2br",
            "attr_list",
            "toc",
        ],
        output_format="html5",
    )
