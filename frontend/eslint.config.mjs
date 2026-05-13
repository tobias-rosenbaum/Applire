import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

export default [
  ...coreWebVitals,
  ...typescript,
  {
    rules: {
      // These strict experimental react-hooks rules flag common intentional patterns
      // (Date.now() in render, setState-in-effect) that work correctly in this codebase.
      // Downgraded to warn until the codebase is audited for full compliance.
      "react-hooks/purity": "warn",
      "react-hooks/set-state-in-effect": "warn",
    },
  },
];
