/**
 * Browser test setup — loads global CSS design tokens.
 *
 * Imported by vite.browser.config.ts setupFiles so that every visual test
 * starts with templates/common.css injected into the browser's document.
 * This makes all --custom-property tokens available via getComputedStyle().
 *
 * The import path escapes the client/ directory (server.fs.allow is set in
 * vite.browser.config.ts to permit this).
 */
import '../../../templates/common.css';
