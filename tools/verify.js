#!/usr/bin/env node
/**
 * 채점 엔진 검증 도구.
 *
 * src/app.html 에서 채점 함수만 떼어내 실제 제출 파일에 돌려 봅니다.
 * 화면 없이 자동 채점 결과만 출력하므로, 채점위원 채점 결과와 숫자로 대조할 수 있습니다.
 *
 *   npm install jszip @xmldom/xmldom
 *   node tools/verify.js <유형> <엑셀파일> [발표자료파일]
 *
 * 예:
 *   node tools/verify.js other  제출물/학생A.xlsx 제출물/학생A.pptx
 *   node tools/verify.js dev    제출물/학생B.xlsx
 *
 * 학생 제출물은 개인정보이므로 저장소에 포함하지 않습니다.
 * 암호가 걸린 파일은 먼저 암호를 풀어야 합니다.
 */
const fs = require("fs");
const path = require("path");

global.JSZip = require("jszip");
global.DOMParser = require("@xmldom/xmldom").DOMParser;

const html = fs.readFileSync(path.join(__dirname, "../src/app.html"), "utf8");
const script = html.split("<script>").pop().split("</script>")[0];
const core = script.split('const state={type:"other"')[0];
eval(core.replace(/^"use strict";/, "") + `
;Object.assign(global,{SETS,TPL,parseXlsx,parsePptx,parseDocx,pickSheet,
  scoreSearch,scoreExcelFx,findTables,scoreDocAuto,studentSlideText});`);

const [type, xlsxPath, docPath] = process.argv.slice(2);
if (!SETS[type] || !xlsxPath) {
  console.error("사용법: node tools/verify.js <other|dev|visual> <엑셀파일> [발표자료파일]");
  process.exit(1);
}

(async () => {
  const set = SETS[type];
  const xl = await parseXlsx(await JSZip.loadAsync(fs.readFileSync(xlsxPath)));
  let doc = null;
  if (docPath) {
    const z = await JSZip.loadAsync(fs.readFileSync(docPath));
    doc = set.doc === "pptx" ? await parsePptx(z) : await parseDocx(z);
  }

  const s1 = pickSheet(xl.sheets, set.sheet1, 0);
  const s3 = pickSheet(xl.sheets, set.sheet3, 2);
  const se = scoreSearch(s1, set.tpl);
  const fx = scoreExcelFx(xl.sheets, set);
  const tb = findTables(s3, set.tpl);

  const line = (a, b) => console.log(String(a).padEnd(34) + b);

  console.log(`\n── ${set.label} — ${path.basename(xlsxPath)}`);
  console.log("시트:", xl.sheets.map(s => s.name).join(" | "), "· 차트", xl.charts);

  console.log("\n[정보 검색] 자동 채점 항목");
  line("  출처 다양성 — 검색엔진", `${Math.min(5, se.engKinds.length)}/5  ${se.engKinds.join(", ") || "(없음)"}`);
  line("  출처 다양성 — 생성형 AI", `${Math.min(5, se.aiKinds.length)}/5  ${se.aiKinds.join(", ") || "(없음)"}`);
  line("  GPT 활용 기법", `${Math.min(5, se.tech.length)}/5  ${se.tech.map(t => t.k).join(", ") || "(없음)"}`);
  console.log(`  검색 기록 ${se.entries.length}건 · 출처 표기 ${se.cited}건 (신뢰성 항목은 내용 판정)`);

  console.log("\n[엑셀] 함수 6문항");
  fx.forEach(f => line(`  ${f.id} ${f.label.split(" — ")[0]}`, `${f.got}/${f.pts}  ${f.why}`));
  const headerOK = tb.filter(t => t.hasHeader).length;
  const structure = Math.max(0, Math.min(5, tb.length) - Math.min(2, tb.length - headerOK));
  const ownFx = Math.min(3, tb.filter(t => t.formulas > 0).length);
  console.log(`  함수 소계 ${fx.reduce((a, b) => a + b.got, 0)}/12`);
  line("  표 구조 & 헤더", `${structure}/5  표 ${tb.length}개 중 머리글 있는 표 ${headerOK}개`);
  line("  자체 표 함수", `${ownFx}/3`);
  line("  표 작성 개수", `${Math.min(5, tb.length)}/5`);
  line("  차트 작성 개수", `${Math.min(5, xl.charts)}/5`);
  console.log(`  엑셀 자동 합계 ${structure + fx.reduce((a, b) => a + b.got, 0) + ownFx + Math.min(5, tb.length) + Math.min(5, xl.charts)}/30`);

  if (doc) {
    const pages = studentSlideText(doc, set.doc, set.tpl);
    const blank = pages.every(p => p.blank || !p.text);
    console.log(`\n[${set.doc === "pptx" ? "발표자료" : "제출 문서"}]`);
    if (blank) {
      console.log("  ⚠ 모든 페이지가 원본 양식 그대로입니다 → 40점 전부 손실");
    } else {
      const a = scoreDocAuto(doc, set.doc);
      line("  기본 기능", `${a.pageNum + a.links + a.alt + a.master}/5  ` +
        `번호 ${a.pageNum ? "O" : "X"} · 링크 ${a.linkCount}개 · 대체텍스트 ${a.alt ? "O" : "X"} · 서식통일 ${a.master ? "O" : "X"}`);
      pages.forEach(p => console.log(`  ${p.page}쪽 ${p.frames != null ? `[표·차트 ${p.frames}]` : ""}${p.guide ? ` ⚠안내문구 ${p.guide}개 남음` : ""} ${(p.text || "(양식 그대로)").slice(0, 60)}`));
      const left = pages.filter(p => p.guide > 0);
      if (left.length) console.log(`  ⚠ 원본 안내 문구가 남아 있는 쪽: ${left.map(p => p.page).join(", ")} — 채점위원은 미작성으로 봅니다.`);
      console.log("  나머지 35점은 내용 판정 항목입니다 (브라우저에서 채점).");
    }
  } else {
    console.log(`\n[${set.doc === "pptx" ? "발표자료" : "제출 문서"}] 파일 없음 → 40점 전부 손실`);
  }
  console.log("");
})().catch(e => {
  console.error("오류:", e.message);
  console.error("암호가 걸린 파일이면 먼저 암호를 풀어 주세요.");
  process.exit(1);
});
