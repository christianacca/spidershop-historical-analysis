/**
 * Range Slider Component
 *
 * Manages min/max slider constraints and display updates.
 */

import { getElement } from './dom-utils.js';

export interface RangeSliderConfig {
  minId: string;
  maxId: string;
  displayId: string;
  parse: (value: string) => number;
  format: (min: number, max: number) => string;
}

export class RangeSlider {
  private minSlider: HTMLElement | null;
  private maxSlider: HTMLElement | null;
  private display: HTMLElement | null;
  private parse: (value: string) => number;
  private format: (min: number, max: number) => string;

  constructor(config: RangeSliderConfig) {
    this.minSlider = getElement(config.minId);
    this.maxSlider = getElement(config.maxId);
    this.display = getElement(config.displayId);
    this.parse = config.parse;
    this.format = config.format;
  }

  /**
   * Create a price slider with standard configuration
   */
  static createPriceSlider(): RangeSlider {
    return new RangeSlider({
      minId: 'priceMin',
      maxId: 'priceMax',
      displayId: 'priceDisplay',
      parse: parseFloat,
      format: (min, max) => `Showing: £${Math.round(min)} - £${Math.round(max)}`
    });
  }

  /**
   * Create a wishlist slider with standard configuration
   */
  static createWishlistSlider(): RangeSlider {
    return new RangeSlider({
      minId: 'wishlistMin',
      maxId: 'wishlistMax',
      displayId: 'wishlistDisplay',
      parse: parseInt,
      format: (min, max) => `Showing: ${min} - ${max}`
    });
  }

  /**
   * Enforce min <= max constraint when sliders change
   */
  enforceConstraints(event?: Event): void {
    if (!this.minSlider || !this.maxSlider) return;

    const minInput = this.minSlider as HTMLInputElement;
    const maxInput = this.maxSlider as HTMLInputElement;

    let min = this.parse(minInput.value);
    let max = this.parse(maxInput.value);

    if (min > max) {
      if (event?.target === this.minSlider) {
        min = max;
        minInput.value = String(max);
      } else {
        max = min;
        maxInput.value = String(min);
      }
    }

    this.updateDisplay(min, max);
  }

  /**
   * Get current slider values
   */
  getValues(): [number, number] {
    if (!this.minSlider || !this.maxSlider) return [0, Infinity];
    return [
      this.parse((this.minSlider as HTMLInputElement).value),
      this.parse((this.maxSlider as HTMLInputElement).value)
    ];
  }

  /**
   * Update display text with formatted values
   */
  updateDisplay(min: number, max: number): void {
    if (this.display) {
      this.display.textContent = this.format(min, max);
    }
  }
}
