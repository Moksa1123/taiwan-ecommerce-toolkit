#!/usr/bin/env python3
"""
grade.py — evals 評分：同一組真題，比「有 skill」與「沒有 skill」的答對率。

流程（給其他 skill 照抄，只要換 cases.json）：
    1. python evals/grade.py --questions > q.txt          只印題目，不含答案，交給作答者
    2. 作答者各跑一次，答案存成 evals/runs/<日期>-with-skill.json、-without-skill.json
       格式：{"meta": {"date": ..., "model": ..., "how": ...}, "answers": {"<id>": "<答案全文>"}}
    3. python evals/grade.py --with <檔> --without <檔> [--write]
       --write 把結果加到 evals/RESULTS.md 最上面（舊紀錄保留）

評分規則：cases.json 每題的 must 是「組」的清單，每一組至少命中一個正規式（不分大小寫），
全部組都命中才算對。沒有 skill 也答對的題沒有鑑別度（SOP 6-4），不列入計分，要換題。

exit code：有 skill 的計分題答對率低於 --min（預設 90%）就回 1。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases.json"
RESULTS = HERE / "RESULTS.md"

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")


def load_cases() -> list[dict]:
    # retired：已確認沒有鑑別度而換掉的題，保留在檔案裡當紀錄，不再作答與評分
    return [c for c in json.loads(CASES.read_text(encoding="utf-8"))["cases"] if not c.get("retired")]


def correct(case: dict, answer: str) -> bool:
    return all(any(re.search(p, answer or "", re.I) for p in group) for group in case["must"])


def load_run(path: str) -> tuple[dict, dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data.get("meta", {}), data["answers"]


def report(cases, with_run, without_run) -> tuple[str, float]:
    (wm, wa), (om, oa) = with_run, without_run
    rows, counted, w_ok, o_ok, w_all, o_all = [], 0, 0, 0, 0, 0
    for c in cases:
        w, o = correct(c, wa.get(c["id"], "")), correct(c, oa.get(c["id"], ""))
        w_all += w
        o_all += o
        if o and w:
            note = "沒 skill 也對：不計分，要換題"
        else:
            counted += 1
            w_ok += w
            o_ok += o
            note = "" if w else "有 skill 仍答錯"
        rows.append(f"| `{c['id']}` | {c['trust']} | {'✅' if w else '❌'} | {'✅' if o else '❌'} | {note} |")
    n = len(cases)
    rate = w_ok / counted * 100 if counted else 0.0
    date = wm.get("date") or om.get("date") or "?"
    out = [
        f"## {date}",
        "",
        "| 項目 | 有 skill | 沒有 skill |",
        "|---|---|---|",
        f"| 計分題答對率（{counted} 題） | **{w_ok}/{counted}（{rate:.1f}%）** | "
        f"{o_ok}/{counted}（{(o_ok / counted * 100 if counted else 0):.1f}%） |",
        f"| 全部題目（{n} 題） | {w_all}/{n} | {o_all}/{n} |",
        f"| 模型 | {wm.get('model', '?')} | {om.get('model', '?')} |",
        f"| 作答方式 | {wm.get('how', '?')} | {om.get('how', '?')} |",
        f"| 答案檔 | `{wm.get('file', '')}` | `{om.get('file', '')}` |",
        "",
        "| 題目 | 可信度 | 有 skill | 沒有 skill | 備註 |",
        "|---|---|---|---|---|",
        *rows,
        "",
    ]
    return "\n".join(out), rate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", action="store_true", help="只印題目（給作答者，不含答案與評分）")
    ap.add_argument("--with", dest="with_", help="有 skill 的答案檔")
    ap.add_argument("--without", help="沒有 skill 的答案檔")
    ap.add_argument("--write", action="store_true", help="把結果加到 RESULTS.md 最上面")
    ap.add_argument("--min", type=float, default=90.0, help="有 skill 計分題答對率門檻（%%）")
    args = ap.parse_args()
    cases = load_cases()

    if args.questions:
        for c in cases:
            print(f"{c['id']}\t{c['question']}")
        return 0
    if not (args.with_ and args.without):
        ap.error("要給 --with 與 --without，或用 --questions")

    runs = []
    for p in (args.with_, args.without):
        meta, ans = load_run(p)
        meta.setdefault("file", Path(p).as_posix().split(HERE.parent.name + "/")[-1])
        runs.append((meta, ans))
    text, rate = report(cases, runs[0], runs[1])
    print(text)

    if args.write:
        head = "# evals 結果\n\n最新的在最上面。題目與評分標準見 `cases.json`，評分程式 `grade.py`。\n\n"
        old = RESULTS.read_text(encoding="utf-8") if RESULTS.exists() else head
        body = old[len(head):] if old.startswith(head) else old
        RESULTS.write_text(head + text + "\n" + body, encoding="utf-8")
        print(f"已寫入 {RESULTS}")
    return 0 if rate >= args.min else 1


if __name__ == "__main__":
    raise SystemExit(main())
