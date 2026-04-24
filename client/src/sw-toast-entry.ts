import { mount } from 'svelte';
import SwUpdateToast from './shared/components/SwUpdateToast.svelte';

// Guard: only mount when SW is supported. Without this guard, useRegisterSW()
// inside SwUpdateToast accesses navigator.serviceWorker and can throw in
// environments where SW is unsupported or blocked (private browsing on some
// mobile browsers). The page must function identically without the toast.
const el = document.getElementById('sw-update-toast-root');
if (el && 'serviceWorker' in navigator) {
  mount(SwUpdateToast, { target: el });
}
