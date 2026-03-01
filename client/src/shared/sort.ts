/**
 * Table Sorting
 *
 * Sorts a table by a given column index.
 */

import { CONFIG } from './constants.js';
import { getElement } from './dom-utils.js';

/**
 * Sort table by column index
 */
export function sortTable(columnIndex: number, tableId: string): void {
  const table = getElement(tableId);
  if (!table) return;

  const tbody = table.querySelector('tbody');
  if (!tbody) return;
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const headers = table.querySelectorAll('th');

  // Bounds check
  if (columnIndex < 0 || columnIndex >= headers.length) {
    console.warn(`Invalid column index: ${columnIndex}`);
    return;
  }

  // Determine if column is numeric by sampling first few rows
  let isNumeric = true;
  for (let i = 0; i < Math.min(CONFIG.NUMERIC_DETECTION_SAMPLE_SIZE, rows.length); i++) {
    const cellText = rows[i].cells[columnIndex].textContent?.trim() ?? '';
    if (cellText && isNaN(parseFloat(cellText.replace(/[^0-9.-]/g, '')))) {
      isNumeric = false;
      break;
    }
  }

  // Get current sort direction and toggle
  const header = headers[columnIndex];
  const currentDirection = header.getAttribute('data-sort-direction') ?? 'asc';
  const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

  // Clear all sort indicators
  headers.forEach(th => th.removeAttribute('data-sort-direction'));

  // Set new sort direction
  header.setAttribute('data-sort-direction', newDirection);

  // Sort rows
  rows.sort((a, b) => {
    const aText = a.cells[columnIndex].textContent?.trim() ?? '';
    const bText = b.cells[columnIndex].textContent?.trim() ?? '';

    if (isNumeric) {
      const aValue = parseFloat(aText.replace(/[^0-9.-]/g, '')) || 0;
      const bValue = parseFloat(bText.replace(/[^0-9.-]/g, '')) || 0;
      return newDirection === 'asc' ? aValue - bValue : bValue - aValue;
    }

    const aLower = aText.toLowerCase();
    const bLower = bText.toLowerCase();
    return newDirection === 'asc' ? aLower.localeCompare(bLower) : bLower.localeCompare(aLower);
  });

  // Reappend sorted rows
  rows.forEach(row => tbody.appendChild(row));
}
