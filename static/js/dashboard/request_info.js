$(document).ready(function() {
//   // For Chat Input Icon
//   document.getElementById('file_input_icon').addEventListener('click', function() {
//   document.getElementById('file_input').click();
//   });

  // To Automatically Scroll to the end For ChatBox
  document.addEventListener('DOMContentLoaded', (event) => {
    var chatContainer = document.getElementById('chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
  });

  // For tax Sections Starts
  $('#tax_body').hide();

  $('#add_tax').click(function() {
    $('#tax_body').toggle();
  });

  $('#add_more').click(function(e) {
    e.preventDefault();
  
    var newRow = $('.tax-row:first').clone();
    
    newRow.find('#add_more_data').remove();
    
    newRow.append('<td><button class="btn btn-danger remove-row"><i class="fa-solid fa-minus"></i></button></td>');

    $('#tax_body').append(newRow);
  });

  $('#tax_body').on('click', '.remove-row', function(e) {
    e.preventDefault();
    $(this).closest('tr').remove(); 
  });
  // For tax Sections Ends


  // For Currency Section Starts
    function handleCurrencyToggle(buttonId, bodyId) {
      $(bodyId).hide();

      $(buttonId).click(function() {
          $(bodyId).toggle();
      });
    }
    handleCurrencyToggle('#currency_converter', '#currency_body');
    handleCurrencyToggle('#currency_converter2', '#currency_body2');
  // For Currency Section Ends


  // Function to fetch countries data and populate currency selects
  function populateCurrencySelectors(className, displayClass) {
    fetch('https://restcountries.com/v3.1/all')
    .then(response => response.json())
    .then(data => {
        const currencySelects = document.querySelectorAll(className);
        const currenciesSet = new Set();

        data.forEach(country => {
            if (country.currencies) {
                Object.keys(country.currencies).forEach(currencyCode => {
                    currenciesSet.add(currencyCode);
                });
            }
        });

        const currencyOptions = Array.from(currenciesSet).map(currencyCode => {
            const option = document.createElement('option');
            option.value = currencyCode;
            option.textContent = currencyCode;
            return option;
        });

        currencySelects.forEach(select => {
            currencyOptions.forEach(option => {
                select.appendChild(option.cloneNode(true));
            });

            // Add event listener to update spans on selection change
            select.addEventListener('change', (event) => {
                const selectedCurrency = event.target.value;
                const currencyDisplays = document.querySelectorAll(displayClass);
                currencyDisplays.forEach(span => {
                    span.textContent = selectedCurrency;
                });
            });
        });
    })
    .catch(error => console.error('Error:', error));
  }
  populateCurrencySelectors('.currency', '.currency_display');
  populateCurrencySelectors('.currency2', '.currency_display2');




  // For Cloning the Refund Ticket Section
  let cloneIndex = 0;
  function handleRefundSectionClone(addButtonClass, sectionClass, wrapperId, removeButtonClass) {
      $(document).on('click', addButtonClass, function () {
          // Clone the section
          const $clone = $(sectionClass).first().clone();
          cloneIndex++;
          
          // Change the IDs and names of the cloned inputs
          $clone.find('input, select').each(function () {
              const id = $(this).attr('id');
              if (id) {
                  $(this).attr('id', id + '_' + cloneIndex);
              }
              const name = $(this).attr('name');
              if (name) {
                  $(this).attr('name', name + '_' + cloneIndex);
              }
          });
  
          // Clear the values of inputs and selects in the cloned section
          $clone.find('input').val('');
          $clone.find('select').prop('selectedIndex', 0);
  
          // Change the add button to a delete button in the cloned section
          $clone.find(addButtonClass).removeClass(addButtonClass.substring(1)).addClass(removeButtonClass.substring(1)).html('<i class="fa-solid fa-minus"></i>');
  
          // Append the cloned section
          $(wrapperId).append($clone);
      });
  
      // Handle the remove button click
      $(document).on('click', removeButtonClass, function () {
          $(this).closest(sectionClass).remove();
      });
  }
  
  handleRefundSectionClone('.add_more_refund', '.refund_duplicate', '#refund_section_wrapper', '.remove_refund');
  handleRefundSectionClone('.add_more_exchange', '.exchange_duplicate', '#exchange_section_wrapper', '.remove_refund2');



  // To Print Preview
  // Function to handle PDF generation from a DOM element
  function generatePDF(buttonId, elementSelector, fileName) {
    $(buttonId).on('click', function () {
        // Initialize jsPDF
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('p', 'pt', 'a4');

        // Function to add HTML content from a DOM element to PDF
        const addElementToPDF = (element) => {
            // Use html2canvas library to capture element as image
            html2canvas(element, { scrollY: -window.scrollY, scale: 2 }).then(canvas => {
                const imgData = canvas.toDataURL('image/png');
                const imgProps = doc.getImageProperties(imgData);
                const pdfWidth = doc.internal.pageSize.getWidth();
                const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

                // Add image to PDF document
                doc.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
                
                // Save PDF
                doc.save(fileName);
            });
        };

        // Call function to add modal content to PDF
        addElementToPDF(document.querySelector(elementSelector));
    });
  }

  // Call the function for the first set of elements
  generatePDF('#print_preview', '.preview_section', 'preview1.pdf');

  // Call the function for the second set of elements
  generatePDF('#print_preview2', '.preview_section2', 'preview2.pdf');





});

