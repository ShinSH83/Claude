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
  // URL 경로는 항상 '/'를 구분자로 쓰므로, OS별 경로 구분자로 바뀌는
  // path.join을 거치기 전에 루트('/') 요청을 index.html로 매핑한다.
  // (Windows에서 path.join이 '/'를 '\\'로 바꿔버려 endsWith('/') 검사가
  //  항상 실패하고 루트 접속 시 404가 나던 버그를 여기서 고쳤다.)
  let urlPath = decodeURIComponent(req.url.split('?')[0]);
  if (urlPath === '' || urlPath.endsWith('/')) urlPath += 'index.html';

  const filePath = path.join(ROOT_DIR, urlPath);
  if (!filePath.startsWith(ROOT_DIR)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

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
