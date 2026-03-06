import { sortRows } from './table-utils.js';

export class SortState {
  key = $state<string | null>(null);
  dir = $state<'asc' | 'desc'>('asc');

  toggle(newKey: string): void {
    if (this.key === newKey) {
      this.dir = this.dir === 'asc' ? 'desc' : 'asc';
    } else {
      this.key = newKey;
      this.dir = 'asc';
    }
  }

  apply(rows: Record<string, unknown>[]): Record<string, unknown>[] {
    return this.key === null ? rows : sortRows(rows, this.key, this.dir);
  }
}
