import { defineConfig, type UserConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { resolve } from 'path';

function createRollupOutput(isCiBuild: boolean) {
  const baseOutput = {
    format: 'es' as const,
    entryFileNames: '[name].js',
  };

  if (isCiBuild) {
    return {
      ...baseOutput,
      chunkFileNames: 'chunks/[name]-[hash].js',
      assetFileNames: 'assets/[name]-[hash][extname]',
    };
  }

  return {
    ...baseOutput,
    preserveModules: true,
    preserveModulesRoot: resolve(__dirname, 'src'),
    chunkFileNames: '[name].js',
    assetFileNames: 'assets/[name][extname]',
  };
}

// Phase 2: reorganised into feature-slice folders.
// One entry per page slice; shared/ utilities are internal imports only.
// Local builds preserve modules for readability.
// CI builds bundle shared code into chunks to reduce production request fan-out.
export function createViteConfig(isCiBuild = !!process.env.CI): UserConfig {
  return {
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
      // Thresholds ratcheted after post-migration hardening phases 2–7.
      // lines/statements measured at 96.9%; set to 95 (rounded down to nearest 5%).
      // branches: 86.18% → 85; functions: 94.36% → 90.
      thresholds: { branches: 85, functions: 90, lines: 95, statements: 95 },
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
    minify: isCiBuild ? 'esbuild' : false,
    sourcemap: isCiBuild,
    rollupOptions: {
      input: {
        'breeder-page': resolve(__dirname, 'src/breeder-page/index.ts'),
        'dealer-page': resolve(__dirname, 'src/dealer-page/index.ts'),
        'snapshot-page': resolve(__dirname, 'src/snapshot-page/index.ts'),
        'history-page': resolve(__dirname, 'src/history-page/index.ts'),
        'species-page': resolve(__dirname, 'src/species-page/index.ts'),
      },
      output: createRollupOutput(isCiBuild),
    },
  },
  };
}

export default defineConfig(createViteConfig());
