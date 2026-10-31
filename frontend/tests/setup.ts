import '@testing-library/jest-dom';

// Comprehensive JSDOM canvas 2D mock for ECharts & ZRender
if (typeof window !== 'undefined') {
  const dummyCtx: Record<string, unknown> = {
    canvas: document.createElement('canvas'),
    fillRect: () => {},
    clearRect: () => {},
    getImageData: () => ({ data: [] }),
    putImageData: () => {},
    createImageData: () => [],
    setTransform: () => {},
    resetTransform: () => {},
    drawImage: () => {},
    save: () => {},
    fillText: () => {},
    strokeText: () => {},
    restore: () => {},
    beginPath: () => {},
    moveTo: () => {},
    lineTo: () => {},
    closePath: () => {},
    stroke: () => {},
    translate: () => {},
    scale: () => {},
    rotate: () => {},
    arc: () => {},
    arcTo: () => {},
    bezierCurveTo: () => {},
    quadraticCurveTo: () => {},
    fill: () => {},
    measureText: () => ({ width: 0, height: 0 }),
    transform: () => {},
    rect: () => {},
    clip: () => {},
    isPointInPath: () => false,
    createLinearGradient: () => ({
      addColorStop: () => {},
    }),
    createRadialGradient: () => ({
      addColorStop: () => {},
    }),
    createPattern: () => null,
  };

  const canvasContextProxy = new Proxy(dummyCtx, {
    get(target, prop: string) {
      if (prop in target) {
        return target[prop];
      }
      return () => {};
    },
    set(target, prop: string, value) {
      target[prop] = value;
      return true;
    },
  });

  (HTMLCanvasElement.prototype.getContext as unknown) = function () {
    return canvasContextProxy as unknown as CanvasRenderingContext2D;
  };

  // Mock global ResizeObserver for ECharts container responsiveness
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
