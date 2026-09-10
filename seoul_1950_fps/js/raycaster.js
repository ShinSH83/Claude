// raycaster.js - 울펜슈타인3D 방식 DDA 레이캐스팅 렌더러
const FOV = Math.PI / 3; // 60도

function renderScene(ctx, screenW, screenH) {
  ctx.imageSmoothingEnabled = false;

  // 하늘(연기 자욱한 서울 상공)과 바닥(아스팔트/흙) - 위아래 절반
  const horizon = screenH / 2;
  ctx.fillStyle = '#4a3b35';
  ctx.fillRect(0, 0, screenW, horizon);
  ctx.fillStyle = '#2e2b24';
  ctx.fillRect(0, horizon, screenW, screenH - horizon);

  const rayCount = screenW;
  for (let col = 0; col < rayCount; col++) {
    const cameraX = (2 * col) / rayCount - 1; // -1 .. 1
    const rayAngle = player.angle + Math.atan(cameraX * Math.tan(FOV / 2));
    const rayDirX = Math.cos(rayAngle);
    const rayDirY = Math.sin(rayAngle);

    let mapX = Math.floor(player.x);
    let mapY = Math.floor(player.y);

    const deltaDistX = rayDirX === 0 ? 1e30 : Math.abs(1 / rayDirX);
    const deltaDistY = rayDirY === 0 ? 1e30 : Math.abs(1 / rayDirY);

    let stepX, sideDistX;
    if (rayDirX < 0) {
      stepX = -1;
      sideDistX = (player.x - mapX) * deltaDistX;
    } else {
      stepX = 1;
      sideDistX = (mapX + 1 - player.x) * deltaDistX;
    }
    let stepY, sideDistY;
    if (rayDirY < 0) {
      stepY = -1;
      sideDistY = (player.y - mapY) * deltaDistY;
    } else {
      stepY = 1;
      sideDistY = (mapY + 1 - player.y) * deltaDistY;
    }

    let hit = 0;
    let side = 0; // 0 = x면, 1 = y면
    let tile = 0;
    let guard = 0;
    while (hit === 0 && guard < 64) {
      guard++;
      if (sideDistX < sideDistY) {
        sideDistX += deltaDistX;
        mapX += stepX;
        side = 0;
      } else {
        sideDistY += deltaDistY;
        mapY += stepY;
        side = 1;
      }
      tile = getTile(mapX, mapY);
      if (isWallTile(tile)) hit = 1;
    }

    let perpDist;
    if (side === 0) {
      perpDist = (mapX - player.x + (1 - stepX) / 2) / rayDirX;
    } else {
      perpDist = (mapY - player.y + (1 - stepY) / 2) / rayDirY;
    }
    perpDist = Math.max(perpDist, 0.0001);

    const lineHeight = Math.floor(screenH / perpDist);
    let drawStart = Math.floor(-lineHeight / 2 + horizon);
    let drawEnd = Math.floor(lineHeight / 2 + horizon);
    if (drawStart < 0) drawStart = 0;
    if (drawEnd >= screenH) drawEnd = screenH - 1;

    // 벽에 부딪힌 지점의 텍스처 X 좌표
    let wallX;
    if (side === 0) wallX = player.y + perpDist * rayDirY;
    else wallX = player.x + perpDist * rayDirX;
    wallX -= Math.floor(wallX);

    const texture = getWallTexture(tile);
    let texX = Math.floor(wallX * TEX_SIZE);
    if ((side === 0 && rayDirX > 0) || (side === 1 && rayDirY < 0)) {
      texX = TEX_SIZE - texX - 1;
    }
    texX = Math.max(0, Math.min(TEX_SIZE - 1, texX));

    ctx.drawImage(
      texture,
      texX, 0, 1, TEX_SIZE,
      col, drawStart, 1, drawEnd - drawStart + 1
    );

    // 거리 기반 안개(그림자) 효과 - 픽셀아트풍 감쇠
    const fog = Math.min(0.85, perpDist / 14);
    const sideDarken = side === 1 ? 0.18 : 0; // 남/북면과 동/서면 명암 차이
    const alpha = Math.min(0.9, fog + sideDarken);
    if (alpha > 0.02) {
      ctx.fillStyle = `rgba(10,8,6,${alpha})`;
      ctx.fillRect(col, drawStart, 1, drawEnd - drawStart + 1);
    }
  }

  // 지뢰 피격 시 붉은 섬광
  const sinceFlash = performance.now() - player.lastMineFlashTime;
  if (sinceFlash < 250) {
    ctx.fillStyle = `rgba(180,20,10,${0.5 * (1 - sinceFlash / 250)})`;
    ctx.fillRect(0, 0, screenW, screenH);
  }
}
