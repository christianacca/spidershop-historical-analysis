export function sortTable(columnIndex, tableId) {
    const table = document.getElementById(tableId);
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine if column is numeric
    let isNumeric = true;
    for (let i = 0; i < Math.min(5, rows.length); i++) {
        const cellText = rows[i].cells[columnIndex].textContent.trim();
        if (cellText && isNaN(parseFloat(cellText.replace(/[^0-9.-]/g, '')))) {
            isNumeric = false;
            break;
        }
    }
    
    // Get current sort direction
    const header = table.querySelectorAll('th')[columnIndex];
    const currentDirection = header.getAttribute('data-sort-direction') || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    
    // Clear all sort indicators
    table.querySelectorAll('th').forEach(th => {
        th.removeAttribute('data-sort-direction');
    });
    
    // Set new sort direction
    header.setAttribute('data-sort-direction', newDirection);
    
    // Sort rows
    rows.sort((a, b) => {
        let aVal = a.cells[columnIndex].textContent.trim();
        let bVal = b.cells[columnIndex].textContent.trim();
        
        if (isNumeric) {
            aVal = parseFloat(aVal.replace(/[^0-9.-]/g, '')) || 0;
            bVal = parseFloat(bVal.replace(/[^0-9.-]/g, '')) || 0;
            return newDirection === 'asc' ? aVal - bVal : bVal - aVal;
        } else {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
            if (newDirection === 'asc') {
                return aVal.localeCompare(bVal);
            } else {
                return bVal.localeCompare(aVal);
            }
        }
    });
    
    // Reappend sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

export function filterBySignal(signalType, tableId, button) {
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    
    // Update button states
    const buttons = button.parentElement.getElementsByClassName('filter-btn');
    for (let btn of buttons) {
        btn.classList.remove('active');
    }
    button.classList.add('active');
    
    // Filter rows by signal
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const signal = row.getAttribute('data-signal');
        
        if (signalType === 'all' || signal === signalType) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
    
    // Update visible count
    updateVisibleCount(tableId);
}

export function filterByStockPattern(patternType, tableId, button) {
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    
    // Update button states
    const buttons = button.parentElement.getElementsByClassName('filter-btn');
    for (let btn of buttons) {
        btn.classList.remove('active');
    }
    button.classList.add('active');
    
    // Filter rows by stock pattern
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const stockPattern = row.getAttribute('data-stock-pattern');
        
        if (patternType === 'all' || stockPattern === patternType) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
    
    // Update visible count
    updateVisibleCount(tableId);
}

export function filterTable(searchInput, tableId) {
    applyAllFilters(tableId);
}

/**
 * Apply all active filters to table rows
 * Checks price, wishlist, and search filters together
 */
function applyAllFilters(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Get search filter value
    const searchBox = document.getElementById('search-' + tableId);
    const searchFilter = searchBox ? searchBox.value.toLowerCase() : '';
    
    // Get price filter values
    const priceMinSlider = document.getElementById('priceMin');
    const priceMaxSlider = document.getElementById('priceMax');
    const minPrice = priceMinSlider ? parseFloat(priceMinSlider.value) : 0;
    const maxPrice = priceMaxSlider ? parseFloat(priceMaxSlider.value) : Infinity;
    
    // Get wishlist filter values
    const wishlistMinSlider = document.getElementById('wishlistMin');
    const wishlistMaxSlider = document.getElementById('wishlistMax');
    const minWishlist = wishlistMinSlider ? parseInt(wishlistMinSlider.value) : 0;
    const maxWishlist = wishlistMaxSlider ? parseInt(wishlistMaxSlider.value) : Infinity;
    
    // Filter all rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        // Get row values
        const priceAttr = row.getAttribute('data-price');
        const price = priceAttr ? parseFloat(priceAttr.replace('£', '').trim()) : 0;
        
        const wishlistAttr = row.getAttribute('data-wishlist');
        const wishlist = wishlistAttr ? parseInt(wishlistAttr.trim()) : 0;
        
        const text = row.textContent.toLowerCase();
        
        // Check all filters
        const priceMatch = price >= minPrice && price <= maxPrice;
        const wishlistMatch = wishlist >= minWishlist && wishlist <= maxWishlist;
        const searchMatch = !searchFilter || text.includes(searchFilter);
        
        // Show row only if all filters match
        if (priceMatch && wishlistMatch && searchMatch) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
    
    updateFilterBadge(tableId);
    updateVisibleCount(tableId);
}

/**
 * Filter table rows by price range
 */
export function filterByPrice(tableId) {
    const minSlider = document.getElementById('priceMin');
    const maxSlider = document.getElementById('priceMax');
    const display = document.getElementById('priceDisplay');
    
    if (!minSlider || !maxSlider || !display) return;
    
    // Get current values and ensure min <= max
    let minPrice = parseFloat(minSlider.value);
    let maxPrice = parseFloat(maxSlider.value);
    
    if (minPrice > maxPrice) {
        if (event && event.target === minSlider) {
            minPrice = maxPrice;
            minSlider.value = maxPrice;
        } else {
            maxPrice = minPrice;
            maxSlider.value = minPrice;
        }
    }
    
    display.textContent = `Showing: £${Math.round(minPrice)} - £${Math.round(maxPrice)}`;
    applyAllFilters(tableId);
}

/**
 * Filter table rows by wishlist count range
 */
export function filterByWishlist(tableId) {
    const minSlider = document.getElementById('wishlistMin');
    const maxSlider = document.getElementById('wishlistMax');
    const display = document.getElementById('wishlistDisplay');
    
    if (!minSlider || !maxSlider || !display) return;
    
    // Get current values and ensure min <= max
    let minWishlist = parseInt(minSlider.value);
    let maxWishlist = parseInt(maxSlider.value);
    
    if (minWishlist > maxWishlist) {
        if (event && event.target === minSlider) {
            minWishlist = maxWishlist;
            minSlider.value = maxWishlist;
        } else {
            maxWishlist = minWishlist;
            maxSlider.value = minWishlist;
        }
    }
    
    display.textContent = `Showing: ${minWishlist} - ${maxWishlist}`;
    applyAllFilters(tableId);
}

export function toggleAdvancedFilters(contentId, toggleButton) {
    const content = document.getElementById(contentId);
    const isExpanded = content.classList.contains('show');
    
    if (isExpanded) {
        content.classList.remove('show');
        toggleButton.classList.remove('expanded');
    } else {
        content.classList.add('show');
        toggleButton.classList.add('expanded');
    }
}

/**
 * Update filter badge count for snapshot/history pages
 * Shows badge with count when filters are active
 */
function updateFilterBadge(tableId) {
    const badge = document.getElementById('filterBadge-' + tableId);
    if (!badge) return; // Badge might not exist on all pages
    
    // Count active filters
    let activeFilters = 0;
    
    // Check search filter
    const searchBox = document.getElementById('search-' + tableId);
    if (searchBox && searchBox.value.trim() !== '') {
        activeFilters++;
    }
    
    // Check price range sliders (active if min > data_min OR max < data_max)
    const priceMinSlider = document.getElementById('priceMin');
    const priceMaxSlider = document.getElementById('priceMax');
    if (priceMinSlider && priceMaxSlider) {
        const dataMin = parseFloat(priceMinSlider.getAttribute('min'));
        const dataMax = parseFloat(priceMaxSlider.getAttribute('max'));
        const currentMin = parseFloat(priceMinSlider.value);
        const currentMax = parseFloat(priceMaxSlider.value);
        if (currentMin > dataMin || currentMax < dataMax) {
            activeFilters++;
        }
    }
    
    // Check wishlist range sliders (active if min > data_min OR max < data_max)
    const wishlistMinSlider = document.getElementById('wishlistMin');
    const wishlistMaxSlider = document.getElementById('wishlistMax');
    if (wishlistMinSlider && wishlistMaxSlider) {
        const dataMin = parseInt(wishlistMinSlider.getAttribute('min'));
        const dataMax = parseInt(wishlistMaxSlider.getAttribute('max'));
        const currentMin = parseInt(wishlistMinSlider.value);
        const currentMax = parseInt(wishlistMaxSlider.value);
        if (currentMin > dataMin || currentMax < dataMax) {
            activeFilters++;
        }
    }
    
    // Update badge display
    if (activeFilters > 0) {
        badge.textContent = activeFilters;
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }
}

/**
 * Update visible count display for a table
 * Counts non-hidden rows and updates the stats strip
 */
function updateVisibleCount(tableId) {
    const countElement = document.getElementById('visible-count-' + tableId);
    if (!countElement) return; // Stats strip might not exist on all pages
    
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');
    
    let visibleCount = 0;
    rows.forEach(row => {
        // Check both hidden class and style.display for backwards compatibility
        if (!row.classList.contains('hidden') && row.style.display !== 'none') {
            visibleCount++;
        }
    });
    
    countElement.textContent = visibleCount;
}
