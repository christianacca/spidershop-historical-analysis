import { describe, expect, it } from 'vitest';

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
});