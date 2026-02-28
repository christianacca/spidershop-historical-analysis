import { defineConfig } from 'vite';
import { resolve } from 'path';

// Phase 1: entry points updated from .js → .ts after TypeScript migration.
// preserveModules keeps each module as its own file in dist/,
// maintaining relative imports — output is structurally identical to source.
// build.lib is intentionally avoided here: it bundles entries together,
// which would break the singleton state shared between table-interactions.ts
// and table-setup.ts when both are loaded on the same page.
export default defineConfig({
  build: {
    outDir: resolve(__dirname, '../templates/scripts/dist'),
    emptyOutDir: true,
    minify: false,
    rollupOptions: {
      // preserveModules requires preserveEntrySignatures !== false (Vite 6 default)
      preserveEntrySignatures: 'allow-extension',
      input: {
        constants: resolve(__dirname, 'src/constants.ts'),
        utils: resolve(__dirname, 'src/utils.ts'),
        'table-interactions': resolve(__dirname, 'src/table-interactions.ts'),
        'table-setup': resolve(__dirname, 'src/table-setup.ts'),
        'species-detail': resolve(__dirname, 'src/species-detail.ts'),
      },
      output: {
        format: 'es',
        preserveModules: true,
        preserveModulesRoot: resolve(__dirname, 'src'),
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
      },
    },
  },
});
