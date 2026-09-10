// smoke.test.js - Playwright 기반 자동 스모크 테스트
// 실행: node tests/smoke.test.js  (사전에 `npm install` 및 `npx playwright install chromium` 필요)
//
// 정적 파일 서버를 스스로 띄운 뒤 Chromium으로 게임을 열어
// 시작 화면 -> 이동/충돌 -> 지뢰 피해 -> 사망/게임오버 -> 재시작 흐름을 검증한다.

const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT_DIR = path.join(__dirname, '..');
const PORT = 8933;

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
};

function startServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      // path.join이 Windows에서 '/'를 '\\'로 바꿔버리므로, OS별 구분자로
      // 바뀌기 전에 URL 경로 상태에서 루트('/') 요청을 index.html로 매핑한다.
      let urlPath = decodeURIComponent(req.url.split('?')[0]);
      if (urlPath === '' || urlPath.endsWith('/')) urlPath += 'index.html';
      const filePath = path.join(ROOT_DIR, urlPath);
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
    server.listen(PORT, () => resolve(server));
  });
}

function assert(condition, message) {
  if (!condition) throw new Error(`FAIL: ${message}`);
  console.log(`  OK: ${message}`);
}

async function run() {
  const server = await startServer();
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const errors = [];

  try {
    const page = await browser.newPage({ viewport: { width: 900, height: 600 } });
    page.on('pageerror', (e) => errors.push(e.message));

    await page.goto(`http://localhost:${PORT}/index.html`, { waitUntil: 'load' });

    console.log('1) 시작 화면');
    const startVisible = await page.evaluate(
      () => !document.getElementById('start-screen').classList.contains('hidden')
    );
    assert(startVisible, '시작 화면이 표시된다');

    console.log('2) 게임 시작');
    await page.click('#start-btn');
    await page.waitForTimeout(200);
    const playingHidden = await page.evaluate(
      () => document.getElementById('start-screen').classList.contains('hidden')
    );
    assert(playingHidden, '시작 버튼 클릭 시 시작 화면이 사라진다');

    console.log('3) 이동 및 벽 충돌');
    const before = await page.evaluate(() => ({ x: player.x, y: player.y }));
    await page.keyboard.down('KeyD'); // 우측 스트레이프 (열린 도로 방향)
    await page.waitForTimeout(500);
    await page.keyboard.up('KeyD');
    const after = await page.evaluate(() => ({ x: player.x, y: player.y }));
    assert(after.y !== before.y || after.x !== before.x, '키 입력으로 플레이어 위치가 변한다');

    const collision = await page.evaluate(() => {
      // 벽으로 알려진 좌표(2,3열 사이 건물)에 충돌하는지 확인
      return collidesAt(2.9, 13.5);
    });
    assert(collision === true, '벽 타일에서 충돌 판정이 true를 반환한다');

    console.log('4) 지뢰 피해');
    const mineResult = await page.evaluate(() => {
      player.health = player.maxHealth;
      player.x = 8.5;
      player.y = 4.5; // 지도상 지뢰 타일
      checkMineTrigger();
      const first = player.health;
      checkMineTrigger(); // 이미 소실된 지뢰는 재발동하지 않아야 함
      const second = player.health;
      return { first, second };
    });
    assert(mineResult.first === 75, '지뢰를 밟으면 체력이 25 감소한다 (100 -> 75)');
    assert(mineResult.second === 75, '같은 지뢰는 두 번 터지지 않는다');

    console.log('5) 사망 및 게임오버');
    await page.evaluate(() => playerTakeDamage(200));
    await page.waitForTimeout(200);
    const gameOverVisible = await page.evaluate(
      () => !document.getElementById('gameover-screen').classList.contains('hidden')
    );
    assert(gameOverVisible, '체력이 0이 되면 게임오버 화면이 표시된다');
    const aliveAfterDeath = await page.evaluate(() => player.alive);
    assert(aliveAfterDeath === false, '체력이 0이면 alive 상태가 false가 된다');

    console.log('6) 재시작');
    await page.click('#restart-btn');
    await page.waitForTimeout(200);
    const afterRestart = await page.evaluate(() => ({
      health: player.health,
      alive: player.alive,
      gameOverHidden: document.getElementById('gameover-screen').classList.contains('hidden'),
    }));
    assert(afterRestart.health === 100, '재시작 시 체력이 100으로 복구된다');
    assert(afterRestart.alive === true, '재시작 시 alive 상태가 true로 복구된다');
    assert(afterRestart.gameOverHidden, '재시작 시 게임오버 화면이 사라진다');

    assert(errors.length === 0, `브라우저 콘솔/런타임 에러가 없다 (감지된 에러: ${JSON.stringify(errors)})`);

    console.log('\n모든 테스트 통과.');
  } finally {
    await browser.close();
    server.close();
  }
}

run().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
