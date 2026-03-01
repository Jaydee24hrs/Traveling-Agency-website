document.addEventListener('DOMContentLoaded', function () {
    
    // Pagination Starts
    let currentPage = 1; 
    const rowsPerPage = 10;  
    const tableBody = document.querySelector('table tbody');
    const tableRows = Array.from(tableBody.querySelectorAll('tr'));
    const totalRows = tableRows.length;
    const totalPages = Math.ceil(totalRows / rowsPerPage);

    // Update the pagination info display
    function updatePaginationInfo() {
        document.getElementById('pagination-info-manage').textContent = `${currentPage} of ${totalPages}`;
        document.getElementById('prev-page-manage').style.display = (currentPage > 1) ? 'inline' : 'none';
        document.getElementById('next-page-manage').style.display = (currentPage < totalPages) ? 'inline' : 'none';
    }

    // Show rows for the current page
    function showPage(page) {
        const startRow = (page - 1) * rowsPerPage;
        const endRow = startRow + rowsPerPage;

        tableRows.forEach((row, index) => {
            row.style.display = (index >= startRow && index < endRow) ? 'table-row' : 'none';
        });
    }

    // Go to next page
    document.getElementById('next-page-manage').addEventListener('click', function () {
        if (currentPage < totalPages) {
            currentPage++;
            showPage(currentPage);
            updatePaginationInfo();
        }
    });

    // Go to previous page
    document.getElementById('prev-page-manage').addEventListener('click', function () {
        if (currentPage > 1) {
            currentPage--;
            showPage(currentPage);
            updatePaginationInfo();
        }
    });


    const statusCells = document.querySelectorAll(".statusClass");
    statusCells.forEach(function (cell) {
        const status = cell.textContent.trim().toLowerCase();
        if (status === "successful") {
            cell.classList.add("text-success");
        } else if (status === "pending") {
            cell.classList.add("text-warning");
        }
    });

    // Filter by Search
    document.getElementById('agencySearch').addEventListener('input', function () {
      const searchText = this.value.toLowerCase();
      const tableRows = document.querySelectorAll('#agency_table tr');
      tableRows.forEach(function (row) {
          const pnrCell = row.querySelector('.pnr'); 
          const customerName = row.querySelector('.customer'); 

          if (pnrCell && pnrCell) {
              const pnrText = pnrCell.textContent.toLowerCase();
              const customer = customerName.textContent.toLowerCase();
              row.style.display = pnrText.includes(searchText) || customer.includes(searchText) ? 'table-row' : 'none';
          }
        });

        updatePaginationInfo();

    });


    showPage(currentPage);
    updatePaginationInfo();


});
