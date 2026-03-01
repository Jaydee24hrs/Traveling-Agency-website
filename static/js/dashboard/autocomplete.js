document.addEventListener('DOMContentLoaded', function () {
    function setupAutocomplete(inputId, suggestionsContainerId, hiddenInputId, isOrigin) {
        const input = document.getElementById(inputId);
        const suggestionsContainer = document.getElementById(suggestionsContainerId);
        const hiddenInput = document.getElementById(hiddenInputId);

        function showSuggestions() {
            suggestionsContainer.style.display = 'block';
        }

        function hideSuggestions() {
            suggestionsContainer.style.display = 'none';
        }

        const iconClass = isOrigin ? 'fa-plane-departure' : 'fa-plane-arrival';

        let debounceTimer;
        input.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const query = input.value;
                if (query.length < 2) {
                    suggestionsContainer.innerHTML = '';
                    hideSuggestions();
                    return;
                }

                fetch(`/booking/search_flight_code?query=${query}`)
                    .then(response => response.json())
                    .then(data => {
                        suggestionsContainer.innerHTML = '';
                        showSuggestions();
                        const fragment = document.createDocumentFragment();
                        data.forEach(item => {
                            const suggestion = document.createElement('div');
                            suggestion.classList.add('autocomplete-suggestion');

                            const itemContent = `
                                <div class="suggestion-item">
                                    <div class="d-flex align-items-center justify-content-between small">
                                        <div>
                                            <strong>${item.city_name}</strong>
                                            <small>${item.country} - ${item.airport}</small>
                                        </div>
                                        <div>
                                            <strong class="border rounded py-1 px-2 small">${item.airport_code}</strong>
                                        </div>
                                    </div>
                                </div>
                            `;
                            suggestion.innerHTML = itemContent;

                            suggestion.setAttribute('data-id', item.id);
                            suggestion.setAttribute('data-code', item.airport_code);
                            suggestion.setAttribute('data-airport', `${item.country} - ${item.city_name} - ${item.airport} - (${item.airport_code})`);

                            suggestion.addEventListener('click', function () {
                                input.value = suggestion.getAttribute('data-airport');
                                hiddenInput.value = suggestion.getAttribute('data-code');
                                suggestionsContainer.innerHTML = '';

                                // Set the text content of the element with the class 'show_origin_text'
                                const showOriginText = document.querySelector('.show_origin_text');
                                const showDestinationText = document.querySelector('.show_destination_text');

                                if (isOrigin) {
                                    // Update the origin text element
                                    if (showOriginText) {
                                        showOriginText.textContent = suggestion.getAttribute('data-airport');
                                    }
                                } else {
                                    // Update the destination text element
                                    if (showDestinationText) {
                                        showDestinationText.textContent = suggestion.getAttribute('data-airport');
                                    }
                                }

                                hideSuggestions();
                            });

                            fragment.appendChild(suggestion);
                        });
                        suggestionsContainer.appendChild(fragment);
                    })
                    .catch(error => {
                        console.error('Error fetching data:', error);
                        hideSuggestions();
                    });
            }, 300); // Debounce delay
        });

        // Hide suggestions if click is outside of input and suggestions container
        document.addEventListener('click', function (event) {
            if (!suggestionsContainer.contains(event.target) && event.target !== input) {
                suggestionsContainer.innerHTML = '';
                hideSuggestions();
            }
        });
    }

    // Function to initialize autocomplete for dynamic clones
    function initializeAutocompleteForClones() {
        const clones = document.querySelectorAll('.multi_clone_class');
        clones.forEach((clone, index) => {
            setupAutocomplete(`origin_${index}`, `autocomplete-suggestions_${index}`, `hidden_origin_${index}`, true);
            setupAutocomplete(`destination_${index}`, `autocomplete-suggestions_return_${index}`, `hidden_destination_${index}`, false);
        });
    }

    // Initialize autocomplete for existing elements
    setupAutocomplete('origin', 'autocomplete-suggestions', 'hidden_origin', true);

    setupAutocomplete('destination', 'autocomplete-suggestions_return', 'hidden_destination', false);

    // Handle dynamic addition of clones
    document.querySelector('#addMore').addEventListener('click', function () {
        // Delay to ensure clones are added to the DOM
        setTimeout(() => {
            initializeAutocompleteForClones();
        }, 100); // Small delay to ensure clones are properly added
    });

    // Initial setup on page load
    initializeAutocompleteForClones();
});
