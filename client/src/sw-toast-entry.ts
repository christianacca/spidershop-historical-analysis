import { mount } from 'svelte';
import SwUpdateToast from './shared/components/SwUpdateToast.svelte';
import { useRegisterSW } from './shared/register-sw';

// Compute the SW URL at runtime from import.meta.url so it is correct in every
// hosting context — local dev (http://localhost:PORT/sw.js) and GitHub Pages
// subpath deployment (https://…/spidershop-historical-analysis/sw.js) alike.
// A hardcoded '/sw.js' would 404 on GitHub Pages because the site is not served
// from the domain root.
//
// /* @vite-ignore */ prevents Vite from transforming this at build time.
// Without it, Vite replaces './sw.js' with a base64 data URI of the SW source
// (its asset-inlining heuristic treats new URL(literal, import.meta.url) as an
// asset reference). We need the URL to stay as a runtime-resolved path.
//
// Guard: only mount when SW is supported. Without this guard, useRegisterSW()
// accesses navigator.serviceWorker and can throw in environments where SW is
// unsupported or blocked (private browsing on some mobile browsers). The page
// must function identically without the toast.
const el = document.getElementById('sw-update-toast-root');
if (el && 'serviceWorker' in navigator) {
  const swUrl = new URL(/* @vite-ignore */ './sw.js', import.meta.url).href;
  const { needRefresh, updateServiceWorker } = useRegisterSW(swUrl);
  mount(SwUpdateToast, { target: el, props: { needRefresh, updateServiceWorker } });
}
