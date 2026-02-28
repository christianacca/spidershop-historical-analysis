/**
 * Constants and Configuration Values
 * 
 * Centralizes all magic numbers, CSS class names, and configuration values
 * used across JavaScript modules.
 */

// SVG Chart Configuration
export const CHART = {
  WIDTH: 640,
  HEIGHT: 180,
  MARGINS: { left: 40, right: 620, top: 20, bottom: 150 },
  CIRCLE_RADIUS: 3.6,
  STROKE_WIDTH: 3,
  PRICE_ROUNDING: 5,
  WISHLIST_ROUNDING: 10
};

// CSS Classes
export const CSS = {
  ACTIVE: 'active',
  HIDDEN: 'hidden',
  SHOW: 'show',
  EXPANDED: 'expanded',
  FILTER_BTN: 'filter-btn'
};

// Configuration
export const CONFIG = {
  NUMERIC_DETECTION_SAMPLE_SIZE: 5
};
