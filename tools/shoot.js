#!/usr/bin/env node
/**
 * 매뉴얼에 넣을 화면 캡쳐를 만듭니다.
 *
 *   python3 tools/make-demo.py .demo     # 가짜 데모 제출물
 *   node tools/build.js                  # docs/ 생성 (캡쳐 없이)
 *   node tools/shoot.js                  # src/manual-shots.json 생성
 *   node tools/build.js                  # 캡쳐를 넣어 다시 생성
 *
 * 캡쳐에 쓰는 제출물은 tools/make-demo.py 가 만든 가짜 데이터입니다.
 * 대회 문제 원문이나 학생 제출물은 절대 쓰지 않습니다.
 */
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.join(__dirname, "..");
const page_url = "file://" + path.join(root, "docs/2026/final/self-scoring/index.html");
const demo = process.argv[2] || path.join(root, ".demo");
const W = 900;

(async () => {
  for (const f of ["demo.xlsx", "demo.pptx"]) {
    if (!fs.existsSync(path.join(demo, f)))
      throw new Error(`${path.join(demo, f)} 가 없습니다. 먼저 python3 tools/make-demo.py ${demo} 를 돌리세요.`);
  }

  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: W, height: 1000 },
    deviceScaleFactor: 2,
    colorScheme: "light",
  });
  /* 이 컨테이너는 외부 CDN 을 못 씁니다. JSZip 은 로컬 사본으로 바꿔치기하고,
     웹폰트 요청은 바로 끊어 기다리지 않게 합니다. (화면 글꼴만 조금 다릅니다) */
  await page.route("**/cdnjs.cloudflare.com/**/jszip*.js", route =>
    route.fulfill({ contentType: "application/javascript",
      body: fs.readFileSync(path.join(root, "node_modules/jszip/dist/jszip.min.js"), "utf8") }));
  await page.route("**/fonts.googleapis.com/**", route => route.abort());
  await page.route("**/fonts.gstatic.com/**", route => route.abort());

  const shots = {};

  const boxOf = sel => page.locator(sel).first().evaluate(el => {
    const r = el.getBoundingClientRect();
    return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height };
  });

  async function snap(key, clip) {
    const buf = await page.screenshot({
      fullPage: true,
      clip: {
        x: Math.max(0, Math.round(clip.x)),
        y: Math.max(0, Math.round(clip.y)),
        width: Math.min(W, Math.round(clip.width)),
        height: Math.round(clip.height),
      },
    });
    const out = path.join(demo, key + ".png");
    fs.writeFileSync(out, buf);
    shots[key] = out;
  }

  /** 두 요소 사이를 한 장으로 (from 위 pad 부터 to 아래 pad 까지) */
  async function span(key, fromSel, toSel, pad = 14) {
    const a = await boxOf(fromSel), b = await boxOf(toSel);
    await snap(key, { x: 0, y: a.y - pad, width: W, height: b.y + b.h - a.y + pad * 2 });
  }
  async function one(key, sel, pad = 14) {
    const a = await boxOf(sel);
    await snap(key, { x: Math.max(0, a.x - pad), y: a.y - pad, width: a.w + pad * 2, height: a.h + pad * 2 });
  }

  await page.goto(page_url, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);

  /* 1. 첫 화면 — 제목·버튼부터 파일 넣는 칸까지 */
  await span("home", "header.top", "#drops");

  /* 2. 파일을 넣은 상태 */
  const inputs = await page.locator("#drops input[type=file]").all();
  await inputs[0].setInputFiles(path.join(demo, "demo.xlsx"));
  await inputs[1].setInputFiles(path.join(demo, "demo.pptx"));
  await page.waitForTimeout(300);
  await span("filled", "#drops", "#run");

  /* 3. 채점 결과 — 총점과 영역별 막대 */
  await page.click("#run");
  await page.waitForSelector("#result:not([hidden])");
  await page.waitForTimeout(1200);
  await span("score", "#result .scoreline", "#result .bars");

  /* 4. AI에게 물어보기 */
  await one("ai", "#ai .aibox");

  /* 5. AI 판정을 반영한 뒤의 총점 — 실제로 붙여넣고 눌러 봅니다 */
  await page.fill("#aiPaste",
    "s1: 3점 — 문제를 끊어서 검색했습니다.\n" +
    "s2: 5점 — 자기 상황에 맞춰 물었습니다.\n" +
    "s6: 4점 — 출처를 4건 적었습니다.\n" +
    "점수: s1=3, s2=5, s6=4, d1=5, d2=6, d3=7, d4=6");
  await page.click("#aiApply");
  await page.waitForTimeout(1000);
  await span("scored", "#result .scoreline", "#result .bars");

  /* 6. 연습 가이드 — 위에서 세 개까지만 */
  {
    const a = await boxOf("#guides");
    const n = await page.locator("#guides .guide").count();
    const last = await boxOf(`#guides .guide:nth-child(${Math.min(3, n)})`);
    await snap("guide", { x: 0, y: a.y - 14, width: W, height: last.y + last.h - a.y + 20 });
  }

  await browser.close();

  /* 용량을 줄여 data URI 로 바꿉니다 */
  const { execFileSync } = require("child_process");
  const outJson = {};
  for (const [k, file] of Object.entries(shots)) {
    const webp = file.replace(/\.png$/, ".webp");
    execFileSync("python3", ["-c", `
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
w = ${W}
im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
im.save(sys.argv[2], "WEBP", quality=76, method=6)
`, file, webp]);
    const b = fs.readFileSync(webp);
    outJson[k] = "data:image/webp;base64," + b.toString("base64");
    console.log("  " + k.padEnd(7), Math.round(b.length / 1024) + "KB");
  }
  fs.writeFileSync(path.join(root, "src/manual-shots.json"), JSON.stringify(outJson));
  console.log("src/manual-shots.json —",
    Math.round(fs.statSync(path.join(root, "src/manual-shots.json")).size / 1024), "KB");
})().catch(e => { console.error(e.message); process.exit(1); });
