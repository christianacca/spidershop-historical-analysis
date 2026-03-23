import { describe, expect, it } from 'vitest';

import '../../../templates/common.css';
import '../../../templates/analysis.css';
import { tokenRgb } from '../test-utils/token-colors';

describe('Methodology tabs visual contract', () => {
  it('uses accent styling for the active tab button', () => {
    document.body.innerHTML = `
      <button class="methodology-tab is-active" type="button">Threshold Inventory</button>
    `;

    const tab = document.querySelector('button') as HTMLElement;
    const styles = window.getComputedStyle(tab);

    expect(styles.backgroundColor).toBe(tokenRgb('--color-accent'));
    expect(styles.color).toBe('rgb(255, 255, 255)');
  });

  it('keeps the methodology shell and cards visually flat', () => {
    document.body.innerHTML = `
      <section class="analysis-methodology">
        <section class="threshold-card">
          <h4>Stock Pattern Rules</h4>
        </section>
      </section>
    `;

    const methodology = document.querySelector('.analysis-methodology') as HTMLElement;
    const card = document.querySelector('.threshold-card') as HTMLElement;
    const methodologyStyles = window.getComputedStyle(methodology);
    const cardStyles = window.getComputedStyle(card);

    expect(methodologyStyles.boxShadow).toBe('none');
    expect(cardStyles.boxShadow).toBe('none');
    expect(cardStyles.backgroundColor).toBe(tokenRgb('--color-surface-light'));
    expect(methodologyStyles.borderRadius).toBe('8px');
    expect(cardStyles.borderRadius).toBe('8px');
  });

  it('uses a native summary row for the collapsible header', () => {
    document.body.innerHTML = `
      <details class="analysis-methodology">
        <summary class="analysis-methodology__summary">How the breeder analysis works</summary>
      </details>
    `;

    const summary = document.querySelector('.analysis-methodology__summary') as HTMLElement;
    const styles = window.getComputedStyle(summary);

    expect(styles.display).toBe('list-item');
    expect(styles.paddingTop).toBe('10px');
    expect(styles.paddingBottom).toBe('10px');
  });

  it('does not add extra inner padding to the expanded methodology body', () => {
    document.body.innerHTML = `
      <details class="analysis-methodology" open>
        <summary class="analysis-methodology__summary">How the breeder analysis works</summary>
        <div class="analysis-methodology__content">
          <p class="analysis-methodology__intro">Conservative scoring keeps the signal stable.</p>
        </div>
      </details>
    `;

    const content = document.querySelector('.analysis-methodology__content') as HTMLElement;
    const styles = window.getComputedStyle(content);

    expect(styles.paddingLeft).toBe('0px');
    expect(styles.paddingRight).toBe('0px');
    expect(styles.paddingBottom).toBe('0px');
  });
});