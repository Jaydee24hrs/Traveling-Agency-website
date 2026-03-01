$(document).ready(function() {
  //To switch between private and corporate form
  function showPrivateForm() {
    $('#private_form').addClass('active');
    $('#corporate_form').removeClass('active');
  }

  function showCorporateForm() {
    $('#corporate_form').addClass('active');
    $('#private_form').removeClass('active');
  }

  $('#private').on('click', function() {
    $('#business_info').hide()
    showPrivateForm();
  });

  $('#corporate').on('click', function() {
    $('#business_info').hide()
    showCorporateForm();
  });

  $('#back_to_home').on('click', function() {
    $('#private_form').removeClass('active')
    $('#business_info').show()
  });
  //To switch between private and corporate form Ends

  //To switch between business and limited in corporate
  function showBusinessDocumentUploadCarousel() {
    $('#business_document_upload').addClass('active');
    // $('#limited_document_upload').removeClass('active');
  }

  function goToPreviousSlide() {
    $('#corporate_carousel').carousel('prev');
  }

  $('#previous_btn').on('click', function() {
    $('#limited_document_upload').removeClass('active')
    goToPreviousSlide();
  });


  $('#back_to_home2').on('click', function() {
    $('#corporate_form').removeClass('active')
    $('#business_info').show()
  });

  //To switch between business and limited in corporate ends


  // Function to update business name
  function updateBusinessName() {
    var givenName = $('#personal_givenName').val();
    var surname = $('#personal_surname').val();
    var fullName = givenName + ' ' + surname;
    $('#businessName').val(fullName.toUpperCase());
  }
  $('#personal_givenName, #personal_surname').on('input', updateBusinessName);
  // Function to update business name Ends

  // Fetch country data from Rest Countries API
  // const countryDropdown = $(".countries");
  // $.ajax({
  //     url: "https://restcountries.com/v3.1/all",
  //     method: "GET",
  //     dataType: "json",
  //     success: function(data) {
  //         // Sort the countries alphabetically
  //         data.sort((a, b) => a.name.common.localeCompare(b.name.common));
  //         // Populate the dropdown with sorted country names
  //         $.each(data, function(index, country) {
  //             const option = $("<option>");
  //             option.val(country.name.common);
  //             option.text(country.name.common);
  //             countryDropdown.append(option);
  //         });
  //     },
  //     error: function(error) {
  //         console.error("Error fetching countries:", error);
  //     }
  // });
  // // Listen for change event on the dropdown
  // countryDropdown.on('change', function() {
  //     // Get the selected value
  //     const selectedCountry = $(this).val();
  //     // Update the selected country element
  //     $('#selectedCountry').text("Selected Country: " + selectedCountry);
  // });
  // Fetch country data from Rest Countries API Ends



  // For Add Directors
  let clonedCount = 0;
   $('#clone_count_value').val(clonedCount);
   $(document).on("click", "#addDirectorBtn", function () {
    // Check if the maximum number of clones (4) has been reached
    $('#clone_count_value').val(clonedCount);
    if (clonedCount < 4) {
        // Clone the director section
        var clonedDirectorInput = $("#directorSection").clone();
        var clonedDirectorDocument = $("#upload_director_section").clone();

        // Clear input fields in the cloned section
        clonedDirectorInput.find('input[type="text"]').val('');
        clonedDirectorInput.find('input[type="file"]').val('');


        clonedDirectorInput.find('.directors_note').hide();
        clonedDirectorDocument.find('.directors_note').hide();

        // Update the id of the cloned section
        var newId = 'directorSection' + clonedCount;
        clonedDirectorInput.attr('id', newId);

        var newClone = 'upload_director_section' + clonedCount;
        clonedDirectorDocument.attr('id', newClone);
        $('#clone_count_value').val(clonedCount);

        // Update the id and names and label for inputs in the cloned section
        clonedDirectorInput.find('[id^="director_"], select').each(function () {
            var currentId = $(this).attr('id');
            var newName = $(this).attr('name');
            var newInputId = currentId + clonedCount;
            var new_name_input = newName + clonedCount;
            $(this).attr('id', newInputId);
            $(this).attr('name', new_name_input);
            // Update the corresponding label
            clonedDirectorInput.find('label[for="' + currentId + '"]').attr('for', newInputId);
        });

        clonedDirectorDocument.find('[id^="director_"], select, span').each(function () {
            var currentDocumentId = $(this).attr('id');
            var newName = $(this).attr('name');
            var newValueId = currentDocumentId + clonedCount;
            var new_file_name = newName + clonedCount;
            $(this).attr('id', newValueId);
            $(this).attr('name', new_file_name);
            // Update the corresponding label
            clonedDirectorDocument.find('label[for="' + currentDocumentId + '"]').attr('for', newValueId);
            // clonedDirectorDocument.find('#means_name_corporate' + currentDocumentId).attr('id', newValueId);
        });


        $('#clone_count_value').val(clonedCount);
        // Change the "Add More Director" button to a "Remove" button in the cloned section
        clonedDirectorInput.find("#addDirectorBtn")
            .text('Remove')
            .css({
                'background': 'red',
                'border': 'none'
            })
            .prop("id", "removeDirectorBtn" + clonedCount); // Change the id for removal

        // Append the cloned section to the container for cloned directors
        $(".clone_director").append(clonedDirectorInput);
        $(".clone_upload_director_section").append(clonedDirectorDocument);

        // Increment the clonedCount
        clonedCount++;

        // $('#clone_count_value').val(clonedCount);
        $('#clone_count_value').val(clonedCount);

        // Disable the button if the maximum clones are reached
        if (clonedCount === 4) {
            $("#addDirectorBtn").prop("disabled", true);
        }
        
    } else {
        // Disable the button if the maximum clones are reached
        $("#addDirectorBtn").prop("disabled", true);
    }
    var input = document.querySelectorAll(".phone");
    input.forEach(item=>{
      window.intlTelInput(item, {
        initialCountry: "gh",
        utilsScript: "/static/build/js/utils.js"
      });
    })
});

  $(document).on("click", "[id^=removeDirectorBtn]", function () {
      // Handle the click event for "Remove" buttons
      var index = $(this).prop("id").match(/\d+/)[0];
      $("#directorSection" + index).remove();

      if ($(".clone_upload_director_section #" + 'upload_director_section' + index).length > 0) {
        $(".clone_upload_director_section #" + 'upload_director_section' + index).remove();
      }
      
      clonedCount--;
      
      // Enable the "Add More Director" button since a section is removed
      $("#addDirectorBtn").prop("disabled", false);
      
      event.stopPropagation(); // Prevent bubbling
  });
  // For Add Directors Ends


  // For Capturing User Giving Name and Surname and append it to the means of identification
  function privateMeans() {
    var givenName = $('#personal_givenName').val();
    var surname = $('#personal_surname').val();
    var fullName = givenName + ' ' + surname;
    $('#means_name_private').text(fullName);
  }
  $('#personal_givenName, #personal_surname').on('input', privateMeans);

  // Function to update corporate means
  function corporateMeans(index) {
    var givenName = $('#director_givenName' + index).val();
    var surname = $('#director_surname' + index).val();
    var fullName = givenName + ' ' + surname;
    $('#means_name_corporate' + index).text(fullName);
  }

  // Event listener for input changes in givenName and surname fields
  $(document).on('input', '[id^="director_givenName"], [id^="director_surname"]', function () {
    var index = $(this).attr('id').replace(/\D+/g, '');
    corporateMeans(index);
  });


  // // For Getting the country Code
  // var input = document.querySelector("#personal_phone_number");
  // const iti =  window.intlTelInput(input, {
  //   initialCountry: "gh",
  //   utilsScript: "/static/build/js/utils.js"
  // });
  // $('#personal_phone_number_dial_code').val(iti.getSelectedCountryData().dialCode);
  // input.addEventListener("countrychange", function() {
  //   $('#personal_phone_number_dial_code').val(iti.getSelectedCountryData().dialCode);
  // });


  // var input = document.querySelector("#company_phone_number");
  // const iti2 =  window.intlTelInput(input, {
  //   initialCountry: "gh",
  //   utilsScript: "/static/build/js/utils.js"
  // });
  // $('#company_phone_number_dial_code').val(iti2.getSelectedCountryData().dialCode);
  // input.addEventListener("countrychange", function() {
  //   $('#company_phone_number_dial_code').val(iti2.getSelectedCountryData().dialCode);
  // });
  
function initializeIntlTelInput(inputSelector, dialCodeSelector) {
    var input = document.querySelector(inputSelector);
    let iti = window.intlTelInput(input, {
        initialCountry: "gh",
        utilsScript: "/static/build/js/utils.js"
    });
    $(dialCodeSelector).val(iti.getSelectedCountryData().dialCode);
    input.addEventListener("countrychange", function() {
        $(dialCodeSelector).val(iti.getSelectedCountryData().dialCode);
    });
}

initializeIntlTelInput("#personal_phone_number", "#personal_phone_number_dial_code");
initializeIntlTelInput("#company_phone_number", "#company_phone_number_dial_code");

var inputs = document.querySelectorAll(".phone");
inputs.forEach(item => {
    let iti = window.intlTelInput(item, {
        initialCountry: "gh",
        utilsScript: "/static/build/js/utils.js"
    });
    $(item).closest('.form-group').find('.dial-code').val(iti.getSelectedCountryData().dialCode);
    item.addEventListener("countrychange", function() {
        $(item).closest('.form-group').find('.dial-code').val(iti.getSelectedCountryData().dialCode);
    });
});

// Handle director phone number specifically
var directorPhoneInput = document.querySelector("#director_phone_number");
if (directorPhoneInput) {
    let itiDirector = window.intlTelInput(directorPhoneInput, {
        initialCountry: "gh",
        utilsScript: "/static/build/js/utils.js"
    });
    $('#director_phone_number_dial_code').val(itiDirector.getSelectedCountryData().dialCode);
    directorPhoneInput.addEventListener("countrychange", function() {
        $('#director_phone_number_dial_code').val(itiDirector.getSelectedCountryData().dialCode);
    });
}

});