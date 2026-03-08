import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { resolve } from 'path';

// Phase 2: reorganised into feature-slice folders.
// One entry per page slice; shared/ utilities are internal imports only.
// preserveModules keeps each module as its own file in dist/,
// maintaining relative imports — output is structurally identical to source.
export default defineConfig({
  // emitCss: false — component styles are injected into <head> at runtime by
  // the JS module that owns them. This means no separate .css files are emitted
  // for Svelte components, so page templates never need to add <link> tags when
  // a new component is introduced or an existing component gains a new dependency.
  plugins: [svelte({ emitCss: false })],
  // Ensure Svelte resolves its browser (DOM) entry conditions for both
  // the build output and the Vitest test environment.
  resolve: {
    conditions: ['browser'],
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['src/test-setup.ts'],
    // Exclude browser-backed visual contract tests: they run via a separate
    // Vitest Browser Mode config (vite.browser.config.ts) and must not
    // distort the logic-coverage gate enforced by `make test-client`.
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      'src/**/*.visual.test.ts',
    ],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,svelte}'],
      exclude: [
        'src/test-setup.ts',
        'src/global.d.ts',
        'src/**/*.test.ts',
        // Browser-backed visual test files: run via vite.browser.config.ts,
        // not in the happy-dom suite. Must not distort logic-coverage numbers.
        'src/**/*.visual.test.ts',
        'src/test-utils/browser-setup.ts',
        'src/test-utils/token-colors.ts',
        // Page entry points: mount Svelte components against window globals and
        // DOM elements injected by the Python template. Only exercisable via E2E.
        'src/*/index.ts',
      ],
      // Thresholds start at 0 and are ratcheted upward phase-by-phase as
      // Svelte components are added and tested (plan phase 4c onwards).
      // Target: 80% across all four metrics once all modules have tests.
      thresholds: { branches: 80, functions: 80, lines: 0, statements: 0 },
      // Apply thresholds globally (not per-file) so early phases don't fail
      // before all modules have tests.
      perFile: false,
    },
  },
  build: {
    outDir: resolve(__dirname, '../templates/scripts/dist'),
    emptyOutDir: true,
    // Minify and emit source maps only in CI (GitHub Actions sets CI=true automatically).
    // Local builds stay readable for easier debugging.
    minify: process.env.CI ? 'esbuild' : false,
    sourcemap: !!process.env.CI,
    rollupOptions: {
      preserveEntrySignatures: 'allow-extension',
      input: {
        'breeder-page': resolve(__dirname, 'src/breeder-page/index.ts'),
        'dealer-page': resolve(__dirname, 'src/dealer-page/index.ts'),
        'snapshot-page': resolve(__dirname, 'src/snapshot-page/index.ts'),
        'history-page': resolve(__dirname, 'src/history-page/index.ts'),
        'species-page': resolve(__dirname, 'src/species-page/index.ts'),
      },
      output: {
        format: 'es',
        preserveModules: true,
        preserveModulesRoot: resolve(__dirname, 'src'),
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: 'assets/[name][extname]',
      },
    },
  },
});
