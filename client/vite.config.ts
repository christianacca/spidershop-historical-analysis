import { defineConfig } from 'vite';
import { resolve } from 'path';

// Phase 0: five existing JS files as entry points.
// preserveModules keeps each module as its own file in dist/,
// maintaining relative imports — output is structurally identical to source.
// build.lib is intentionally avoided here: it bundles entries together,
// which would break the singleton state shared between table-interactions.js
// and table-setup.js when both are loaded on the same page.
export default defineConfig({
  build: {
    outDir: resolve(__dirname, '../templates/scripts/dist'),
    emptyOutDir: true,
    minify: false,
    rollupOptions: {
      // preserveModules requires preserveEntrySignatures !== false (Vite 6 default)
      preserveEntrySignatures: 'allow-extension',
      input: {
        constants: resolve(__dirname, 'src/constants.js'),
        utils: resolve(__dirname, 'src/utils.js'),
        'table-interactions': resolve(__dirname, 'src/table-interactions.js'),
        'table-setup': resolve(__dirname, 'src/table-setup.js'),
        'species-detail': resolve(__dirname, 'src/species-detail.js'),
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
