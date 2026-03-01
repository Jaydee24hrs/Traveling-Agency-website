$(document).ready(function(){
  $('#oneway').on('click', function(){
    $('.return_date_col').hide()
    $('.add_more_multiple').hide()
    $('.flexible_col').show()
    $('.normal_submit').show()
    $('.round_passenger').show()
    $('.multi_passenger').hide()
    $('.clone_count').hide()
    $('.append_clone').hide()
    $('.up_multiple').hide()
    $('.down_multiple').removeClass('d-none').addClass('d-flex');
  })



  $('#round_trip').on('click', function(){
    $('.return_date_col').show()
    $('.hide_multiple').show()
    $('.add_more_multiple').hide()
    $('.flexible_col').show()
    $('.normal_submit').show()
    $('.round_passenger').show()
    $('.multi_passenger').hide()
    $('.clone_count').hide()
    $('.append_clone').hide()
    $('.up_multiple').hide()
    $('.down_multiple').removeClass('d-none').addClass('d-flex');
  })

  $('#round_trip').trigger('click');

  $('#multiple').on('click', function(){
    $('.return_date_col').hide()
    $('.flexible_col').hide()
    $('.normal_submit').hide()
    $('.add_more_multiple').show()
    $('.round_passenger').hide()
    $('.multi_passenger').show()
    $('.clone_count').show()
    $('.append_clone').show()
    $('.up_multiple').show()
    $('.down_multiple').removeClass('d-flex').addClass('d-none');
  })




  // For Swap Between Origin and Destination Starts
  $(document).on('click', '.swap_btn', function () {
    var $clone = $(this).closest('.clone_count, .multi_clone_class'); // Find the closest clone section
    var originValue = $clone.find('.origin').val();
    var destinationValue = $clone.find('.destination').val();

    var originValueMain = $clone.find('.main_origin').val();
    var destinationValueMain = $clone.find('.main_destination').val();

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
  // var maxClones = 5;
  var maxClones = 2;

  $('#addMore').on('click', function(){
    if(cloneCount < maxClones){
      var clonedDiv = $('#multi_clone').clone();
      clonedDiv.attr('id', 'multi_clone_' + cloneCount);
      clonedDiv.find('.remove-flight').show();
      clonedDiv.find('.multi_flights').text('Flight ' + (cloneCount + 2));

      // Clear values of input fields inside the cloned element
      clonedDiv.find('input').each(function(){
        $(this).val('');
      });

      clonedDiv.find('input, select, div').each(function(){
        var currentId = $(this).attr('id');
        var currentName = $(this).attr('name');
        if(currentId){
          $(this).attr('id', currentId + '_' + cloneCount);
        }
        if(currentName){
          $(this).attr('name', currentName + '_' + cloneCount);
        }
        
      });
      $('.append_clone').append(clonedDiv);
      cloneCount++;
      if(cloneCount === maxClones){
        $('#addMore').hide()
      }
    }
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
  const adultsSelect = document.getElementById('markup_adults');
  const childSelect = document.getElementById('markup_child');
  const infantsSelect = document.getElementById('markup_infants');

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
  const adultsSelect_multiple = document.getElementById('markup_adult_multiple');
  const childSelect_multiple = document.getElementById('markup_child_multiple');
  const infantsSelect_multiple = document.getElementById('markup_infants_multiple');

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

