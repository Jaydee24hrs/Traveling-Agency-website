$(document).ready(function() {
    let allRows = $('.airline_entry').clone(); // Clone all rows initially
    let filteredRows = [];
    const itemsPerPage = 4; // Number of items per page
    let currentPage = 1; // Current page number

    function applyFilters() {
    
        let rows = allRows; // Start with all rows, not just visible ones

        // Apply each filter function
        rows = filterByPrice(rows);
        rows = filterByStops(rows);
        rows = filterByAirline(rows);
        rows = filterByCabin(rows);
        rows = filterByFlexibility(rows);
        rows = filterByBaggages(rows);

        filteredRows = rows; // Store filtered rows

        if (filteredRows.length === 0) {
            document.getElementById('preloader2').style.display = 'none';
            return;
        }

        // Re-group, sort, and paginate after filtering
        setupPagination(filteredRows); // Set up pagination controls
        paginateGroups(filteredRows);  // Display paginated rows
        document.dispatchEvent(new Event('filteringComplete'));
    }

    function filterByPrice(rows) {
        const rangeInput = document.getElementById('filter_price_small');
        const maxPrice = parseInt(rangeInput.value);

        return rows.filter(function() {
            const priceTd = $(this).find('.flight_price');
            const priceText = priceTd.text().replace(/[₦,]/g, '').trim();
            // const priceText = priceTd.text().replace(/[₵,]/g, '').trim();
            const rowPrice = parseInt(priceText);
            return rowPrice <= maxPrice;
        });
    }

    function filterByStops(rows) {
        const nonStopChecked = $('#nonStop_small').is(':checked');
        const oneStopChecked = $('#oneStop_small').is(':checked');
        const twoStopsChecked = $('#twoStops_small').is(':checked');

        if (!nonStopChecked && !oneStopChecked && !twoStopsChecked) {
            return rows; // No filter applied
        }

        return rows.filter(function() {
            const stopsSpans = $(this).find('.stops_summary');
            let shouldShowRow = false;

            stopsSpans.each(function() {
                const stopsText = $(this).text().trim();
                if ((nonStopChecked && stopsText === 'Non Stop') ||
                    (oneStopChecked && stopsText === '1 Stop') ||
                    (twoStopsChecked && stopsText === '2 Stops')) {
                    shouldShowRow = true;
                    return false; // Break loop if match found
                }
            });

            return shouldShowRow;
        });
    }

    function filterByAirline(rows) {
        const airlineCheckboxes = $('.airline-checkbox:checked').map(function() {
            return $(this).val().toUpperCase();
        }).get();

        if (airlineCheckboxes.length === 0) {
            return rows; // No filter applied
        }

        return rows.filter(function() {
            const airlineNames = $(this).find('.airline_name').map(function() {
                return $(this).text().trim().toUpperCase();
            }).get();

            return airlineNames.some(airlineName => airlineCheckboxes.includes(airlineName));
        });
    }


    function filterByCabin(rows) {
        const economy = $('#economy_small').is(':checked');
        const premium = $('#premium_economy_small').is(':checked');
        const business = $('#businessClass_small').is(':checked');
        const first = $('#firstClass_small').is(':checked');


        if (!economy && !premium && !business && !first) {
            return rows; // No filter applied
        }

        return rows.filter(function() {
            const cabins = $(this).find('.cabin_filter');
            let shouldShowRow = false;

            cabins.each(function() {
                const cabin = $(this).text().trim();
                if ((economy && cabin === 'ECONOMY') ||
                    (premium && cabin === 'PREMIUM') ||
                    (business && cabin === 'BUSINESS') ||
                    (first && cabin === 'FIRST')) {
                    shouldShowRow = true;
                    return false; // Break loop if match found
                }
            });

            return shouldShowRow;
        });
    }
    

    function filterByFlexibility(rows) {
        const refundChecked = $('#refund_small').is(':checked');
        const noRefundChecked = $('#noRefund_small').is(':checked');

        if (!refundChecked && !noRefundChecked ) {
            return rows; // No filter applied
        }

        return rows.filter(function() {
            const flexibilities = $(this).find('.flexibility_filter');
            let shouldShowRow = false;

            flexibilities.each(function() {
                const flexibility = $(this).text().trim();
                if ((refundChecked && flexibility === 'Refundable') ||
                    (noRefundChecked && flexibility === 'Non Refundable')) {
                    shouldShowRow = true;
                    return false; // Break loop if match found
                }
            });

            return shouldShowRow;
        });
    }
    

    function filterByBaggages(rows) {
        const zeroBaggageChecked = $('#checkin0_small').is(':checked');
        const oneBaggageChecked = $('#checkin1_small').is(':checked');

        if (!zeroBaggageChecked && !oneBaggageChecked) {
            return rows; // No filter applied
        }

        return rows.filter(function() {
            const baggages = $(this).find('.baggages_filter');
            let shouldShowRow = false;

            baggages.each(function() {
                const baggageText = $(this).text().trim();
                if ((zeroBaggageChecked && (baggageText === '0 PC' || baggageText === '0kg')) ||
                    (oneBaggageChecked && baggageText !== '0 PC' && baggageText !== '0kg')) {
                    shouldShowRow = true;
                    return false; // Break loop if match found
                }
            });

            return shouldShowRow;
        });
    }


    // Function to display rows for the current page
    function paginateGroups(filteredRows = []) {
        let rowsToPaginate = filteredRows.length ? filteredRows : rows;

        $('#flight_result_table2 tbody').empty();  // Clear current table contents

        let startIndex = (currentPage - 1) * itemsPerPage;
        let endIndex = Math.min(startIndex + itemsPerPage, rowsToPaginate.length);
        let paginatedRows = rowsToPaginate.slice(startIndex, endIndex);

        $('#flight_result_table2 tbody').append(paginatedRows);  // Append the rows for the current page
    }

    // Function to setup pagination controls
    function setupPagination(filteredRows = []) {
        let rowsToPaginate = filteredRows.length ? filteredRows : rows;
        let totalPages = Math.ceil(rowsToPaginate.length / itemsPerPage);

        $('#pagination').empty();  // Clear existing pagination controls

        if (totalPages <= 1) return;  // No need for pagination if there's only one page

        // Previous button
        $('#pagination').append(`
            <li class="page-item${currentPage === 1 ? ' disabled' : ''}">
                <a class="page-link" href="#" aria-label="Previous" data-page="${currentPage - 1}">
                    <span aria-hidden="true">&laquo; Previous</span>
                </a>
            </li>
        `);

        // Display current page and total pages
        $('#pagination').append(`
            <li class="page-item disabled">
                <span class="page-link">${currentPage} of ${totalPages}</span>
            </li>
        `);

        // Next button
        $('#pagination').append(`
            <li class="page-item${currentPage === totalPages ? ' disabled' : ''}">
                <a class="page-link" href="#" aria-label="Next" data-page="${currentPage + 1}">
                    <span aria-hidden="true">Next &raquo;</span>
                </a>
            </li>
        `);

        // Pagination button click event
        $('#pagination').on('click', 'a', function(e) {
            e.preventDefault();
            let newPage = $(this).data('page');
            if (newPage && newPage >= 1 && newPage <= totalPages) {
                currentPage = newPage;
                paginateGroups(filteredRows);  // Refresh the current page content
                setupPagination(filteredRows);  // Refresh pagination controls
            }
        });
    }

    // Attach event listeners to apply filters on any change
    $('#filter_price').on('input', applyFilters);
    $('.airline-checkbox, #economy, #nonStop, #oneStop, #twoStops, #economy, #premium_economy, #firstClass, #businessClass, #refund, #noRefund, #first_office_id, #second_office_id, #third_office_id, #fourth_office_id, #checkin0, #checkin1').on('change', applyFilters);

    // Initialize filtering and pagination on page load
    applyFilters();

    // Event listener to hide the preloader when filtering and pagination are complete
    document.addEventListener('filteringComplete', function() {
        if (filteredRows.length === 0) {
            document.getElementById('preloader2').style.display = 'none';
        } else {
            setTimeout(function() {
                document.getElementById('preloader2').style.display = 'none';
            }, 1000);
        }
    });
});
