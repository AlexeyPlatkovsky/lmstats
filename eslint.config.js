import js from "@eslint/js";
import globals from "globals";

export default [
  {
    ignores: ["test/npm/**", "scripts/**", "node_modules/**"],
  },
  {
    files: ["lmstats/static/**/*.js"],
    ...js.configs.recommended,
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "script",
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
    rules: {
      "no-empty": ["error", { allowEmptyCatch: true }],
    },
  },
];
