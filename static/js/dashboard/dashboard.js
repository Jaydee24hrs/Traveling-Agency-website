$(document).ready(function(){
  // Switch Between Round trip To One Way
  $('#travel_type').on('change', function() {
    const selectedValue = $(this).val(); // Get the selected value

    $('#flight_type_round, #flight_type_multiple').on('change', function(){
        $('#selected_flight_type').val($(this).val());
    });

    if (selectedValue === 'oneway') {
        $('.return_date_col').hide();
        $('.add_more_multiple').hide();
        $('.flexible_col').show();
        $('.return_col').hide();
        $('.returnDate').hide();
        $('.normal_submit').show();
        $('.round_passenger').show();
        $('.multi_passenger').hide();
        $('.clone_count').hide();
        $('.append_clone').hide();
        $('.up_multiple').hide();
        $('.down_multiple').removeClass('d-none').addClass('d-flex');
        $('.economy_multiple').removeClass('d-flex').addClass('d-none');
        $('.economy_round').show();
        $('#selected_flight_type').val($('#flight_type_round').val());
    } else if (selectedValue === 'round_trip') {
        $('.return_date_col').show();
        $('.hide_multiple').show();
        $('.return_col').show();
        $('.returnDate').show();
        $('.add_more_multiple').hide();
        $('.flexible_col').show();
        $('.normal_submit').show();
        $('.round_passenger').show();
        $('.multi_passenger').hide();
        $('.clone_count').hide();
        $('.append_clone').hide();
        $('.up_multiple').hide();
        $('.down_multiple').removeClass('d-none').addClass('d-flex');
        $('.economy_multiple').removeClass('d-flex').addClass('d-none');
        $('.economy_round').show();
        $('#selected_flight_type').val($('#flight_type_round').val());
    } else if (selectedValue === 'multiple') {
        $('.return_date_col').hide();
        $('.flexible_col').hide();
        $('.return_col').hide();
        $('.returnDate').hide();
        $('.normal_submit').hide();
        $('.add_more_multiple').show();
        $('.round_passenger').hide();
        $('.multi_passenger').show();
        $('.clone_count').show();
        $('.append_clone').show();
        $('.up_multiple').show();
        $('.down_multiple').removeClass('d-flex').addClass('d-none');
        $('.economy_multiple').removeClass('d-none').addClass('d-flex');
        $('.economy_round').hide();
        $('#selected_flight_type').val($('#flight_type_multiple').val()); 
    }
});

// Trigger the change event initially to set the correct state based on the default selected option
$('#travel_type').trigger('change');


  // For Swap Between Origin and Destination Starts
  $(document).on('click', '.swap_btn', function () {
    var $clone = $(this).closest('.clone_count, .multi_clone_class'); // Find the closest clone section
    var originValue = $clone.find('.origin').val();
    var destinationValue = $clone.find('.destination').val();

    var originValueMain = $clone.find('.main_origin').val();
    var destinationValueMain = $clone.find('.main_destination').val();

    // Also
    var originLabel = $clone.find('.show_origin_text').text();
    var destinationLabel = $clone.find('.show_destination_text').text();

    $clone.find('.show_origin_text').text(destinationLabel)
    $clone.find('.show_destination_text').text(originLabel)

    $clone.find('.origin').val(destinationValue);
    $clone.find('.destination').val(originValue);

    $clone.find('.main_origin').val(destinationValueMain);
    $clone.find('.main_destination').val(originValueMain);
  });
  // For Swap Between Origin and Destination Ends


  // For Button Group To switch between one way, round trip, and multiple
  const buttons = document.querySelectorAll('.btn-group .btn');

  buttons.forEach(button => {
    button.addEventListener('click', function() {
      buttons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
    });
  });


  

  var cloneCount = 0;
  var maxClones = 2;
  
  $('#addMore').on('click', function () {
      if (cloneCount < maxClones) {
          var clonedDiv = $('#multi_clone').clone();
          clonedDiv.attr('id', 'multi_clone_' + cloneCount);
          clonedDiv.find('.remove-flight').show();
          clonedDiv.find('.multi_flights').text('Flight ' + (cloneCount + 2));
  
          // Clear values of input fields inside the cloned element
          clonedDiv.find('input').each(function () {
              $(this).val('');
          });
  
          clonedDiv.find('input, select, div, span').each(function () {
              var currentId = $(this).attr('id');
              var currentName = $(this).attr('name');
              if (currentId) {
                  $(this).attr('id', currentId + '_' + cloneCount);
              }
              if (currentName) {
                  $(this).attr('name', currentName + '_' + cloneCount);
              }
          });
  
          // Update the 'for' attribute of the label to match the new ID of the input field
          clonedDiv.find('label[for="origin"]').attr('for', 'origin_' + cloneCount);
          clonedDiv.find('label[for="destination"]').attr('for', 'destination_' + cloneCount);
  
          // Remove the "Search for Flight" button from the cloned div
          clonedDiv.find('.submit_btn[name="round_trip"]').closest('.parent_div_submit').remove();
  
          // Append cloned div
          $('.append_clone').append(clonedDiv);

          let container = $('#multi_clone_' + cloneCount);
          let flightTypeSelect = container.find('[id^="flight_type_multiple"]');
          let selectedFlightTypeInput = container.find('[id^="selected_flight_type"]');
  
          // Attach change event to update the hidden input
          flightTypeSelect.on('change', function () {
            selectedFlightTypeInput.val($(this).val());
          });


          cloneCount++;
  
          // Reattach event listeners to new elements
          attachDatePickers(clonedDiv, cloneCount);
  
          if (cloneCount === maxClones) {
              $('#addMore').hide();
          }
      }
  });
  
  // Function to format date as "10 Feb"
  function formatDate(dateString) {
      const date = new Date(dateString);
      if (isNaN(date)) return "-"; // Handle invalid dates
      const day = date.getDate();
      const month = date.toLocaleString("en-US", { month: "short" });
      return `${day} ${month}`;
  }
  
  // Function to attach event listeners to cloned spans and inputs
  function attachDatePickers(container, count) {
      let departureSpan = container.find('[id^="departureSpan"]');
      let returnSpan = container.find('[id^="returnSpan"]');
      let departureDate = container.find('[id^="departureDate"]');
      let returnDate = container.find('[id^="ReturnDate"]');
  
      function openDatePicker(inputElement) {
          inputElement.css('pointer-events', 'auto'); // Enable interaction
          inputElement[0].showPicker(); // Open the date picker
  
          setTimeout(() => {
              inputElement.css('pointer-events', 'none');
          }, 500);
      }
  
      departureSpan.on("click", function () {
          openDatePicker(departureDate);
      });
  
      returnSpan.on("click", function () {
          openDatePicker(returnDate);
      });
  
      departureDate.on("change", function () {
          if (departureDate.val()) {
              departureSpan.text(formatDate(departureDate.val()));
          }
      });
  
      returnDate.on("change", function () {
          if (returnDate.val()) {
              returnSpan.text(formatDate(returnDate.val()));
          }
      });
  }
  
  // Attach event listeners to the original elements
  $(document).ready(function () {
      attachDatePickers($('#multi_clone'), 0);
  });
  

  $('.append_clone').on('click', '.remove-flight', function(){
    $(this).closest('.row').remove();
    cloneCount--;
    $('#addMore').show()
    reNumberFlights(); 
  });

  $('.remove-flight').hide();

  // Function to update number
  function reNumberFlights() {
    $('.append_clone .clone_count').each(function (index) {
        $(this).find('.multi_flights').text('Flight ' + (index + 2)); // Renumber flight text
        $(this).attr('id', 'multi_clone_' + index); // Update the clone ID
        $(this).find('input, select').each(function () {
            var currentId = $(this).attr('id');
            var currentName = $(this).attr('name');
            if (currentId) {
                var newId = currentId.split('_')[0] + '_' + index;
                $(this).attr('id', newId);
            }
            if (currentName) {
                var newName = currentName.split('_')[0] + '_' + index;
                $(this).attr('name', newName);
            }
        });
    });
  }

  // Function to allow only numbers in input fields
  $('.form-outline input[type="number"]').on('input', function(){
    // Remove any non-numeric characters
    $(this).val(function(_, value){
      return value.replace(/\D/g, '');
    });
  });


  // Disable past dates in date inputs
  var today = new Date().toISOString().split('T')[0];
  $('input[type="date"]').attr('min', today);

  // Disable dates before the selected departure date in the return date input
  $('.departureDate').on('change', function(){
    var selectedDate = $(this).val();
    $('.returnDate').attr('min', selectedDate);
  });

  // For Passengers
  const adultsSelect = document.getElementById('adults');
  const childSelect = document.getElementById('child');
  const infantsSelect = document.getElementById('infants');

  function updateOptions() {
      const adults = parseInt(adultsSelect.value);
      const children = parseInt(childSelect.value);
      const infants = parseInt(infantsSelect.value);
      const totalPassengers = adults + children + infants;
      const totalAllowed = 9 - totalPassengers;

      const remainingForAdults = 9 - (children + infants);
      const remainingForChildren = 9 - (adults + infants);
      const remainingForInfants = Math.min(adults, 9 - (adults + children));

      updateSelectOptions(adultsSelect, remainingForAdults, 'Adult', adults);
      updateSelectOptions(childSelect, remainingForChildren, 'Child', children);
      updateSelectOptions(infantsSelect, remainingForInfants, 'Infant', infants);
  }

  function updateSelectOptions(selectElement, maxOption, defaultText, currentValue) {
      selectElement.innerHTML = '';
      for (let i = 0; i <= maxOption; i++) {
          const option = document.createElement('option');
          option.value = i;
          option.textContent = i === 0 ? defaultText : i;
          if (i === currentValue) {
              option.selected = true;
          }
          selectElement.appendChild(option);
      }
  }

  adultsSelect.addEventListener('change', updateOptions);
  childSelect.addEventListener('change', updateOptions);
  infantsSelect.addEventListener('change', updateOptions);

  // Initialize options on page load
  updateOptions();


  
  // For Passengers
  const adultsSelect_multiple = document.getElementById('adults_multiple');
  const childSelect_multiple = document.getElementById('child_multiple');
  const infantsSelect_multiple = document.getElementById('infants_multiple');

  function updateOptions_multiple() {
      const adults = parseInt(adultsSelect_multiple.value);
      const children = parseInt(childSelect_multiple.value);
      const infants = parseInt(infantsSelect_multiple.value);
      const totalPassengers = adults + children + infants;
      const totalAllowed = 9 - totalPassengers;

      const remainingForAdults = 9 - (children + infants);
      const remainingForChildren = 9 - (adults + infants);
      const remainingForInfants = Math.min(adults, 9 - (adults + children));

      updateSelectOptions(adultsSelect_multiple, remainingForAdults, 'Adult', adults);
      updateSelectOptions(childSelect_multiple, remainingForChildren, 'Child', children);
      updateSelectOptions(infantsSelect_multiple, remainingForInfants, 'Infant', infants);
  }

  function updateSelectOptions(selectElement, maxOption, defaultText, currentValue) {
      selectElement.innerHTML = '';
      for (let i = 0; i <= maxOption; i++) {
          const option = document.createElement('option');
          option.value = i;
          option.textContent = i === 0 ? defaultText : i;
          if (i === currentValue) {
              option.selected = true;
          }
          selectElement.appendChild(option);
      }
  }

  adultsSelect_multiple.addEventListener('change', updateOptions_multiple);
  childSelect_multiple.addEventListener('change', updateOptions_multiple);
  infantsSelect_multiple.addEventListener('change', updateOptions_multiple);

  // Initialize options on page load
  updateOptions_multiple();
  

});

