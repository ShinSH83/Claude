// main.js - 게임 루프 및 상태 관리 (시작 / 플레이 / 일시정지 / 게임오버)
(function () {
  const canvas = document.getElementById('game-canvas');
  const ctx = canvas.getContext('2d');
  const RENDER_W = 480;
  const RENDER_H = 270;
  canvas.width = RENDER_W;
  canvas.height = RENDER_H;

  const startScreen = document.getElementById('start-screen');
  const pauseScreen = document.getElementById('pause-screen');
  const gameOverScreen = document.getElementById('gameover-screen');
  const startBtn = document.getElementById('start-btn');
  const restartBtn = document.getElementById('restart-btn');

  let state = 'start'; // start | playing | paused | gameover
  let muzzleFlashUntil = -1;
  let reloading = false;

  setupInput(canvas, (locked) => {
    if (state === 'playing' && !locked) {
      state = 'paused';
      pauseScreen.classList.remove('hidden');
    }
  });

  window.addEventListener('mousedown', (e) => {
    if (state === 'playing' && pointerLocked && e.button === 0) {
      fireWeapon();
    }
  });
  window.addEventListener('keydown', (e) => {
    if (state === 'playing' && e.code === 'KeyR') {
      reloadWeapon();
    }
  });

  function fireWeapon() {
    if (reloading || weaponState.ammoInClip <= 0) return;
    weaponState.ammoInClip--;
    muzzleFlashUntil = performance.now() + 60;
  }

  function reloadWeapon() {
    if (reloading || weaponState.ammoInClip === weaponState.clipSize) return;
    reloading = true;
    setTimeout(() => {
      weaponState.ammoInClip = weaponState.clipSize;
      reloading = false;
    }, 900); // M1 개런드 클립 재장전 시간(연출용 근사치)
  }

  function beginGame() {
    resetPlayer();
    weaponState.ammoInClip = weaponState.clipSize;
    reloading = false;
    state = 'playing';
    startScreen.classList.add('hidden');
    pauseScreen.classList.add('hidden');
    gameOverScreen.classList.add('hidden');
    canvas.requestPointerLock();
  }

  startBtn.addEventListener('click', beginGame);
  restartBtn.addEventListener('click', beginGame);
  pauseScreen.addEventListener('click', () => {
    if (state === 'paused') canvas.requestPointerLock();
  });

  let lastTime = performance.now();

  function loop(now) {
    const dt = Math.min(0.05, (now - lastTime) / 1000);
    lastTime = now;

    if (state === 'playing') {
      const dx = consumeMouseDX();
      updatePlayer(dt, keys, dx);
    }

    if (state === 'playing' || state === 'paused') {
      renderScene(ctx, RENDER_W, RENDER_H);
      drawHUD(ctx, RENDER_W, RENDER_H);
      if (performance.now() < muzzleFlashUntil) {
        ctx.fillStyle = 'rgba(255, 230, 150, 0.25)';
        ctx.fillRect(0, 0, RENDER_W, RENDER_H);
      }
    }

    if (state === 'playing' && !player.alive) {
      state = 'gameover';
      gameOverScreen.classList.remove('hidden');
      document.exitPointerLock();
    }

    requestAnimationFrame(loop);
  }

  requestAnimationFrame(loop);
})();
