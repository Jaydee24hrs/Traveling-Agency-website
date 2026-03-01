$(document).ready(function () {
    let airlines = {}; // Stores grouped itineraries during initial grouping
    let itineraries = []; // Stores individual itineraries for filtering
    let rows = []; // Stores grouped rows for display
    let filteredRows = []; // Stores filtered grouped rows
    const $flightResultsTable = $('#flight_result_table2 tbody');

    let resultsPerPage = 5;
    let currentResultsCount = 0;
    let price = null;
    let activeAirlineFilter = null;


    // Helper function to extract filter-relevant attributes from an itinerary
    function extractItineraryAttributes($el) {
        const stopsSummary = $el.find('.stops_summary').map(function () {
            return $(this).text().trim();
        }).get()[0] || '';

        const cabin = $el.find('.cabin_filter').map(function () {
            return $(this).text().trim();
        }).get()[0] || '';

        const flexibility = $el.find('.flexibility_filter').map(function () {
            return $(this).text().trim();
        }).get()[0] || '';

        const baggage = $el.find('.baggages_filter').map(function () {
            return $(this).text().trim();
        }).get()[0] || '';

        const officeID = $el.find('.office_id_filter').map(function () {
            return $(this).text().trim();
        }).get()[0] || '';

        const airlineNames = $el.find('.airline_name').map(function () {
            return $(this).text().trim();
        }).get();

        const price = parseFloat($el.find('.main_flight_price').text().trim().replace(/[₦$,\s]+/g, '').replace(/,/g, ''));

        return { stopsSummary, cabin, flexibility, baggage, officeID, airlineNames, price };
    }

    // Modified groupAndSortItineraries to store individual itineraries
    function groupAndSortItineraries() {
        airlines = {};
        itineraries = [];
        rows = [];
        filteredRows = [];

        $('.summary_grouping').each(function () {
            let $el = $(this);

            let airlineNameGoing = $el.find('.airline_name_going').map(function () {
                return $(this).text().trim();
            }).get();

            let prices = $el.find('.flight_price').map(function () {
                return parseFloat($(this).text().trim().replace(/[₦$,\s]+/g, '').replace(/,/g, ''));
            }).get();

            let uniqueAirlinesGoing = [...new Set(airlineNameGoing)];
            let groupKey = uniqueAirlinesGoing.join(" - ");

            if (prices.every(price => !isNaN(price))) {
                let minPrice = Math.min(...prices);

                // Store individual itinerary details
                const attributes = extractItineraryAttributes($el);
                itineraries.push({
                    flightHTML: $el.closest('.parent_result').prop('outerHTML'),
                    price: minPrice,
                    airlineName: groupKey,
                    stops: attributes.stopsSummary,
                    cabin: attributes.cabin,
                    flexibility: attributes.flexibility,
                    baggage: attributes.baggage,
                    officeID: attributes.officeID,
                    airlineNames: attributes.airlineNames
                });

                // Group by airline for initial display
                if (!airlines[groupKey]) {
                    airlines[groupKey] = [];
                }
                airlines[groupKey].push({
                    flightHTML: $el.closest('.parent_result').prop('outerHTML'),
                    price: minPrice,
                    airlineName: groupKey
                });
            }
        });

        // Build grouped rows from airlines
        rebuildGroups(airlines);

        completeLoading();
    }

    // Helper function to rebuild grouped rows from filtered itineraries
    function rebuildGroups(filteredAirlines) {
        rows = [];
        filteredRows = [];

        Object.keys(filteredAirlines).forEach(airline => {
            filteredAirlines[airline].sort((a, b) => a.price - b.price);
            let count = filteredAirlines[airline].length;
            let firstItinerary = filteredAirlines[airline][0].flightHTML;
            let airlineID = `airline_${airline.replace(/\W+/g, '_')}`;

            let airlineEntry = {
                html: $('<tr class="airline_entry shadow-1 bg-white text-dark row m-0 p-0 mt-3" data-aos="fade-up" data-aos-duration="2000"></tr>').append(firstItinerary),
                price: filteredAirlines[airline][0].price,
                airlineName: airline
            };

            if (count > 1) {
                // Create the "Show +X More Flights Available" button
                let $collapseLink = $(`
                    <div class="text-center make_bg_result py-2 text-white show-more-button" data-mdb-toggle="collapse" href="#${airlineID}" role="button" aria-expanded="false" aria-controls="${airlineID}" style="">
                        <span class='text-white'> Show +${count - 1}</span> <span class="">More Flights</span>
                    </div>
                `);
        
                // Create the "Hide Additional Flights Shown" button
                let $hideButton = $(`
                    <div class="text-center py-2 make_bg_result text-white hide-button" data-mdb-toggle="collapse" href="#${airlineID}" role="button" aria-expanded="false" aria-controls="${airlineID}" style="display: none;">
                        <span>Hide Flights Shown</span>
                    </div>
                `);
        
                // Create the collapse container
                let $collapseContainer = $(`
                    <div class="collapse shadow-2 m-0 p-0" id="${airlineID}">
                        <div class="row group_content make_bg_new border-0 text-dark p-0 m-0">
                            ${airlines[airline].slice(1).map(itinerary => {
                                // Create a temporary container to modify the HTML
                                const $temp = $('<div>').html(itinerary.flightHTML);
                                
                                // Add mt-3 class to the parent_result element
                                $temp.find('.parent_result').addClass('mt-3');
                                
                                // Return the modified HTML
                                return $temp.html();
                            }).join('')}
                        </div>
                    </div>
                `);
        
                // Append the buttons and collapse container to the airline entry
                airlineEntry.html.append($collapseLink).append($collapseContainer).append($hideButton);
        
                // Handle the collapse show event
                $collapseContainer.on('show.bs.collapse', function () {
                    $collapseLink.hide(); // Hide the "Show +X" button
                    $hideButton.show();   // Show the "Hide" button
                });
        
                // Handle the collapse hide event
                $collapseContainer.on('hide.bs.collapse', function () {
                    $hideButton.hide();   // Hide the "Hide" button
                    $collapseLink.show(); // Show the "Show +X" button
                });
            }
        
            rows.push(airlineEntry);
        });

        rows.sort((a, b) => a.price - b.price);
        filteredRows = rows;
        currentResultsCount = 0;
        $flightResultsTable.empty();
        loadMoreRows();
    }

    function loadMoreRows() {
        const remainingRows = filteredRows.slice(currentResultsCount, currentResultsCount + resultsPerPage);

        if (remainingRows.length === 0) return;

        let fragment = $(document.createDocumentFragment());
        remainingRows.forEach(row => fragment.append(row.html));
        $flightResultsTable.append(fragment);

        currentResultsCount += remainingRows.length;
        document.dispatchEvent(new Event('filteringComplete'));
    }

    // Infinite Scroll Event
    let scrollTimeout;
    $(window).on('scroll', function () {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            if ($(window).scrollTop() + $(window).height() >= $(document).height() - 100) {
                loadMoreRows();
            }
        }, 100);
    });

    // Filter by Airline (checkbox)
    function filterByAirline() {
        const checkedAirlines = $('.airline-checkbox:checked').map(function () {
            return $(this).val().trim();
        }).get();

        let filteredItineraries = itineraries;

        if (checkedAirlines.length > 0) {
            filteredItineraries = itineraries.filter(itinerary => {
                return checkedAirlines.some(airline => itinerary.airlineNames.includes(airline));
            });
        }

        // Regroup filtered itineraries by airline
        let filteredAirlines = {};
        filteredItineraries.forEach(itinerary => {
            if (!filteredAirlines[itinerary.airlineName]) {
                filteredAirlines[itinerary.airlineName] = [];
            }
            filteredAirlines[itinerary.airlineName].push({
                flightHTML: itinerary.flightHTML,
                price: itinerary.price,
                airlineName: itinerary.airlineName
            });
        });

        rebuildGroups(filteredAirlines);
    }

    // Filter by Stops
    function filterByStops() {
        const nonStopChecked = $('#nonStop').is(':checked');
        const oneStopChecked = $('#oneStop').is(':checked');
        const twoStopsChecked = $('#twoStops').is(':checked');

        let filteredItineraries = itineraries;

        if (nonStopChecked || oneStopChecked || twoStopsChecked) {
            filteredItineraries = itineraries.filter(itinerary => {
                return (
                    (nonStopChecked && itinerary.stops === 'Non Stop') ||
                    (oneStopChecked && itinerary.stops === '1 Stop') ||
                    (twoStopsChecked && itinerary.stops === '2 Stops')
                );
            });
        }

        // Regroup filtered itineraries by airline
        let filteredAirlines = {};
        filteredItineraries.forEach(itinerary => {
            if (!filteredAirlines[itinerary.airlineName]) {
                filteredAirlines[itinerary.airlineName] = [];
            }
            filteredAirlines[itinerary.airlineName].push({
                flightHTML: itinerary.flightHTML,
                price: itinerary.price,
                airlineName: itinerary.airlineName
            });
        });

        rebuildGroups(filteredAirlines);
    }

    // Filter by Cabin
    function filterByCabin() {
        const economy = $('#economy').is(':checked');
        const premium = $('#premium_economy').is(':checked');
        const business = $('#businessClass').is(':checked');
        const first = $('#firstClass').is(':checked');

        let filteredItineraries = itineraries;

        if (economy || premium || business || first) {
            filteredItineraries = itineraries.filter(itinerary => {
                return (
                    (economy && itinerary.cabin === 'ECONOMY') ||
                    (premium && itinerary.cabin === 'PREMIUM') ||
                    (business && itinerary.cabin === 'BUSINESS') ||
                    (first && itinerary.cabin === 'FIRST')
                );
            });
        }

        // Regroup filtered itineraries by airline
        let filteredAirlines = {};
        filteredItineraries.forEach(itinerary => {
            if (!filteredAirlines[itinerary.airlineName]) {
                filteredAirlines[itinerary.airlineName] = [];
            }
            filteredAirlines[itinerary.airlineName].push({
                flightHTML: itinerary.flightHTML,
                price: itinerary.price,
                airlineName: itinerary.airlineName
            });
        });

        rebuildGroups(filteredAirlines);
    }

    // Filter by Flexibility
    function filterByFlexibility() {
        const refundChecked = $('#refund').is(':checked');
        const noRefundChecked = $('#noRefund').is(':checked');

        let filteredItineraries = itineraries;

        if (refundChecked || noRefundChecked) {
            filteredItineraries = itineraries.filter(itinerary => {
                return (
                    (refundChecked && itinerary.flexibility === 'Refundable') ||
                    (noRefundChecked && itinerary.flexibility === 'Non Refundable')
                );
            });
        }

        // Regroup filtered itineraries by airline
        let filteredAirlines = {};
        filteredItineraries.forEach(itinerary => {
            if (!filteredAirlines[itinerary.airlineName]) {
                filteredAirlines[itinerary.airlineName] = [];
            }
            filteredAirlines[itinerary.airlineName].push({
                flightHTML: itinerary.flightHTML,
                price: itinerary.price,
                airlineName: itinerary.airlineName
            });
        });

        rebuildGroups(filteredAirlines);
    }

    // Filter by Baggage
    function filterByBaggages() {
        const zeroBaggageChecked = $('#checkin0').is(':checked');
        const oneBaggageChecked = $('#checkin1').is(':checked');

        let filteredItineraries = itineraries;

        if (zeroBaggageChecked || oneBaggageChecked) {
            filteredItineraries = itineraries.filter(itinerary => {
                return (
                    (zeroBaggageChecked && (itinerary.baggage === '0 PC' || itinerary.baggage === '0kg')) ||
                    (oneBaggageChecked && itinerary.baggage !== '0 PC' && itinerary.baggage !== '0kg')
                );
            });
        }

        // Regroup filtered itineraries by airline
        let filteredAirlines = {};
        filteredItineraries.forEach(itinerary => {
            if (!filteredAirlines[itinerary.airlineName]) {
                filteredAirlines[itinerary.airlineName] = [];
            }
            filteredAirlines[itinerary.airlineName].push({
                flightHTML: itinerary.flightHTML,
                price: itinerary.price,
                airlineName: itinerary.airlineName
            });
        });

        rebuildGroups(filteredAirlines);
    }

    // Filter by Office ID
    function filterByOfficeID() {
        const lagos = $('#first_office_id').is(':checked');
        const london = $('#second_office_id').is(':checked');
        const usa = $('#third_office_id').is(':checked');
        const accra = $('#fourth_office_id').is(':checked');

        let filteredItineraries = itineraries;

        if (lagos || accra || usa || london) {
            filteredItineraries = itineraries.filter(itinerary => {
                return (
                    (lagos && itinerary.officeID === 'LOSN828HJ') ||
                    (accra && itinerary.officeID === 'ACCG828TY') ||
                    (usa && itinerary.officeID === 'SHR1S28AA') ||
                    (london && itinerary.officeID === 'LONU128XJ')
                );
            });
        }

        // Regroup filtered itineraries by airline
        let filteredAirlines = {};
        filteredItineraries.forEach(itinerary => {
            if (!filteredAirlines[itinerary.airlineName]) {
                filteredAirlines[itinerary.airlineName] = [];
            }
            filteredAirlines[itinerary.airlineName].push({
                flightHTML: itinerary.flightHTML,
                price: itinerary.price,
                airlineName: itinerary.airlineName
            });
        });

        rebuildGroups(filteredAirlines);
    }

    // Filter by Price (click filter)
    function filterByPriceNew(price) {
        const formattedPrice = parseFloat(price.toString().replace(/[^\d.-]/g, '').trim());

        let filteredItineraries = itineraries.filter(itinerary => {
            return Math.abs(itinerary.price - formattedPrice) < 0.01; // Tolerance for floating-point comparison
        });

        // Regroup filtered itineraries by airline
        let filteredAirlines = {};
        filteredItineraries.forEach(itinerary => {
            if (!filteredAirlines[itinerary.airlineName]) {
                filteredAirlines[itinerary.airlineName] = [];
            }
            filteredAirlines[itinerary.airlineName].push({
                flightHTML: itinerary.flightHTML,
                price: itinerary.price,
                airlineName: itinerary.airlineName
            });
        });

        rebuildGroups(filteredAirlines);
    }

    // Filter by Airline (click filter)
    function filterByAirlineNew(selectedAirline) {
        let filteredItineraries = itineraries;

        if (selectedAirline) {
            filteredItineraries = itineraries.filter(itinerary => {
                return itinerary.airlineNames.includes(selectedAirline);
            });
        }

        // Regroup filtered itineraries by airline
        let filteredAirlines = {};
        filteredItineraries.forEach(itinerary => {
            if (!filteredAirlines[itinerary.airlineName]) {
                filteredAirlines[itinerary.airlineName] = [];
            }
            filteredAirlines[itinerary.airlineName].push({
                flightHTML: itinerary.flightHTML,
                price: itinerary.price,
                airlineName: itinerary.airlineName
            });
        });

        rebuildGroups(filteredAirlines);
    }


     // Set up the click handler for price filtering
     $('.filter_price_atag').on('click', function (e) {
        e.preventDefault();
        const selectedPrice = parseFloat($(this).text().replace(/[^\d.-]/g, ''));
        if (price === selectedPrice) {
            price = null;
            filterByPriceNew(); // Reset to all itineraries
        } else {
            price = selectedPrice;
            filterByPriceNew(price);
        }
    });

    // Set up the click handler for airline filtering
    $('.airline-filter').on('click', function (e) {
        e.preventDefault();
        const selectedAirline = $(this).text().trim();
        if (activeAirlineFilter === selectedAirline) {
            activeAirlineFilter = null;
            filterByAirlineNew(); 
        } else {
            activeAirlineFilter = selectedAirline;
            filterByAirlineNew(selectedAirline);
        }
    });

    // Event listener for all filter changes
    $('body').on('change', '.airline-checkbox, #nonStop, #oneStop, #twoStops, #economy, #premium_economy, #businessClass, #firstClass, #refund, #noRefund, #checkin0, #checkin1, #first_office_id, #second_office_id, #third_office_id, #fourth_office_id', function () {
        if ($(this).hasClass('airline-checkbox')) {
            filterByAirline();
        } else if ($('#nonStop, #oneStop, #twoStops').is(this)) {
            filterByStops();
        } else if ($('#economy, #premium_economy, #businessClass, #firstClass').is(this)) {
            filterByCabin();
        } else if ($('#refund, #noRefund').is(this)) {
            filterByFlexibility();
        } else if ($('#checkin0, #checkin1').is(this)) {
            filterByBaggages();
        } else if ($('#first_office_id, #second_office_id, #third_office_id, #fourth_office_id').is(this)) {
            filterByOfficeID();
        }
    });

    groupAndSortItineraries();

    $('body').append('<ul id="pagination" class="pagination justify-content-center mt-3"></ul>');
});