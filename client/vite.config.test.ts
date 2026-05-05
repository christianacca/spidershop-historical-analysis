import { describe, expect, it } from 'vitest';

import { createViteConfig } from './vite.config.js';

describe('createViteConfig', () => {
  it('preserves modules for local builds', () => {
    const config = createViteConfig(false);
    const output = config.build?.rollupOptions?.output;

    expect(output).toMatchObject({
      format: 'es',
      preserveModules: true,
      entryFileNames: '[name].js',
      chunkFileNames: '[name].js',
      assetFileNames: 'assets/[name][extname]',
    });
  });

  it('bundles shared code into hashed chunks for CI builds', () => {
    const config = createViteConfig(true);
    const output = config.build?.rollupOptions?.output;

    expect(output).toMatchObject({
      format: 'es',
      entryFileNames: '[name].js',
      chunkFileNames: 'chunks/[name]-[hash].js',
      assetFileNames: 'assets/[name]-[hash][extname]',
    });
    expect(output).not.toHaveProperty('preserveModules');
    expect(output).not.toHaveProperty('preserveModulesRoot');
  });

  it('includes view-transitions-entry in rollup inputs', () => {
    const config = createViteConfig();
    const inputs = config.build?.rollupOptions?.input as Record<string, string>;
    expect(inputs).toHaveProperty('view-transitions-entry');
  });

  it('excludes view-transitions-entry.ts from coverage', () => {
    const config = createViteConfig();
    const excluded = config.test?.coverage?.exclude as string[];
    expect(excluded).toContain('src/view-transitions-entry.ts');
  });
});