function sortTable(columnIndex, tableId) {
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

function filterBySignal(signalType, tableId, button) {
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

function filterByStockPattern(patternType, tableId, button) {
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

function filterTable(searchInput, tableId) {
    const filter = searchInput.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');
    
    // Get price slider value (if exists)
    const priceSlider = document.getElementById('priceMax');
    const maxPrice = priceSlider ? parseFloat(priceSlider.value) : Infinity;
    
    // Get wishlist slider value (if exists)
    const wishlistSlider = document.getElementById('wishlistMax');
    const maxWishlist = wishlistSlider ? parseInt(wishlistSlider.value) : Infinity;
    
    rows.forEach(row => {
        // Check search filter
        const text = row.textContent.toLowerCase();
        const searchMatch = !filter || text.includes(filter);
        
        // Check price filter (if slider exists)
        let priceMatch = true;
        if (priceSlider) {
            const priceAttr = row.getAttribute('data-price');
            const price = priceAttr ? parseFloat(priceAttr.replace('£', '').trim()) : 0;
            priceMatch = price <= maxPrice;
        }
        
        // Check wishlist filter (if slider exists)
        let wishlistMatch = true;
        if (wishlistSlider) {
            const wishlistAttr = row.getAttribute('data-wishlist');
            const wishlist = wishlistAttr ? parseInt(wishlistAttr.trim()) : 0;
            wishlistMatch = wishlist <= maxWishlist;
        }
        
        // Show row only if all filters match (AND logic)
        if (searchMatch && priceMatch && wishlistMatch) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
    
    // Update filter badge count
    updateFilterBadge(tableId);
    
    // Update visible count
    updateVisibleCount(tableId);
}

/**
 * Filter table rows by price range
 * Hides rows where price is outside the min-max range
 */
function filterByPrice(tableId) {
    const minSlider = document.getElementById('priceMin');
    const maxSlider = document.getElementById('priceMax');
    const display = document.getElementById('priceDisplay');
    const table = document.getElementById(tableId);
    
    if (!minSlider || !maxSlider || !display || !table) return;
    
    // Get current values and ensure min <= max
    let minPrice = parseFloat(minSlider.value);
    let maxPrice = parseFloat(maxSlider.value);
    
    // Enforce min <= max constraint
    if (minPrice > maxPrice) {
        if (event && event.target === minSlider) {
            minPrice = maxPrice;
            minSlider.value = maxPrice;
        } else {
            maxPrice = minPrice;
            maxSlider.value = minPrice;
        }
    }
    
    // Update display text
    display.textContent = `Showing: £${Math.round(minPrice)} - £${Math.round(maxPrice)}`;
    
    // Get search filter value (if exists)
    const searchBox = document.getElementById('search-' + tableId);
    const searchFilter = searchBox ? searchBox.value.toLowerCase() : '';
    
    // Get wishlist filter values (if exists)
    const wishlistMinSlider = document.getElementById('wishlistMin');
    const wishlistMaxSlider = document.getElementById('wishlistMax');
    const minWishlist = wishlistMinSlider ? parseInt(wishlistMinSlider.value) : 0;
    const maxWishlist = wishlistMaxSlider ? parseInt(wishlistMaxSlider.value) : Infinity;
    
    // Filter rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const priceAttr = row.getAttribute('data-price');
        const price = priceAttr ? parseFloat(priceAttr.replace('£', '').trim()) : 0;
        
        const wishlistAttr = row.getAttribute('data-wishlist');
        const wishlist = wishlistAttr ? parseInt(wishlistAttr.trim()) : 0;
        
        // Check price filter (must be within range)
        const priceMatch = price >= minPrice && price <= maxPrice;
        
        // Check wishlist filter (must be within range)
        const wishlistMatch = wishlist >= minWishlist && wishlist <= maxWishlist;
        
        // Check search filter (if active)
        const text = row.textContent.toLowerCase();
        const searchMatch = !searchFilter || text.includes(searchFilter);
        
        // Show row only if all filters match (AND logic)
        if (priceMatch && wishlistMatch && searchMatch) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
    
    // Update filter badge and visible count
    updateFilterBadge(tableId);
    updateVisibleCount(tableId);
}

/**
 * Filter table rows by wishlist count range
 * Hides rows where wishlist count is outside the min-max range
 */
function filterByWishlist(tableId) {
    const minSlider = document.getElementById('wishlistMin');
    const maxSlider = document.getElementById('wishlistMax');
    const display = document.getElementById('wishlistDisplay');
    const table = document.getElementById(tableId);
    
    if (!minSlider || !maxSlider || !display || !table) return;
    
    // Get current values and ensure min <= max
    let minWishlist = parseInt(minSlider.value);
    let maxWishlist = parseInt(maxSlider.value);
    
    // Enforce min <= max constraint
    if (minWishlist > maxWishlist) {
        if (event && event.target === minSlider) {
            minWishlist = maxWishlist;
            minSlider.value = maxWishlist;
        } else {
            maxWishlist = minWishlist;
            maxSlider.value = minWishlist;
        }
    }
    
    // Update display text
    display.textContent = `Showing: ${minWishlist} - ${maxWishlist}`;
    
    // Get search filter value (if exists)
    const searchBox = document.getElementById('search-' + tableId);
    const searchFilter = searchBox ? searchBox.value.toLowerCase() : '';
    
    // Get price filter values (if exists)
    const priceMinSlider = document.getElementById('priceMin');
    const priceMaxSlider = document.getElementById('priceMax');
    const minPrice = priceMinSlider ? parseFloat(priceMinSlider.value) : 0;
    const maxPrice = priceMaxSlider ? parseFloat(priceMaxSlider.value) : Infinity;
    
    // Filter rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const wishlistAttr = row.getAttribute('data-wishlist');
        const wishlist = wishlistAttr ? parseInt(wishlistAttr.trim()) : 0;
        
        const priceAttr = row.getAttribute('data-price');
        const price = priceAttr ? parseFloat(priceAttr.replace('£', '').trim()) : 0;
        
        // Check wishlist filter (must be within range)
        const wishlistMatch = wishlist >= minWishlist && wishlist <= maxWishlist;
        
        // Check price filter (must be within range)
        const priceMatch = price >= minPrice && price <= maxPrice;
        
        // Check search filter (if active)
        const text = row.textContent.toLowerCase();
        const searchMatch = !searchFilter || text.includes(searchFilter);
        
        // Show row only if all filters match (AND logic)
        if (wishlistMatch && priceMatch && searchMatch) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
    
    // Update filter badge and visible count
    updateFilterBadge(tableId);
    updateVisibleCount(tableId);
}

function toggleAdvancedFilters(contentId, toggleButton) {
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
