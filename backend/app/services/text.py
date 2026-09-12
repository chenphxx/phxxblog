"""文本统计: 文章字数与预计阅读时间。"""
import math
import re

# 中日韩字符(按"字"计)
_CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿぀-ヿ가-힯]")
# 英文/数字(按"词"计)
_WORD_RE = re.compile(r"[A-Za-z0-9_']+")

# 预计阅读速度(字/分钟)
READING_SPEED = 300


def count_words(text: str | None) -> int:
    """统计字数: 中日韩字符按字计, 英文/数字按单词计。"""
    if not text:
        return 0
    return len(_CJK_RE.findall(text)) + len(_WORD_RE.findall(text))


def reading_minutes(word_count: int) -> int:
    """按固定速度估算阅读时间(分钟), 不足 1 分钟按 1 分钟计。"""
    if word_count <= 0:
        return 0
    return max(1, math.ceil(word_count / READING_SPEED))
