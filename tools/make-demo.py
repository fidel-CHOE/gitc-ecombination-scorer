#!/usr/bin/env python3
"""
매뉴얼 화면 캡쳐용 '데모 제출물'을 만듭니다.

대회 문제 원문이나 학생 제출물은 절대 쓰지 않습니다. 내용은 전부 지어낸
가짜 데이터(우리 동네 도서관)이고, 채점기가 실제로 어떻게 채점하는지를
보여주기 위한 용도로만 씁니다.

    python3 tools/make-demo.py <출력폴더>
      → demo.xlsx, demo.pptx
"""
import sys, random, os
from openpyxl import Workbook
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from pptx import Presentation
from pptx.util import Inches, Pt

out = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(out, exist_ok=True)
random.seed(7)

# ─────────────────────────────────────────── 엑셀
wb = Workbook()

# Sheet1 — 검색
s1 = wb.active
s1.title = "Searching(검색)"
s1["A1"] = "Step 1. 정보 검색"
s1["C3"], s1["D3"], s1["E3"] = "도구", "검색어 / 프롬프트", "검색 결과 요약"

rows = [
    ("Google", "동네 도서관 좌석 예약 시스템 도입 사례",
     "서울 강동구청 자료에 따르면 예약제 도입 후 좌석 회전율이 1.6배 올랐다. https://www.gangdong.go.kr/library/notice/1204"),
    ("네이버", "공공도서관 이용자 만족도 조사 2025",
     "문화체육관광부 2025 조사에서 만족도 1위 요인은 '조용한 환경'(38%)이었다. https://www.mcst.go.kr/report/2025-library"),
    ("Bing", "public library seat occupancy sensor",
     "IoT 좌석 센서를 쓰면 빈자리를 실시간으로 안내할 수 있다. https://www.techforlibraries.org/seat-sensor"),
    ("ChatGPT", "너는 공공도서관 공간 기획 전문가야. 좌석이 늘 부족한 동네 도서관의 문제를 세 가지로 정리해 줘.",
     "① 좌석 회전율 낮음 ② 시간대 편중 ③ 용도별 공간 부족 으로 정리해 주었다."),
    ("Gemini", "예를 들어 '무인 반납기'처럼, 사람 손을 덜 쓰는 도서관 기술을 2개 더 알려줘.",
     "자동 서가 정리 로봇과 셀프 대출 키오스크를 알려주었다."),
    ("Claude", "단계별로 차근차근 생각해서, 좌석 예약제를 도입할 때 생길 문제 2가지를 짚어줘.",
     "① 예약 후 안 오는 노쇼 ② 디지털 기기에 익숙하지 않은 이용자 소외 를 짚어주었다."),
    ("코파일럿", "정확히 숫자 번호(1, 2, 3)를 붙여서 3가지만 제시해 줘.",
     "번호를 붙인 목록으로 답을 정리해 주었다."),
    ("뤼튼", "우리 동네는 학생 이용자가 특히 많은 상황이야. 시험기간에 어떤 문제가 생길까?",
     "시험기간 좌석 독점과 소음 민원이 늘어난다고 답했다."),
]
for i, (tool, q, a) in enumerate(rows):
    r = 4 + i
    s1.cell(r, 3, tool); s1.cell(r, 4, q); s1.cell(r, 5, a)
for w, c in zip((14, 52, 62), "CDE"):
    s1.column_dimensions[c].width = w

# Sheet2 — 함수
s2 = wb.create_sheet("Function(함수)")
s2["A1"] = "Step 2. 함수"
hdr = ["ID", "도서관", "구분", "이용자수", "좌석수", "장서수", "미반납률"]
for j, h in enumerate(hdr):
    s2.cell(4, 1 + j, h)
kinds = ["구립", "시립", "작은도서관", "학교"]
for i in range(50):
    r = 5 + i
    s2.cell(r, 1, f"L{i+1:02d}")
    s2.cell(r, 2, f"{random.choice('가나다라마바사아자차')}동 도서관")
    s2.cell(r, 3, kinds[i % 4])
    s2.cell(r, 4, random.randint(40, 99))
    s2.cell(r, 5, random.randint(20, 90))
    s2.cell(r, 6, random.randint(30, 95))
    s2.cell(r, 7, round(random.uniform(0.005, 0.06), 3))
    s2.cell(r, 9, f"=SUM(D{r}:F{r})")
    s2.cell(r, 10, f"=RANK.EQ(I{r},$I$5:$I$54)")
    s2.cell(r, 11, f'=IF(AND(J{r}<=5,G{r}<=2%),"Select","-")')
