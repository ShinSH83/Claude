// hud.js - 체력 게이지, 무기(M1 개런드) 표시, 조준점 등 HUD (울펜슈타인3D 스타일)
const weaponState = {
  name: 'M1 개런드',
  clipSize: 8, // M1 개런드 8발 클립 (1950년 국군/미군 표준 보병 소총)
  ammoInClip: 8,
};

function drawCrosshair(ctx, screenW, screenH) {
  const cx = screenW / 2;
  const cy = screenH / 2;
  ctx.strokeStyle = 'rgba(255,255,255,0.8)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx - 5, cy);
  ctx.lineTo(cx - 2, cy);
  ctx.moveTo(cx + 2, cy);
  ctx.lineTo(cx + 5, cy);
  ctx.moveTo(cx, cy - 5);
  ctx.lineTo(cx, cy - 2);
  ctx.moveTo(cx, cy + 2);
  ctx.lineTo(cx, cy + 5);
  ctx.stroke();
}

function drawWeapon(ctx, screenW, screenH) {
  const bobX = Math.sin(player.bobPhase) * 6 * player.bobAmount;
  const bobY = Math.abs(Math.cos(player.bobPhase)) * 5 * player.bobAmount;
  const baseX = screenW / 2 + bobX;
  const baseY = screenH + bobY;

  ctx.save();
  ctx.translate(baseX, baseY);

  // 개머리판 (나무, 짙은 갈색)
  ctx.fillStyle = '#5c4423';
  ctx.fillRect(-14, -70, 28, 46);
  // 총열덮개 (올리브 드랍)
  ctx.fillStyle = '#4b5320';
  ctx.fillRect(-9, -118, 18, 54);
  // 총열 (금속)
  ctx.fillStyle = '#3a3a3a';
  ctx.fillRect(-4, -150, 8, 40);
  // 가늠쇠
  ctx.fillStyle = '#222';
  ctx.fillRect(-2, -152, 4, 4);

  ctx.restore();
}

function drawHealthBar(ctx, screenW, screenH) {
  const barW = 90;
  const barH = 12;
  const x = 10;
  const y = screenH - barH - 10;
  const pct = player.health / player.maxHealth;

  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.fillRect(x - 2, y - 12, barW + 4, barH + 24);

  let color;
  if (pct > 0.5) color = '#3fae4a';
  else if (pct > 0.25) color = '#d9b23c';
  else color = '#c92f2f';

  ctx.fillStyle = '#222';
  ctx.fillRect(x, y, barW, barH);
  ctx.fillStyle = color;
  ctx.fillRect(x, y, barW * Math.max(0, pct), barH);
  ctx.strokeStyle = '#ddd';
  ctx.strokeRect(x, y, barW, barH);

  ctx.fillStyle = '#fff';
  ctx.font = '10px monospace';
  ctx.fillText('체력', x, y - 3);
  ctx.fillText(`${Math.ceil(player.health)} / ${player.maxHealth}`, x, y + barH + 12);
}

function drawAmmoCounter(ctx, screenW, screenH) {
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.fillRect(screenW - 82, screenH - 36, 72, 30);
  ctx.fillStyle = '#fff';
  ctx.font = '10px monospace';
  ctx.fillText(weaponState.name, screenW - 76, screenH - 22);
  ctx.fillText(`탄약 ${weaponState.ammoInClip} / ${weaponState.clipSize}`, screenW - 76, screenH - 10);
}

function drawMineWarning(ctx, screenW) {
  const tile = getTile(player.x, player.y - 0.001);
  const nearMine =
    getTile(player.x + 1, player.y) === TILE_MINE ||
    getTile(player.x - 1, player.y) === TILE_MINE ||
    getTile(player.x, player.y + 1) === TILE_MINE ||
    getTile(player.x, player.y - 1) === TILE_MINE;
  if (nearMine) {
    ctx.fillStyle = '#ffcc33';
    ctx.font = 'bold 11px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('⚠ 지뢰 주의', screenW / 2, 20);
    ctx.textAlign = 'left';
  }
}

function drawHUD(ctx, screenW, screenH) {
  drawWeapon(ctx, screenW, screenH);
  drawCrosshair(ctx, screenW, screenH);
  drawHealthBar(ctx, screenW, screenH);
  drawAmmoCounter(ctx, screenW, screenH);
  drawMineWarning(ctx, screenW);
}
