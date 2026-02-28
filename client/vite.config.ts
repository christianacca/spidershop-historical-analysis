import { defineConfig } from 'vite';
import { resolve } from 'path';

// Phase 2: reorganised into feature-slice folders.
// One entry per page slice; shared/ utilities are internal imports only.
// preserveModules keeps each module as its own file in dist/,
// maintaining relative imports — output is structurally identical to source.
export default defineConfig({
  build: {
    outDir: resolve(__dirname, '../templates/scripts/dist'),
    emptyOutDir: true,
    minify: false,
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
      },
    },
  },
});
