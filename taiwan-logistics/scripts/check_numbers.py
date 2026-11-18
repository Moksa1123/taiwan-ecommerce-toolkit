#!/usr/bin/env python3
"""
check_numbers.py — SKILL.md、README.md、README.zh-TW.md 裡的每一個數字都要有來由，而且要對得上資料（SOP 6-1）。

做法是白名單：把三個檔的數字全部找出來（程式碼區塊、行內 `code`、網址除外），
每一個都必須被該檔規則的某一條認領，否則失敗。新增數字時要同時登記規則。
SKILL.md 用 RULES，README.md 用 README_RULES，README.zh-TW.md 用 README_ZH_RULES。

規則四種：
    stat   搜尋域的筆數，跟 core.dataset_stats() 比          （--fix 可自動改）
    fact   其他由資料算出來的值，跟 FACTS 比                  （--fix 可自動改）
    data   規格常數：數字必須出現在指定查詢的前 5 名結果裡
    fixed  不從資料來的數字（步驟編號、通過標準、演算法名稱、日期），要寫明理由

引擎照抄 line-api 的 check_numbers.py；三個 taiwan skill 只有 FACTS 與 RULES 不同。

用法：
    python scripts/check_numbers.py            # 有問題 exit 1
    python scripts/check_numbers.py --fix      # stat / fact 不一致時直接改三個檔
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_MD = HERE.parent / "SKILL.md"
README_MD = HERE.parent / "README.md"
README_ZH_MD = HERE.parent / "README.zh-TW.md"
CLI = "logistics-cli"  # npm 安裝程式所在資料夾
sys.path.insert(0, str(HERE))

import core  # noqa: E402


# ---------------------------------------------------------------------------
# 這個 skill 自己的事實與規則
# ---------------------------------------------------------------------------
def _providers() -> list[dict]:
    import csv
    with open(core.DATA_DIR / "providers.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _count(**want) -> int:
    def ok(r):
        return all(r[k] in v if isinstance(v, tuple) else r[k] == v for k, v in want.items())
    return sum(1 for r in _providers() if ok(r))



def _evals(i: int) -> int:
    """evals/RESULTS.md 最新一輪：0＝計分題數、1＝有 skill 答對、2＝沒有 skill 答對。"""
    path = HERE.parent / "evals" / "RESULTS.md"
    m = re.search(r"計分題答對率（(\d+) 題） \| \*\*(\d+)/\d+[^|]*\| (\d+)/\d+",
                  path.read_text(encoding="utf-8")) if path.exists() else None
    return int(m.group(i + 1)) if m else -1


def _ai_platforms() -> int:
    """CLI 支援的 AI 平台數＝<cli>/assets/templates/platforms/*.json 的檔數。
    repo 裡從 taiwan-<skill>/ 往上找 <cli>/assets/templates；在 assets 副本裡就是旁邊的 templates/。"""
    for base in (HERE.parent.parent / CLI / "assets" / "templates", HERE.parent.parent / "templates"):
        d = base / "platforms"
        if d.is_dir():
            return len(list(d.glob("*.json")))
    return -1

FACTS = {
    "evals_n": lambda: _evals(0),
    "evals_with": lambda: _evals(1),
    "evals_without": lambda: _evals(2),
    "rows": lambda: sum(core.dataset_stats().values()),
    "domains": lambda: len(core.CSV_CONFIG),
    "providers": lambda: len(_providers()),
    "aggregators_api": lambda: _count(type=("aggregator", "payment_aggregator"), api_available="true"),
    "carrier_api": lambda: _count(type="carrier", api_available="true"),
    "ondemand": lambda: _count(type="ondemand"),
    "no_api": lambda: _count(api_available="false"),
    # 徽章「providers」：可串接的＝聚合商＋直連物流＋即時配送
    "api_providers": lambda: (_count(type=("aggregator", "payment_aggregator"), api_available="true")
                              + _count(type="carrier", api_available="true") + _count(type="ondemand")),
    "ai_platforms": _ai_platforms,
}

# (正規式, 種類, 參數)。第 1 組是被認領的數字；沒有分組就認領整段。
RULES: list[tuple[str, str, str]] = [
    # ---- 由資料算出來 ----
    (r"has (\d+) rows:", "fact", "providers"),
    (r"(\d+) aggregators with a logistics API", "fact", "aggregators_api"),
    (r"(\d+) direct carrier API", "fact", "carrier_api"),
    (r"(\d+) on-demand services", "fact", "ondemand"),
    (r"(\d+) rows with no public API", "fact", "no_api"),
    (r"\*\*(\d+) rows\*\*", "fact", "rows"),
    (r"in (\d+) search domains", "fact", "domains"),
    # ---- 規格常數：要在資料裡查得到 ----
    (r"狀態 (2073)", "data", "2073|status|2073"),
    # ---- 不從資料來的數字 ----
    (r"AES-256(?:-CBC|-GCM)?|SHA256|MD5|3DES|7-11|7-ELEVEN|B2C|C2C", "fixed", "演算法與通路名稱"),
    (r"(?<![\d.v])\d\. ", "fixed", "步驟編號"),
    (r"FAIL 0|failed 0|exit 0", "fixed", "驗證器的通過標準"),
    (r"≥ 90%", "fixed", "evals 門檻，與 evals/grade.py --min 預設值相同"),
    (r"2026-11-15:", "fixed", "最近一次跑完自我測試與 verify-examples 的日期"),
]


# README.md（英文，也是 npm 套件頁）
# 徽章：shields.io /badge/ 網址不遮（見引擎 _MASKS），徽章數字由 badge 規則核對。
README_RULES: list[tuple[str, str, str]] = [
    # ---- 徽章 ----
    (r"/badge/providers-(\d+)-", "fact", "api_providers"),
    (r"/badge/AI_platforms-(\d+)-", "fact", "ai_platforms"),
    (r"/badge/python-3-", "fixed", "Python 徽章：腳本的最低需求"),
    (r"00457C", "fixed", "PayPal 徽章的品牌色"),
    # ---- 由資料算出來 ----
    (r"Covers (\d+) aggregators with a logistics API", "fact", "aggregators_api"),
    (r"(\d+) direct carrier API \(HCT\)", "fact", "carrier_api"),
    (r"(\d+) on-demand delivery services", "fact", "ondemand"),
    (r"searches (\d+) rows", "fact", "rows"),
    (r"supports (\d+) AI coding agents", "fact", "ai_platforms"),
    (r"On the (\d+) scored questions", "fact", "evals_n"),
    (r"answered (\d+) correctly with the skill", "fact", "evals_with"),
    (r"and (\d+) without it", "fact", "evals_without"),
    # ---- 不從資料來的數字 ----
    (r"</?h[13]\b", "fixed", "置中標題的 HTML 標籤"),
    (r"\*\*Step \d\.\*\*", "fixed", "快速開始的步驟編號"),
    (r"(?:HMAC-)?SHA256|AES-256-(?:CBC|GCM)|MD5|3DES|7-ELEVEN|B2C|C2C|C2B|OAuth 2\.0", "fixed", "演算法、通路與交易型態名稱"),
    (r"ended 2026-07-01", "fixed", "綠界 OK 超商 C2C 終止日（references/audit-20261117.md；providers.csv okmart 列）"),
    (r"Python 3\b", "fixed", "腳本的最低需求"),
    (r"Node\.js 18 or later", "fixed", "logistics-cli/package.json 的 engines.node"),
    (r"runs \d+ checks, 0 failures", "fixed", "test_skill.py 在 2026-11-17 的檢查數；test_skill 增減檢查時要重跑並更新"),
    (r"2026-11-17", "fixed", "最近一次官方文件稽核與自我測試的日期"),
]

# README.zh-TW.md（段落與 README.md 一一對應）
README_ZH_RULES: list[tuple[str, str, str]] = [
    # ---- 徽章 ----
    (r"/badge/providers-(\d+)-", "fact", "api_providers"),
    (r"/badge/AI_platforms-(\d+)-", "fact", "ai_platforms"),
    (r"/badge/python-3-", "fixed", "Python 徽章：腳本的最低需求"),
    (r"00457C", "fixed", "PayPal 徽章的品牌色"),
    # ---- 由資料算出來 ----
    (r"涵蓋 (\d+) 家有物流 API 的聚合商", "fact", "aggregators_api"),
    (r"(\d+) 家直連物流 API", "fact", "carrier_api"),
    (r"(\d+) 家即時配送", "fact", "ondemand"),
    (r"離線查詢 (\d+) 筆", "fact", "rows"),
    (r"支援 (\d+) 個 AI 開發工具", "fact", "ai_platforms"),
    (r"計分的 (\d+) 題", "fact", "evals_n"),
    (r"有 skill 時 Claude 答對 (\d+) 題", "fact", "evals_with"),
    (r"沒有 skill 時答對 (\d+) 題", "fact", "evals_without"),
    # ---- 不從資料來的數字 ----
    (r"</?h[13]\b", "fixed", "置中標題的 HTML 標籤"),
    (r"\*\*Step \d\.\*\*", "fixed", "快速開始的步驟編號"),
    (r"(?:HMAC-)?SHA256|AES-256-(?:CBC|GCM)|MD5|3DES|7-11|B2C|C2C|C2B|OAuth 2\.0", "fixed", "演算法、通路與交易型態名稱"),
    (r"已於 2026-07-01 終止", "fixed", "綠界 OK 超商 C2C 終止日（references/audit-20261117.md；providers.csv okmart 列）"),
    (r"Python 3\b", "fixed", "腳本的最低需求"),
    (r"Node\.js 18 以上", "fixed", "logistics-cli/package.json 的 engines.node"),
    (r"共 \d+ 項檢查，失敗 0", "fixed", "test_skill.py 在 2026-11-17 的檢查數；test_skill 增減檢查時要重跑並更新"),
    (r"2026-11-17", "fixed", "最近一次官方文件稽核與自我測試的日期"),
]


# ---------------------------------------------------------------------------
# 引擎（照抄即可）
# ---------------------------------------------------------------------------
TARGETS = [(SKILL_MD, RULES), (README_MD, README_RULES), (README_ZH_MD, README_ZH_RULES)]

NUM = re.compile(r"\d+(?:[.,]\d+)*")
_MASKS = [
    re.compile(r"^```.*?^```", re.S | re.M),   # 程式碼區塊
    re.compile(r"`[^`\n]+`"),                  # 行內 code
    re.compile(r"\]\([^)\n]*\)"),              # markdown 連結目標
    # 網址（遇到中文標點就停）。shields.io 靜態徽章 /badge/<標籤>-<數字>-<顏色> 不遮，
    # 徽章上的數字照樣要被規則認領，不會因為寫在 <img src> 裡就被略過。
    re.compile(r"https?://(?!img\.shields\.io/badge/)[^\s)）（，、|]+"),
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


def check(path: Path = SKILL_MD, rules: list[tuple[str, str, str]] | None = None,
          fix: bool = False) -> tuple[list[str], int]:
    """回傳 (問題清單, 檢查過的數字個數)。rules 預設 RULES；fix=True 時就地改 stat / fact。"""
    rules = RULES if rules is None else rules
    name = path.name
    text = path.read_text(encoding="utf-8")
    scan = _masked(text)
    match_view = _masked(text, keep_inline=True)
    problems: list[str] = []
    covered: set[int] = set()
    edits: list[tuple[int, int, str]] = []
    stats = core.dataset_stats()

    for pattern, kind, arg in rules:
        found = list(re.finditer(pattern, match_view, re.M))
        if not found:
            problems.append(f"規則沒用到（{name} 改過寫法？）：{pattern}")
            continue
        for m in found:
            span = m.span(1) if m.re.groups else m.span()
            covered.update(range(*m.span()))
            got = text[span[0]:span[1]]
            if kind in ("stat", "fact"):
                want = str(stats.get(arg, -1) if kind == "stat" else FACTS[arg]())
                if got != want:
                    problems.append(f"{kind} {arg}：{name} 寫 {got}，實際 {want}")
                    edits.append((span[0], span[1], want))
            elif kind == "data":
                query, domain, needle = arg.split("|")
                if needle.lower() not in _search_blob(query, domain).lower():
                    problems.append(f"data：查 {query!r}（{domain}）前 5 名找不到 {needle!r}")

    line_of = lambda pos: text.count("\n", 0, pos) + 1  # noqa: E731
    for m in NUM.finditer(scan):
        if not any(i in covered for i in range(*m.span())):
            problems.append(f"{name} 第 {line_of(m.start())} 行的 {m.group(0)} 沒有登記在規則裡")

    if fix and edits:
        for start, end, want in sorted(edits, reverse=True):
            text = text[:start] + want + text[end:]
        path.write_text(text, encoding="utf-8")
    n = sum(1 for _ in NUM.finditer(scan))
    return problems, n


def check_all(fix: bool = False) -> list[tuple[Path, list[str], int]]:
    """檢查 TARGETS 裡存在的檔（安裝版可能沒有 README）。"""
    return [(p, *check(p, r, fix=fix)) for p, r in TARGETS if p.exists()]


def main() -> int:
    core.use_utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--fix", action="store_true", help="stat / fact 不一致時直接改檔")
    args = ap.parse_args()
    bad = 0
    for path, problems, n in check_all(fix=args.fix):
        if not problems:
            print(f"{path.name} 的 {n} 個數字全部登記且與資料一致。")
            continue
        bad += 1
        print(f"{path.name} 有 {len(problems)} 個數字問題：")
        for p in problems:
            print("  ✗", p)
    for path, _ in TARGETS:
        if not path.exists():
            print(f"{path.name} 不存在，略過。")
    if bad and args.fix:
        print("（stat / fact 已改；其餘要人工處理）")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
