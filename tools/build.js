#!/usr/bin/env node
/**
 * src/*.html  →  docs/
 *
 * src/app.html 은 Claude Artifact 게시용 본문입니다. Artifact 는 게시할 때
 * <!doctype>·<head>·<body> 뼈대를 자동으로 씌워 주기 때문에 소스에는 없습니다.
 * GitHub Pages 는 그런 게 없으므로, 같은 본문에 뼈대만 입혀서 내보냅니다.
 * 채점 로직은 한 벌뿐이고, 두 배포본은 이 파일에서 갈립니다.
 *
 * 나오는 파일:
 *   docs/index.html                            GITC 자료실 첫 화면
 *   docs/2026/final/self-scoring/index.html    자가채점기
 *   docs/CNAME                                 사용자 지정 도메인 (빌드마다 다시 씀)
 */
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const DOMAIN = "gitc.visioncampus.co.kr";

/** Artifact 용 본문에 GitHub Pages 용 뼈대를 씌웁니다. */
function shell(body, description) {
  return `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="${description}">
<style>
  :root { color-scheme: light dark; }
  body { margin: 0; font-family: system-ui, sans-serif; font-size: 14px; background: #f7f7f5; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
</head>
<body>
${body}
</body>
</html>
`;
}

/**
 * 매뉴얼 화면 캡쳐를 페이지 안에 그대로 심습니다.
 * src/manual-shots.json 이 있으면 `const SHOTS = {};` 를 실제 이미지로 바꿔치기합니다.
 * (소스에는 이미지를 넣지 않습니다 — 파일이 너무 커지고 diff 를 읽을 수 없게 됩니다)
 */
function withShots(body) {
  const p = path.join(root, "src", "manual-shots.json");
  if (!fs.existsSync(p)) {
    console.log("  (매뉴얼 캡쳐 없음 — tools/shoot.js 를 먼저 돌리세요)");
    return body;
  }
  const shots = JSON.parse(fs.readFileSync(p, "utf8"));
  const n = Object.keys(shots).length;
  const bytes = JSON.stringify(shots).length;
  console.log(`  매뉴얼 캡쳐 ${n}장 —`, Math.round(bytes / 1024), "KB");
  return body.replace("const SHOTS = {};", "const SHOTS = " + JSON.stringify(shots) + ";");
}

function emit(relPath, srcName, description) {
  const body = withShots(fs.readFileSync(path.join(root, "src", srcName), "utf8"));
  const out = path.join(root, "docs", relPath);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, shell(body, description));
  console.log(`  docs/${relPath}  —`, body.length, "자");
}

fs.mkdirSync(path.join(root, "docs"), { recursive: true });

emit("index.html", "hub.html",
  "2026 GITC 한국대표단 e-Combination 자료실 — 자가채점기와 준비 자료");
emit("2026/final/self-scoring/index.html", "app.html",
  "2026 GITC e-Combination 제출물을 채점 루브릭대로 채점하고 연습 가이드를 뽑아주는 자가채점 도구");

fs.writeFileSync(path.join(root, "docs/.nojekyll"), "");
fs.writeFileSync(path.join(root, "docs/CNAME"), DOMAIN + "\n");
console.log("빌드 완료 —", DOMAIN);