s2.cell(4, 9, "총점"); s2.cell(4, 10, "순위"); s2.cell(4, 11, "선정")
s2["M4"] = "① 구립 도서관 개수"
s2["N4"] = '=COUNTIF(C5:C54,"구립")'
s2["M6"] = "② 찾을 ID"; s2["N6"] = "L07"
s2["M7"] = "② 도서관 이름"; s2["N7"] = "=VLOOKUP(N6,A5:B54,2,FALSE)"
s2["M9"] = "③ 안내 메시지"
s2["N9"] = '=IFERROR(VLOOKUP(N6,A5:B54,2,FALSE),"ID를 확인하세요")'

# Sheet3 — 시각화
s3 = wb.create_sheet("Visualization(시각화)")
s3["A1"] = "Step 3. 표와 차트"

tables = [
    ("구분별 도서관 수", ["구분", "개수"], [(k, f'=COUNTIF(\'Function(함수)\'!C5:C54,"{k}")') for k in kinds]),
    ("구분별 평균 이용자수", ["구분", "평균"], [(k, f'=ROUND(AVERAGEIF(\'Function(함수)\'!C5:C54,"{k}",\'Function(함수)\'!D5:D54),1)') for k in kinds]),
    ("구분별 총 좌석수", ["구분", "좌석 합계"], [(k, f'=SUMIF(\'Function(함수)\'!C5:C54,"{k}",\'Function(함수)\'!E5:E54)') for k in kinds]),
    ("구분별 총 장서수", ["구분", "장서 합계"], [(k, f'=SUMIF(\'Function(함수)\'!C5:C54,"{k}",\'Function(함수)\'!F5:F54)') for k in kinds]),
    ("최종 선정 도서관", ["구분", "선정 수"], [(k, f'=COUNTIFS(\'Function(함수)\'!C5:C54,"{k}",\'Function(함수)\'!K5:K54,"Select")') for k in kinds]),
]
anchors = [("A", 3), ("E", 3), ("A", 12), ("E", 12), ("A", 21)]
starts = []
for (title, head, body), (col, row) in zip(tables, anchors):
    ci = ord(col) - 64
    s3.cell(row, ci, title)
    s3.cell(row + 1, ci, head[0]); s3.cell(row + 1, ci + 1, head[1])
    for k, (label, formula) in enumerate(body):
        s3.cell(row + 2 + k, ci, label)
        s3.cell(row + 2 + k, ci + 1, formula)
    s3.cell(row + 6, ci, "나의 인사이트 : 구립 도서관이 가장 많고 좌석도 가장 넉넉합니다.")
    starts.append((ci, row + 1, row + 5))

# 차트는 일부러 3개만 만듭니다 — 매뉴얼에서 "덜 채운 항목"이 어떻게 보이는지 보여주려고요.
chart_types = [PieChart, BarChart, LineChart]
chart_at = ["I3", "I20", "I37"]
for (ci, hrow, lrow), Ct, at in zip(starts, chart_types, chart_at):
    ch = Ct()
    ch.title = s3.cell(hrow - 1, ci).value
    ch.height, ch.width = 6, 10
    data = Reference(s3, min_col=ci + 1, min_row=hrow, max_row=lrow)
    cats = Reference(s3, min_col=ci, min_row=hrow + 1, max_row=lrow)
    ch.add_data(data, titles_from_data=True)
    ch.set_categories(cats)
    s3.add_chart(ch, at)

for c, w in (("A", 30), ("B", 16), ("E", 30), ("F", 16)):
    s3.column_dimensions[c].width = w

xlsx_path = os.path.join(out, "demo.xlsx")
wb.save(xlsx_path)

# openpyxl 은 수식의 계산 결과를 저장하지 않습니다. 실제 엑셀 파일에는 항상
# 결과값이 함께 들어 있으므로, 데모 파일도 같은 모습이 되도록 값을 넣어 줍니다.
import re, zipfile, shutil

vals = {row[0]: (row[3] + row[4] + row[5]) for row in
        [[s2.cell(5 + i, j + 1).value for j in range(7)] for i in range(50)]}
totals = {f"I{5+i}": s2.cell(5 + i, 4).value + s2.cell(5 + i, 5).value + s2.cell(5 + i, 6).value
          for i in range(50)}
order = sorted(totals.values(), reverse=True)
cached = {"Function(함수)": {}, "Visualization(시각화)": {}}
for i in range(50):
    t = totals[f"I{5+i}"]
    rank = order.index(t) + 1
    cached["Function(함수)"][f"I{5+i}"] = str(t)
    cached["Function(함수)"][f"J{5+i}"] = str(rank)
