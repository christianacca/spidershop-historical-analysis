import { beforeEach, describe, expect, it } from 'vitest';

import { wireMethodologyTabs } from './dom-utils.js';

describe('wireMethodologyTabs', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <section id="methodology-section">
        <div class="methodology-tabs" role="tablist">
          <button class="tab-btn is-active" data-methodology-tab="thresholds" aria-selected="true">Threshold Inventory</button>
          <button class="tab-btn" data-methodology-tab="tree" aria-selected="false">Decision Tree</button>
          <button class="tab-btn" data-methodology-tab="example" aria-selected="false">Worked Example</button>
        </div>
        <div class="methodology-panels">
          <section class="methodology-panel is-active" data-methodology-panel="thresholds"></section>
          <section class="methodology-panel" data-methodology-panel="tree"></section>
          <section class="methodology-panel" data-methodology-panel="example"></section>
        </div>
      </section>
    `;
  });

  it('activates the matching panel and updates aria-selected when a tab is clicked', () => {
    wireMethodologyTabs();

    const treeTab = document.querySelector<HTMLButtonElement>('[data-methodology-tab="tree"]');
    const thresholdPanel = document.querySelector<HTMLElement>('[data-methodology-panel="thresholds"]');
    const treePanel = document.querySelector<HTMLElement>('[data-methodology-panel="tree"]');

    treeTab?.click();

    expect(treeTab).toHaveClass('is-active');
    expect(treeTab).toHaveAttribute('aria-selected', 'true');
    expect(thresholdPanel).not.toHaveClass('is-active');
    expect(treePanel).toHaveClass('is-active');
  });
});