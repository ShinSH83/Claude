// serve.js - 게임을 실제로 플레이하기 위한 로컬 정적 파일 서버
// 실행: node serve.js  (또는 npm run serve)
// 실행 후 터미널에 나오는 주소를 브라우저(Chrome, Edge 등)에서 직접 열어야 한다.
// (이 스크립트는 서버만 띄울 뿐 브라우저를 자동으로 열지 않는다.)

const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT_DIR = __dirname;
const PORT = process.env.PORT || 8080;

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
};

const server = http.createServer((req, res) => {
  let filePath = path.join(ROOT_DIR, decodeURIComponent(req.url.split('?')[0]));
  if (filePath.endsWith('/')) filePath = path.join(filePath, 'index.html');
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream' });
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log(`서버 실행 중: http://localhost:${PORT}`);
  console.log('브라우저에서 위 주소를 열어 게임을 플레이하세요. (Ctrl+C로 종료)');
});
