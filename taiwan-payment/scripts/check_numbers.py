#!/usr/bin/env python3
"""
check_numbers.py — SKILL.md 裡的每一個數字都要有來由，而且要對得上資料（SOP 6-1）。

做法是白名單：把 SKILL.md 的數字全部找出來（程式碼區塊、行內 `code`、網址除外），
每一個都必須被 RULES 的某一條認領，否則失敗。新增數字時要同時登記規則。

規則四種：
    stat   搜尋域的筆數，跟 core.dataset_stats() 比          （--fix 可自動改）
    fact   其他由資料算出來的值，跟 FACTS 比                  （--fix 可自動改）
    data   規格常數：數字必須出現在指定查詢的前 5 名結果裡
    fixed  不從資料來的數字（步驟編號、通過標準、演算法名稱、日期），要寫明理由

引擎照抄 line-api 的 check_numbers.py；三個 taiwan skill 只有 FACTS 與 RULES 不同。

用法：
    python scripts/check_numbers.py            # 有問題 exit 1
    python scripts/check_numbers.py --fix      # stat / fact 不一致時直接改 SKILL.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_MD = HERE.parent / "SKILL.md"
sys.path.insert(0, str(HERE))

import core  # noqa: E402


# ---------------------------------------------------------------------------
# 這個 skill 自己的事實與規則
# ---------------------------------------------------------------------------
FACTS = {
    "rows": lambda: sum(core.dataset_stats().values()),
    "domains": lambda: len(core.CSV_CONFIG),
    "providers": lambda: core.dataset_stats()["provider"],
}

# (正規式, 種類, 參數)。第 1 組是被認領的數字；沒有分組就認領整段。
RULES: list[tuple[str, str, str]] = [
    # ---- 由資料算出來 ----
    (r"共 (\d+) 家", "fact", "providers"),
    (r"共 \*\*(\d+) 筆\*\*", "fact", "rows"),
    (r"分 (\d+) 個搜尋域", "fact", "domains"),
    # ---- 規格常數：要在資料裡查得到 ----
    (r"綠界回 (10200073)", "data", "10200073|error|10200073"),
    # ---- 不從資料來的數字 ----
    (r"(?:HMAC-)?SHA-?256|AES-256(?:-CBC|-GCM)?|MD5|LINE Pay v4", "fixed", "演算法與產品版本名稱"),
    (r"padding 可能到 32 bytes", "fixed", "藍新官方外掛以 32 bytes 補齊，標準答案見 tests/vectors/newebpay.json"),
    (r"(?<![\d.v])\d\. ", "fixed", "步驟編號"),
    (r"(?:FAIL|失敗|略過也要是) 0|exit 0|非 0", "fixed", "驗證器的通過標準"),
    (r"≥ 90%", "fixed", "evals 門檻，與 evals/grade.py --min 預設值相同"),
    (r"2026-11-15：", "fixed", "最近一次跑完自我測試與 verify-examples 的日期"),
]


# ---------------------------------------------------------------------------
# 引擎（照抄即可）
# ---------------------------------------------------------------------------
NUM = re.compile(r"\d+(?:[.,]\d+)*")
_MASKS = [
    re.compile(r"^```.*?^```", re.S | re.M),   # 程式碼區塊
    re.compile(r"`[^`\n]+`"),                  # 行內 code
    re.compile(r"\]\([^)\n]*\)"),              # markdown 連結目標
    re.compile(r"https?://[^\s)）（，、|]+"),    # 網址（遇到中文標點就停）
]


def _masked(text: str, keep_inline: bool = False) -> str:
    """把不檢查的區段換成等長空白，位置不變。"""
    for i, rx in enumerate(_MASKS):
        if keep_inline and i == 1:
            continue
        text = rx.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    return text


def _search_blob(query: str, domain: str) -> str:
    hits = core.search(query, domain=domain, max_results=5)
    return " | ".join(" ".join(str(v) for k, v in h.items() if not k.startswith("_")) for h in hits)


def check(path: Path = SKILL_MD, fix: bool = False) -> tuple[list[str], int]:
    """回傳 (問題清單, 檢查過的數字個數)。fix=True 時就地改 stat / fact。"""
    text = path.read_text(encoding="utf-8")
    scan = _masked(text)
    match_view = _masked(text, keep_inline=True)
    problems: list[str] = []
    covered: set[int] = set()
    edits: list[tuple[int, int, str]] = []
    stats = core.dataset_stats()

    for pattern, kind, arg in RULES:
        found = list(re.finditer(pattern, match_view, re.M))
        if not found:
            problems.append(f"規則沒用到（SKILL.md 改過寫法？）：{pattern}")
            continue
        for m in found:
            span = m.span(1) if m.re.groups else m.span()
            covered.update(range(*m.span()))
            got = text[span[0]:span[1]]
            if kind in ("stat", "fact"):
                want = str(stats.get(arg, -1) if kind == "stat" else FACTS[arg]())
                if got != want:
                    problems.append(f"{kind} {arg}：SKILL.md 寫 {got}，實際 {want}")
                    edits.append((span[0], span[1], want))
            elif kind == "data":
                query, domain, needle = arg.split("|")
                if needle.lower() not in _search_blob(query, domain).lower():
                    problems.append(f"data：查 {query!r}（{domain}）前 5 名找不到 {needle!r}")

    line_of = lambda pos: text.count("\n", 0, pos) + 1  # noqa: E731
    for m in NUM.finditer(scan):
        if not any(i in covered for i in range(*m.span())):
            problems.append(f"第 {line_of(m.start())} 行的 {m.group(0)} 沒有登記在 RULES")

    if fix and edits:
        for start, end, want in sorted(edits, reverse=True):
            text = text[:start] + want + text[end:]
        path.write_text(text, encoding="utf-8")
    n = sum(1 for _ in NUM.finditer(scan))
    return problems, n


def main() -> int:
    core.use_utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--fix", action="store_true", help="stat / fact 不一致時直接改 SKILL.md")
    args = ap.parse_args()
    problems, n = check(fix=args.fix)
    if not problems:
        print(f"SKILL.md 的 {n} 個數字全部登記且與資料一致。")
        return 0
    print(f"SKILL.md 有 {len(problems)} 個數字問題：")
    for p in problems:
        print("  ✗", p)
    if args.fix:
        print("（stat / fact 已改；其餘要人工處理）")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
