#!/usr/bin/env python3
"""
원본 제출 양식(빈 파일)에서 '양식 문구 해시'를 뽑습니다.

채점기는 학생이 낸 파일과 원본 양식을 대조해서, 학생이 실제로 쓴 내용만 골라냅니다.
그러려면 원본 양식의 문구를 알아야 하는데, 대회 문제 원문을 공개 저장소에 그대로
싣지 않으려고 해시(FNV-1a 32bit, base36)만 담습니다. 대조는 정확히 똑같이 동작합니다.

사용법:
    python3 tools/make-template-hashes.py \
        --other  "가이드폴더/Submission1_eCombination_Other.xlsx" "가이드폴더/Submission2_eCombination_Other.pptx" \
        --dev    "가이드폴더/Submission1_e-Combination_Dev.xlsx"  "가이드폴더/Submission2_e-Combination_Dev.pptx" \
        --visual "가이드폴더/Submission1_eCombination_Visual.xlsx"

출력된 JSON을 src/app.html 의 `const TPL = ...` 에 붙여 넣으세요.

필요 패키지: openpyxl
"""
import argparse, html, json, re, sys, zipfile

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl 이 필요합니다:  pip install openpyxl")


def h32(s: str) -> str:
    """JS 쪽 h32() 와 같은 값을 냅니다 (FNV-1a 32bit → base36)."""
    h = 0x811C9DC5
    for ch in s:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    if h == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while h:
        out = digits[h % 36] + out
        h //= 36
    return out


def norm(s) -> str:
    return " ".join(str("" if s is None else s).split())


def sheet_hashes(path, matcher):
    wb = openpyxl.load_workbook(path)
    for ws in wb.worksheets:
        if matcher.search(ws.title):
            vals = {norm(c.value) for row in ws.iter_rows() for c in row if norm(c.value)}
            return sorted({h32(v) for v in vals})
    return []


def slide_hashes(path):
    z = zipfile.ZipFile(path)
    names = sorted(
        [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
        key=lambda x: int(re.findall(r"\d+", x)[0]),
    )
    out = []
    for n in names:
        xml = z.read(n).decode("utf8", "ignore")
        texts = {norm(html.unescape(m)) for m in re.findall(r"<a:t>(.*?)</a:t>", xml, re.S)}
        out.append(sorted({h32(t) for t in texts if t}))
    return out


S1 = re.compile(r"Searching|검색")
S3 = re.compile(r"Visualization|시각화")

ap = argparse.ArgumentParser()
for k in ("other", "dev", "visual"):
    ap.add_argument(f"--{k}", nargs="+", metavar="FILE", help=f"{k} 유형의 빈 양식 (xlsx [pptx])")
args = ap.parse_args()

result = {}
for key in ("other", "dev", "visual"):
    files = getattr(args, key)
    if not files:
        continue
    xlsx = next((f for f in files if f.lower().endswith(".xlsx")), None)
    pptx = next((f for f in files if f.lower().endswith(".pptx")), None)
    result[key] = {
        "s1": sheet_hashes(xlsx, S1) if xlsx else [],
        "s3": sheet_hashes(xlsx, S3) if xlsx else [],
        "ppt": slide_hashes(pptx) if pptx else [],
    }

print(json.dumps(result, separators=(",", ":")))