cached["Function(함수)"]["N4"] = str(sum(1 for i in range(50) if kinds[i % 4] == "구립"))
for (title, head, body), (col, row) in zip(tables, anchors):
    ci = ord(col) - 64
    for k, kind in enumerate(kinds):
        idx = [i for i in range(50) if kinds[i % 4] == kind]
        if "개수" in head[1]:
            v = len(idx)
        elif "평균" in head[1]:
            v = round(sum(s2.cell(5 + i, 4).value for i in idx) / len(idx), 1)
        elif "좌석" in head[1]:
            v = sum(s2.cell(5 + i, 5).value for i in idx)
        elif "장서" in head[1]:
            v = sum(s2.cell(5 + i, 6).value for i in idx)
        else:
            v = sum(1 for i in idx if order.index(totals[f"I{5+i}"]) + 1 <= 5
                    and s2.cell(5 + i, 7).value <= 0.02)
        ref = chr(64 + ci + 1) + str(row + 2 + k)
        cached["Visualization(시각화)"][ref] = str(v)

names = [ws.title for ws in wb.worksheets]
tmp = xlsx_path + ".tmp"
with zipfile.ZipFile(xlsx_path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        m = re.match(r"xl/worksheets/sheet(\d+)\.xml$", item.filename)
        if m:
            sheet = names[int(m.group(1)) - 1]
            table = cached.get(sheet, {})
            if table:
                xml_s = data.decode("utf8")

                def put(mo):
                    ref = mo.group(1)
                    s = mo.group(0)
                    if ref not in table or "</f>" not in s:
                        return s
                    if "<v></v>" in s:
                        return s.replace("<v></v>", f"<v>{table[ref]}</v>")
                    if "<v>" in s:
                        return s
                    return s.replace("</f>", f"</f><v>{table[ref]}</v>")

                xml_s = re.sub(r'<c r="([A-Z]+\d+)"[^>]*>.*?</c>', put, xml_s, flags=re.S)
                data = xml_s.encode("utf8")
        zout.writestr(item, data)
shutil.move(tmp, xlsx_path)

# ─────────────────────────────────────────── 발표자료
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
blank = prs.slide_layouts[6]


def tb(slide, x, y, w, h, text, size=18, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.name = "맑은 고딕"
    return box


pages = [
    ("우리 동네 도서관 이용 개선 제안",
     "목차\n1. 분석 결과\n2. 최종 선정\n3. 이용자별 제안",
     "대한민국 · 데모 학생"),
    ("이용자가 많은 도서관일수록 좌석이 부족합니다.",
     "· 구립 도서관 13곳 중 9곳이 좌석 대비 이용자 수 상위권입니다.\n"
     "· 미반납률이 2% 이하인 곳은 전체의 31%뿐입니다.\n"
     "· 아래 두 차트는 엑셀 Sheet3에서 만든 표를 그대로 옮긴 것입니다.", None),
    ("이용자 수 상위 · 미반납률 2% 이하인 5곳을 최종 선정했습니다.",
     "선정 도서관 표 (구분 / 이용자수 / 좌석수 / 미반납률)\n\n"
     "① 사람이 모입니다 — 이용자 수 상위 5위 안에 드는 곳만 남겼습니다.\n"
     "② 관리가 됩니다 — 미반납률 2% 이하만 남겼습니다.\n"
     "③ 공간이 있습니다 — 5곳 모두 좌석 수가 50석 이상입니다.", None),
    ("필요한 기술과 이용자가 원하는 것",
     "기술 요구사항\n1. 좌석 실시간 안내판\n2. 무인 반납기\n3. 셀프 대출 키오스크\n4. 예약 알림 문자",
     "이용자 요구사항\n1. 조용한 열람 공간\n2. 시험기간 좌석 확대\n3. 휠체어 접근 가능한 통로\n4. 큰 글씨 도서 코너"),
]
for i, (title, body, sub) in enumerate(pages):
    sl = prs.slides.add_slide(blank)
    tb(sl, 0.7, 0.5, 12, 1.1, title, 28, True)
    if i == 3:
        tb(sl, 0.7, 1.9, 5.7, 4.4, body, 17)
        tb(sl, 6.9, 1.9, 5.7, 4.4, sub, 17)
    else:
        tb(sl, 0.7, 1.9, 12, 4.0, body, 17)
        if sub:
            tb(sl, 0.7, 6.0, 12, 0.7, sub, 15)
    num = tb(sl, 11.6, 6.8, 1.4, 0.4, f"{i+1} / 4", 13)
    num.name = f"page-{i+1}"

# 대체 텍스트 (차트 대신 도형에 넣어 두었습니다 — descr 속성이면 채점기가 인식합니다)
for sl in prs.slides:
    sl.shapes[0]._element.nvSpPr.cNvPr.set("descr", "이 장의 결론을 한 문장으로 적은 제목입니다.")

prs.save(os.path.join(out, "demo.pptx"))
print("만들었습니다:", os.path.join(out, "demo.xlsx"), os.path.join(out, "demo.pptx"))
