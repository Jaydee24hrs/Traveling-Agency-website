document.addEventListener('DOMContentLoaded', function () {
  // Filter Select
  const filterSelect = document.querySelector('.filter_radio');
  const requestRadio = document.querySelector('.request_type_radio');
  const statusRadio = document.querySelector('.status_radio');

  filterSelect.addEventListener('change', function () {
      const selectedValue = filterSelect.value;
      requestRadio.style.display = selectedValue === 'request_type' ? 'flex' : 'none';
      statusRadio.style.display = selectedValue === 'status' ? 'flex' : 'none';
  });

  // Filter by Request Type
  function applyFilter(inputId) {
      document.getElementById(inputId).addEventListener('input', function () {
          const searchText = this.value.toLowerCase();
          const tableRows = document.querySelectorAll('table tbody tr');
          tableRows.forEach(function (row) {
              const currentRowText = row.querySelector('.rType').textContent.toLowerCase();
              row.style.display = currentRowText.includes(searchText) ? 'table-row' : 'none';
          });
      });
  }
  applyFilter('issuance');
  applyFilter('void');
  applyFilter('exchange');
  applyFilter('refund');
  applyFilter('other');



  // Filter by Status
  function filterByStatus(statusId) {
      const statusInput = document.getElementById(statusId);
      statusInput.addEventListener('change', function () {
          const selectedStatus = document.querySelector('input[name="status"]:checked').value;
          const tableRows = document.querySelectorAll('table tbody tr');
          tableRows.forEach(function (row) {
              const currentRowStatus = row.querySelector('.statusClass').textContent.trim().toLowerCase();
              row.style.display = selectedStatus === 'all' || currentRowStatus === selectedStatus ? 'table-row' : 'none';
          });
      });
  }
  filterByStatus('open');
  filterByStatus('progressing');
  filterByStatus('resolved');


  // Filter by Search
  document.getElementById('agencySearch').addEventListener('input', function () {
    const searchText = this.value.toLowerCase();
    const tableRows = document.querySelectorAll('#agency_table tr');
    tableRows.forEach(function (row) {
        const agentNameCell = row.querySelector('.agent_name');
        const pnrCell = row.querySelector('.pnr');
        const case_id = row.querySelector('.case_ID');

        if (agentNameCell && pnrCell) {
            const agentNameText = agentNameCell.textContent.toLowerCase();
            const pnrText = pnrCell.textContent.toLowerCase();
            const caseID = case_id.textContent.toLowerCase();
            row.style.display = agentNameText.includes(searchText) || pnrText.includes(searchText) || caseID.includes(searchText) ? 'table-row' : 'none';
        }
    });
    updateAgencyStatistics();
  });

  // Add classes based on status
  const statusCells = document.querySelectorAll(".statusClass");
  statusCells.forEach(function (cell) {
      const status = cell.textContent.trim().toLowerCase();
      if (status === "resolved") {
          cell.classList.add("text-success");
      } else if (status === "open") {
          cell.classList.add("text-warning");
      } else if (status === "in progress") {
          cell.classList.add("text-primary");
      }
  });

  // Filter Select Dropdown
  filterSelect.addEventListener('change', function () {
      const selectedValue = filterSelect.value;
      const tableRows = document.querySelectorAll('#agency_table tr');
      if (selectedValue === 'select') {
          tableRows.forEach(function (row) {
              row.style.display = 'table-row';
          });
      }
  });



  // Update agency statistics
  function updateAgencyStatistics() {
    const totalRequest = document.querySelectorAll('table tbody tr').length;
    document.getElementById('totalRequest').textContent = totalRequest;

    const openRequest = document.querySelectorAll('table tbody tr:has(td.text-warning)').length;
    document.getElementById('openRequest').textContent = openRequest;

    const progressingRequest = document.querySelectorAll('table tbody tr:has(td.text-primary)').length;
    document.getElementById('progressingRequest').textContent = progressingRequest;

    const resolvedRequest = document.querySelectorAll('table tbody tr:has(td.text-success)').length;
    document.getElementById('resolvedRequest').textContent = resolvedRequest;
  }
  updateAgencyStatistics();


});
