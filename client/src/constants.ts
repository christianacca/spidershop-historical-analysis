/**
 * Constants and Configuration Values
 * 
 * Centralizes all magic numbers, CSS class names, and configuration values
 * used across JavaScript modules.
 */

// SVG Chart Configuration
interface ChartConfig {
  WIDTH: number;
  HEIGHT: number;
  MARGINS: { left: number; right: number; top: number; bottom: number };
  CIRCLE_RADIUS: number;
  STROKE_WIDTH: number;
  PRICE_ROUNDING: number;
  WISHLIST_ROUNDING: number;
}

// CSS Classes
interface CssClasses {
  ACTIVE: string;
  HIDDEN: string;
  SHOW: string;
  EXPANDED: string;
  FILTER_BTN: string;
}

// Configuration
interface AppConfig {
  NUMERIC_DETECTION_SAMPLE_SIZE: number;
}

export const CHART: ChartConfig = {
  WIDTH: 640,
  HEIGHT: 180,
  MARGINS: { left: 40, right: 620, top: 20, bottom: 150 },
  CIRCLE_RADIUS: 3.6,
  STROKE_WIDTH: 3,
  PRICE_ROUNDING: 5,
  WISHLIST_ROUNDING: 10
};

export const CSS: CssClasses = {
  ACTIVE: 'active',
  HIDDEN: 'hidden',
  SHOW: 'show',
  EXPANDED: 'expanded',
  FILTER_BTN: 'filter-btn'
};

export const CONFIG: AppConfig = {
  NUMERIC_DETECTION_SAMPLE_SIZE: 5
};
