document.addEventListener('DOMContentLoaded', function () {

 // Profile Modal
 // Find the team_pic_edit icon and the file input element
 var editIcon = document.getElementById('uploadIcon');
 var fileInput = document.getElementById('imageUpload');

 // Add a click event listener to the icon
 editIcon.addEventListener('click', function () {
   // Trigger the click event of the hidden file input
   fileInput.click();
 });


 // Personal Information Edit
 function enableEditing(fields) {
   fields.forEach(function (field) {
     field.removeAttribute("readonly");
     field.classList.add("active-edit"); // Add the active-edit class
   });
 }

 function disableEditing(fields) {
   fields.forEach(function (field) {
     field.setAttribute("readonly", true);
     field.classList.remove("active-edit"); // Remove the active-edit class
   });
 }


 document.querySelectorAll(".edit_btn_personal").forEach((editBtn, index) => {
  editBtn.addEventListener("click", function () {
    enableEditing(document.querySelectorAll('.personal_edit'));
  });
});

 // Get all save buttons and attach event listeners
document.querySelectorAll(".personal_save_btn").forEach((saveBtn, index) => {
  saveBtn.addEventListener("click", function () {
    // Save logic here, you can use AJAX to send data to the server
    // For simplicity, I'll just alert the saved message
    iziToast.success({
      title: 'OK',
      message: 'Information Saved',
      position: 'topRight'
    });

    // Make all fields readonly again
    disableEditing(document.querySelectorAll('.personal_edit'));
  });
});



 // Personal Information Search =================================
 // Generic table filter function
 function filterTable(inputId, tableId) {
   document.getElementById(inputId).addEventListener("input", function () {
     var input, filter, table, tr, td, i, txtValue;
     input = document.getElementById(inputId);
     filter = input.value.toUpperCase();
     table = document.getElementById(tableId);
     tr = table.getElementsByTagName("tr");

     for (i = 1; i < tr.length; i++) {
       td = tr[i].getElementsByTagName("td")[0];
       if (td) {
         txtValue = td.textContent || td.innerText;
         if (txtValue.toUpperCase().indexOf(filter) > -1) {
           tr[i].style.display = "";
         } else {
           tr[i].style.display = "none";
         }
       }
     }
   });
 }

 // Call the function for the "agencyTable"
 filterTable("personal_search", "agencyTable");
 // Call the function for the "teamsTable"
 filterTable("search_teams", "teamsTable");



 // Attach click event handlers to the trash icons
 attachTrashClickHandlers();

 // Update the agency number
 updateAgencyNum();

 function updateAgencyNum() {
   var table = document.getElementById("agencyTable");
   var rowCount = table.tBodies[0].rows.length;
   document.getElementById("agency_num").innerText = rowCount;
 }

 function attachTrashClickHandlers() {
   var trashIcons = document.querySelectorAll(".trash_can");
   trashIcons.forEach(function (icon, index) {
     icon.addEventListener("click", function () {
       confirmDelete(this);
     });
   });
 }

 function confirmDelete(icon) {
   iziToast.question({
     title: 'Confirmation',
     message: 'Are you sure you want to delete?',
     position: 'center',
     color: 'red',
     buttons: [
       ['<button><b>Yes</b></button>', function (instance, toast) {
         instance.hide({ transitionOut: 'fadeOut' }, toast, 'button');
         // Delete the row
         deleteRow(icon);
       }, true],
       ['<button>No</button>', function (instance, toast) {
         instance.hide({ transitionOut: 'fadeOut' }, toast, 'button');
       }],
     ],
   });
 }

 function deleteRow(icon) {
   var row = icon.closest("tr");
   var table = document.getElementById("agencyTable");
   table.tBodies[0].removeChild(row);
   // Update the agency number after deletion
   updateAgencyNum();
 }


 // Assign new Agency
 document.getElementById('agencySelect').addEventListener('change', function () {
   var assignBody = document.getElementById('assign_body');
   assignBody.style.display = this.value !== '' ? 'table-row-group' : 'none';
 });

});


