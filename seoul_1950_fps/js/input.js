// input.js - 키보드 / 마우스(포인터락) 입력 처리
const keys = {};
let mouseDX = 0;
let pointerLocked = false;

function setupInput(canvas, onLockChange) {
  window.addEventListener('keydown', (e) => {
    keys[e.code] = true;
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
      e.preventDefault();
    }
  });
  window.addEventListener('keyup', (e) => {
    keys[e.code] = false;
  });

  canvas.addEventListener('click', () => {
    if (document.pointerLockElement !== canvas) {
      canvas.requestPointerLock();
    }
  });

  document.addEventListener('pointerlockchange', () => {
    pointerLocked = document.pointerLockElement === canvas;
    if (onLockChange) onLockChange(pointerLocked);
  });

  document.addEventListener('mousemove', (e) => {
    if (pointerLocked) {
      mouseDX += e.movementX || 0;
    }
  });
}

function consumeMouseDX() {
  const v = mouseDX;
  mouseDX = 0;
  return v;
}
