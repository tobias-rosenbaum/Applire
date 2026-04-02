import "@testing-library/jest-dom";

// jsdom does not implement ResizeObserver — stub it so components that use it can be tested
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
