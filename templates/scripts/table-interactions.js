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
}

function filterTable(searchInput, tableId) {
    const filter = searchInput.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
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
