/**
 * Vitest Browser Mode configuration — browser-backed visual contract tests.
 *
 * Separate from vite.config.ts so that:
 *   - Visual tests run in a real Chromium instance (required for
 *     getComputedStyle to resolve CSS custom properties).
 *   - Coverage metrics from visual tests do not distort the logic-coverage
 *     gate enforced by `make test-client`.
 *
 * Run with: make test-visual
 * Install browser binary once with: make visual-install
 */
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [svelte({ emitCss: false })],
  resolve: {
    // Ensure Svelte resolves its browser (DOM) entry conditions.
    conditions: ['browser'],
    alias: {
      // vite-plugin-pwa is not loaded in this config, so Vite cannot resolve
      // the real virtual module. Alias it to a local stub so that components
      // importing it are resolvable; vi.mock() in test files overrides the stub.
      'virtual:pwa-register/svelte': resolve(__dirname, 'src/test-utils/pwa-register-stub.ts'),
    },
  },
  // Allow Vite to serve files from the project root so that
  // templates/common.css can be imported by browser-setup.ts.
  server: {
    fs: {
      allow: [resolve(__dirname, '..')],
    },
  },
  // Pre-bundle @testing-library/svelte so Vite does not reload the browser
  // context mid-run when the dependency is first encountered by a test file.
  // Without this entry, the first test in each component file fails with
  // "Vite unexpectedly reloaded a test" and a TypeError from the reload.
  optimizeDeps: {
    include: ['@testing-library/svelte'],
  },
  test: {
    globals: true,
    // Browser mode: tests run inside a real Chromium instance via Playwright.
    // This is the only way to verify CSS custom-property resolution via
    // getComputedStyle() — happy-dom cannot resolve var(--token) references.
    browser: {
      enabled: true,
      provider: 'playwright',
      headless: true,
      instances: [{ browser: 'chromium' }],
    },
    // Load jest-dom matchers and inject global CSS design tokens into the page.
    setupFiles: ['src/test-setup.ts', 'src/test-utils/browser-setup.ts'],
    // Only run browser-backed visual contract tests from this config.
    // Naming convention: *.visual.test.ts
    include: ['src/**/*.visual.test.ts'],
    // Coverage disabled: visual tests exercise style rather than logic.
    // Including them would inflate logic-coverage numbers with browser-
    // instrumentation overhead and conceal true branch coverage gaps.
    coverage: {
      enabled: false,
    },
  },
});
