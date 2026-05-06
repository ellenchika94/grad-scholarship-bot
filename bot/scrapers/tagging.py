"""対象テキストから短いタグを抽出するルールベース要約。"""
from __future__ import annotations

import re

# 学位・学年（順序が優先順位）
_DEGREE_RULES: list[tuple[str, str]] = [
    ("修士1〜2年", r"修士1[～〜~\-]?2年|修士1年生?・2年生?|修士1[\-〜～]2年生?"),
    ("修士1年", r"修士1年"),
    ("修士2年", r"修士2年"),
    ("修士", r"修士|マスター|master"),
    ("博士", r"博士|ドクター|Ph\.?D|PhD|D課程"),
    ("学部", r"学部[1-4]?[~〜～\-]?[1-4]?年|大学[1-4]年|学士課程"),
    ("高校生", r"高校[1-3]?年|高校生"),
]

_NATIONALITY_RULES: list[tuple[str, str]] = [
    ("日本国籍", r"日本国籍|日本人"),
    ("永住権可", r"永住権"),
]

_FIELD_RULES: list[tuple[str, str]] = [
    ("STEM", r"STEM|科学.{0,3}技術.{0,3}工学.{0,3}数学"),
    ("自然科学", r"自然科学"),
    ("理工系", r"理工系"),
    ("工学", r"工学(?!部)"),
    ("医学・医療", r"医学|医療|看護|公衆衛生|保健"),
    ("数学", r"^数学|数学科目|数学を専攻"),
    ("文系", r"人文|社会科学|文系"),
    ("芸術", r"芸術|アート|美術|音楽"),
    ("BME", r"BME|生命科学.*工学|バイオメディカル"),
    ("情報", r"情報.{0,3}(科学|工学)|コンピュータ|computer"),
    ("分野不問", r"分野.{0,3}不問|分野.{0,3}問わ"),
]

_DESTINATION_RULES: list[tuple[str, str]] = [
    ("米国", r"米国|アメリカ|USA|US$|United States"),
    ("英国", r"英国|イギリス|UK|United Kingdom"),
    ("カナダ", r"カナダ|Canada"),
    ("豪州", r"オーストラリア|豪州|Australia"),
    ("欧州", r"欧州|ヨーロッパ|Europe|EU圏"),
    ("アジア", r"アジア(?!.*欧)"),
]

_LANGUAGE_RULES: list[tuple[str, str]] = [
    ("TOEFL/IELTS要", r"TOEFL|IELTS"),
]

_GENDER_RULES: list[tuple[str, str]] = [
    ("女性のみ", r"女性(?:である|に限る|のみ|であること)"),
]


def _scan(rules: list[tuple[str, str]], text: str) -> list[str]:
    out: list[str] = []
    for label, pat in rules:
        if re.search(pat, text, re.IGNORECASE):
            out.append(label)
    return out


def extract_tags(raw: str | None, *, include_destination: bool = False) -> str | None:
    """対象テキストから簡潔なタグ列を生成。何も拾えなければ None。"""
    if not raw:
        return None

    parts: list[str] = []
    # 学位は最初にヒットしたものだけ採用（「修士」と「修士1〜2年」が両方当たるのを防ぐ）
    for label, pat in _DEGREE_RULES:
        if re.search(pat, raw, re.IGNORECASE):
            parts.append(label)
            break

    parts.extend(_scan(_GENDER_RULES, raw))
    parts.extend(_scan(_NATIONALITY_RULES, raw))
    parts.extend(_scan(_FIELD_RULES, raw))
    if include_destination:
        parts.extend(_scan(_DESTINATION_RULES, raw))
    parts.extend(_scan(_LANGUAGE_RULES, raw))

    # 重複排除しつつ順序維持
    seen: set[str] = set()
    deduped: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            deduped.append(p)

    return " / ".join(deduped) if deduped else None
