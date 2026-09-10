// player.js - 국군 병사(플레이어) 상태, 이동, 충돌, 체력
const player = {
  x: 2.5,
  y: 17.5,
  angle: 0, // 동쪽(서울 시내 대로 방향)을 바라보며 시작
  radius: 0.22,
  walkSpeed: 3.0,   // 타일/초
  runSpeed: 4.8,
  rotSpeed: 2.6,    // 라디안/초 (키보드 회전)
  mouseSensitivity: 0.0022,
  health: 100,
  maxHealth: 100,
  alive: true,
  bobPhase: 0,
  bobAmount: 0,
  lastMineFlashTime: -999,
};

function resetPlayer() {
  player.x = 2.5;
  player.y = 17.5;
  player.angle = 0;
  player.health = player.maxHealth;
  player.alive = true;
  player.bobPhase = 0;
  player.bobAmount = 0;
}

function playerTakeDamage(amount) {
  if (!player.alive) return;
  player.health = Math.max(0, player.health - amount);
  if (player.health <= 0) {
    player.alive = false;
  }
}

function collidesAt(x, y) {
  const r = player.radius;
  return (
    isWallTile(getTile(x - r, y - r)) ||
    isWallTile(getTile(x + r, y - r)) ||
    isWallTile(getTile(x - r, y + r)) ||
    isWallTile(getTile(x + r, y + r))
  );
}

function updatePlayer(dt, keys, mouseDX) {
  if (!player.alive) return;

  // 마우스 시점 회전
  if (mouseDX) {
    player.angle += mouseDX * player.mouseSensitivity;
  }
  // 키보드 회전 (마우스 포인터락 미사용 시 대체 조작)
  if (keys['ArrowLeft']) player.angle -= player.rotSpeed * dt;
  if (keys['ArrowRight']) player.angle += player.rotSpeed * dt;

  const forwardX = Math.cos(player.angle);
  const forwardY = Math.sin(player.angle);
  const strafeX = Math.cos(player.angle + Math.PI / 2);
  const strafeY = Math.sin(player.angle + Math.PI / 2);

  let dx = 0, dy = 0;
  if (keys['KeyW']) { dx += forwardX; dy += forwardY; }
  if (keys['KeyS']) { dx -= forwardX; dy -= forwardY; }
  if (keys['KeyD']) { dx += strafeX; dy += strafeY; }
  if (keys['KeyA']) { dx -= strafeX; dy -= strafeY; }

  const len = Math.hypot(dx, dy);
  const isMoving = len > 0.0001;
  if (isMoving) { dx /= len; dy /= len; }

  const running = keys['ShiftLeft'] || keys['ShiftRight'];
  const speed = running ? player.runSpeed : player.walkSpeed;

  const stepX = dx * speed * dt;
  const stepY = dy * speed * dt;

  const nx = player.x + stepX;
  const ny = player.y + stepY;
  if (!collidesAt(nx, player.y)) player.x = nx;
  if (!collidesAt(player.x, ny)) player.y = ny;

  // 걷기 시 화면/무기 흔들림 (bob)
  if (isMoving) {
    const bobSpeed = running ? 14 : 9;
    player.bobPhase += dt * bobSpeed;
    player.bobAmount = 1.0;
  } else {
    player.bobAmount *= 0.85;
  }

  checkMineTrigger();
}

function checkMineTrigger() {
  const tile = getTile(player.x, player.y);
  if (tile === TILE_MINE) {
    playerTakeDamage(25);
    player.lastMineFlashTime = performance.now();
    setTile(player.x, player.y, TILE_EMPTY); // 지뢰는 1회성
  }
}
