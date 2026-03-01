$(document).ready(function() {
  // Function to set up the print buttons
  function setupPrintButtons() {
      // Trigger system print dialog for each .print_itinerary button
      $('.print_itinerary').off('click').on('click', function() {
          // Hide other content and only show #booking_information when printing
          var originalContents = document.body.innerHTML;
          var printContents = document.getElementById('booking_information').innerHTML;
          // Set the body content to the booking information only
          document.body.innerHTML = printContents;
          // Open print dialog
          window.print();
          // Restore the original content after printing
          document.body.innerHTML = originalContents;
          // Re-setup event listeners
          setupPrintButtons();
      });
      
      // Trigger system print dialog for each .print_itinerary_full button
      $('.print_itinerary_full').off('click').on('click', function() {
          // Hide other content and only show #booking_information when printing
          var originalContents = document.body.innerHTML;
          var printContents = document.getElementById('full_itinerary').innerHTML;
          // Set the body content to the booking information only
          document.body.innerHTML = printContents;
          // Open print dialog
          window.print();
          // Restore the original content after printing
          document.body.innerHTML = originalContents;
          // Re-setup event listeners
          setupPrintButtons();
      });
  }
  
  // Initial setup
  setupPrintButtons();
});