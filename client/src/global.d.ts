/**
 * Global type declarations for browser-injected data
 */

interface SpeciesRun {
  observed: boolean;
  price: string;
  wishlist: string;
}

interface SpeciesChartData {
  runs: SpeciesRun[];
}

interface Window {
  speciesChartData?: SpeciesChartData;
}
