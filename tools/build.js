#!/usr/bin/env node
/**
 * src/app.html  →  docs/index.html
 *
 * src/app.html 은 Claude Artifact 게시용 본문입니다. Artifact 는 게시할 때
 * <!doctype>·<head>·<body> 뼈대를 자동으로 씌워 주기 때문에 소스에는 없습니다.
 * GitHub Pages 는 그런 게 없으므로, 같은 본문에 뼈대만 입혀서 docs/index.html 로 냅니다.
 * 채점 로직은 한 벌뿐이고, 두 배포본은 이 파일에서 갈립니다.
 */
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const body = fs.readFileSync(path.join(root, "src/app.html"), "utf8");

const page = `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="2026 GITC e-Combination 제출물을 채점 루브릭대로 채점하고 연습 가이드를 뽑아주는 자가채점 도구">
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

fs.mkdirSync(path.join(root, "docs"), { recursive: true });
fs.writeFileSync(path.join(root, "docs/index.html"), page);
fs.writeFileSync(path.join(root, "docs/.nojekyll"), "");
fs.writeFileSync(path.join(root, "docs/CNAME"), "gitc.visioncampus.co.kr\n");
console.log("docs/index.html 생성 완료 —", page.length, "자");
