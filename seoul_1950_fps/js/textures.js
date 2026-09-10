// textures.js - 벽/바닥 픽셀아트 텍스처를 코드로 생성한다 (외부 이미지 자산 없이 동작)
const TEX_SIZE = 32;

function makeCanvas(size) {
  const c = document.createElement('canvas');
  c.width = size;
  c.height = size;
  return c;
}

// 결정적 의사난수 (매번 동일한 패턴이 나오도록)
function hashNoise(i, j, seed) {
  const v = Math.sin(i * 127.1 + j * 311.7 + seed * 74.7) * 43758.5453;
  return v - Math.floor(v);
}

function buildBrickTexture() {
  // 종로 상가 붉은 벽돌 건물
  const c = makeCanvas(TEX_SIZE);
  const ctx = c.getContext('2d');
  const block = 4;
  for (let y = 0; y < TEX_SIZE; y += block) {
    const rowOffset = (Math.floor(y / block) % 2 === 0) ? 0 : block / 2;
    for (let x = -block; x < TEX_SIZE; x += block) {
      const n = hashNoise(x, y, 1);
      const shade = 0.85 + n * 0.3;
      const r = Math.min(255, 122 * shade);
      const g = Math.min(255, 58 * shade);
      const b = Math.min(255, 46 * shade);
      ctx.fillStyle = `rgb(${r | 0},${g | 0},${b | 0})`;
      ctx.fillRect(x + rowOffset, y, block - 1, block - 1);
    }
  }
  // 총탄 자국 / 그을음
  ctx.fillStyle = 'rgba(20,15,12,0.6)';
  ctx.fillRect(6, 20, 3, 3);
  ctx.fillRect(22, 8, 4, 2);
  return c;
}

function buildConcreteTexture() {
  // 관공서 콘크리트 벽
  const c = makeCanvas(TEX_SIZE);
  const ctx = c.getContext('2d');
  for (let y = 0; y < TEX_SIZE; y++) {
    for (let x = 0; x < TEX_SIZE; x++) {
      const n = hashNoise(x, y, 2);
      const shade = 120 + n * 30;
      ctx.fillStyle = `rgb(${shade | 0},${shade | 0},${(shade - 4) | 0})`;
      ctx.fillRect(x, y, 1, 1);
    }
  }
  ctx.strokeStyle = 'rgba(60,60,58,0.8)';
  ctx.lineWidth = 1;
  ctx.strokeRect(0, 0, TEX_SIZE, TEX_SIZE / 2);
  ctx.strokeRect(0, TEX_SIZE / 2, TEX_SIZE, TEX_SIZE / 2);
  // 균열
  ctx.strokeStyle = 'rgba(40,38,36,0.9)';
  ctx.beginPath();
  ctx.moveTo(4, 0);
  ctx.lineTo(10, 14);
  ctx.lineTo(6, 30);
  ctx.stroke();
  return c;
}

function buildRubbleTexture() {
  // 포격으로 파괴된 잔해 벽
  const c = makeCanvas(TEX_SIZE);
  const ctx = c.getContext('2d');
  const block = 3;
  for (let y = 0; y < TEX_SIZE; y += block) {
    for (let x = 0; x < TEX_SIZE; x += block) {
      const n = hashNoise(x, y, 3);
      const shade = 55 + n * 55;
      ctx.fillStyle = `rgb(${shade | 0},${(shade * 0.9) | 0},${(shade * 0.85) | 0})`;
      ctx.fillRect(x, y, block, block);
    }
  }
  // 노출된 철근
  ctx.strokeStyle = 'rgba(120,70,50,0.7)';
  ctx.beginPath();
  ctx.moveTo(0, 10);
  ctx.lineTo(32, 6);
  ctx.moveTo(0, 22);
  ctx.lineTo(32, 26);
  ctx.stroke();
  return c;
}

function buildSandbagTexture() {
  // 국군 모래주머니 바리케이드
  const c = makeCanvas(TEX_SIZE);
  const ctx = c.getContext('2d');
  const rowH = TEX_SIZE / 6;
  for (let row = 0; row < 6; row++) {
    const y = row * rowH;
    const offset = (row % 2 === 0) ? 0 : rowH / 2;
    for (let x = -rowH; x < TEX_SIZE; x += rowH) {
      const n = hashNoise(x, row, 4);
      const shade = 0.85 + n * 0.25;
      const r = 194 * shade, g = 167 * shade, b = 107 * shade;
      ctx.fillStyle = `rgb(${r | 0},${g | 0},${b | 0})`;
      ctx.beginPath();
      ctx.ellipse(x + offset + rowH / 2, y + rowH / 2, rowH / 2 - 0.5, rowH / 2.4, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'rgba(70,55,30,0.6)';
      ctx.stroke();
    }
  }
  return c;
}

function buildMineFloorTexture() {
  const c = makeCanvas(TEX_SIZE);
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#3a352c';
  ctx.fillRect(0, 0, TEX_SIZE, TEX_SIZE);
  ctx.strokeStyle = 'rgba(200,40,30,0.85)';
  ctx.lineWidth = 2;
  ctx.strokeRect(6, 6, TEX_SIZE - 12, TEX_SIZE - 12);
  ctx.beginPath();
  ctx.moveTo(6, 6);
  ctx.lineTo(TEX_SIZE - 6, TEX_SIZE - 6);
  ctx.moveTo(TEX_SIZE - 6, 6);
  ctx.lineTo(6, TEX_SIZE - 6);
  ctx.stroke();
  return c;
}

const WALL_TEXTURES = {
  [TILE_BRICK]: buildBrickTexture(),
  [TILE_CONCRETE]: buildConcreteTexture(),
  [TILE_RUBBLE]: buildRubbleTexture(),
  [TILE_SANDBAG]: buildSandbagTexture(),
};
const MINE_FLOOR_TEXTURE = buildMineFloorTexture();

function getWallTexture(tileId) {
  return WALL_TEXTURES[tileId] || WALL_TEXTURES[TILE_CONCRETE];
}
