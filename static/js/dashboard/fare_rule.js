
// Fare Rule With Only PENALTIES Starts
$(document).ready(function() {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    $('.fare-rules-link').on('click', function(e) {
        e.preventDefault();

        var flightData = $(this).attr('data-flight');
        var guestOfficeId = $(this).attr('data-guest-office-id');
        var modalId = $(this).attr('data-mdb-target');
        var contentSelector = modalId + ' .fare-rule-data';
        const textElement = document.querySelector('.preloader_text');
        // const preloader = document.querySelector('.preloader');  // Initialize preloader

        var flightDatas = {
            flight_data: flightData,
            guest_office_id: guestOfficeId
        };

        // Show preloader text
        sessionStorage.setItem('preloaderVisible', 'true');
        if (textElement) {
            textElement.innerText = 'Getting your fare rules, please wait...';
        }
        if (preloader) {
            preloader.style.display = 'flex';
        }

        // Clear previous content
        $(contentSelector).find('h5, h6, p').remove();

        $.ajax({
            url: '/booking/get_fare_rule',
            type: 'POST',
            contentType: 'application/json',
            headers: { 'X-CSRFToken': csrftoken },
            data: JSON.stringify(flightDatas),
            success: function(response) {
                let content = '';

                // Ensure that the detailed-fare-rules object exists
                if (response.included && response.included['detailed-fare-rules']) {
                    for (var ruleId in response.included['detailed-fare-rules']) {
                        var fareRule = response.included['detailed-fare-rules'][ruleId];
                        content += `<h5>Fare Basis: ${fareRule.fareBasis} - ${fareRule.name}</h5>`;

                        // Optional: Check if the fareRule itself is related to PENALTIES
                        // If there's a specific identifier, you can use it here
                        // For example: if (fareRule.category === 'PENALTIES') { ... }

                        // Loop through each description
                        fareRule.fareNotes.descriptions.forEach(function(description) {
                            // Check if the descriptionType is 'PENALTIES'
                            if (description.descriptionType.toUpperCase().includes('PENALTIES')) {
                                // Remove all sequences of dashes longer than 2 characters
                                let cleanText = description.text.replace(/-{2,}/g, '');
                                content += `<h6>${description.descriptionType}</h6>`;
                                content += `<p>${cleanText.replace(/\n/g, '<br>')}</p>`;
                            }
                        });
                    }
                } else {
                    content = `<h6>Cannot Get Fare Rule</h6>`;
                }

                // Check if any penalties content was found
                if (content.trim() === '') {
                    content = `<h6>No Penalties Information Available.</h6>`;
                }

                $(contentSelector).append(content);
                $(modalId).modal('show');
            },
            error: function(xhr, status, error) {
                console.error("Error fetching fare rules:", xhr.responseText);  // Detailed error logging
                $(contentSelector).html('<p>An error occurred while retrieving fare rules.</p>');
                $(modalId).modal('show');
            },
            complete: function() {
                // Hide the preloader
                sessionStorage.setItem('preloaderVisible', 'false');
                if (preloader) {
                    preloader.style.display = 'none';
                }
            }
        });
    });
});

// Fare Rule With Only PENALTIES Ends