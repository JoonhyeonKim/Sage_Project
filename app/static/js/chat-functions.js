$(document).ready(function() {
    // Handle form submission event
    $('#chat-form').on('submit', function(e) {
        e.preventDefault(); // Prevent default form submission
        submitMessage();
    });

    // Handle button click event for users who click the button instead of pressing Enter
    $('#submit-btn').on('click', function(e) {
        e.preventDefault(); // Prevent default button action
        submitMessage();
    });

    // Handle character card upload submission
    $('#upload-submit-btn').click(function(e) {
        e.preventDefault();
        var fileInput = $('#character_card')[0];
        if (fileInput.files.length > 0) {
            uploadCharacterCard(fileInput.files[0]);
        } else {
            alert('Please select a file to upload.');
        }
    });
    // Function to handle the message submission
    function submitMessage() {
        var userInput = $('#user_input').val(); // Get the user input
        if(userInput.trim() === '') {
            alert('Please type a message.'); // Simple validation
            return; // Stop the function if input is empty
        }

         // Explicitly show the loading indicator
        $('#loading').css('display', 'block');

        $.ajax({
            type: "POST",
            url: "/interact",
            data: JSON.stringify({ user_input: userInput }), // Correctly format the data for JSON
            contentType: "application/json", // Set the correct content type for JSON
            dataType: "json", // Expect a JSON response
            success: function(response) {
                // Assuming the response object contains 'ai_response'
                var aiResponse = response.ai_response;

                // Append both user input and AI response to the chat history
                $('.chat-history').append(
                    '<div class="chat-container user-container">' +
                    '<div class="response user-input"><strong>You:</strong> ' + userInput + '</div>' +
                    '<img src="/static/images/user.jpg" alt="User Profile Photo" class="profile-image"></div>' +
                    '<div class="chat-container response">' +
                    '<img src="/static/images/ai.jpg" alt="AI Profile Photo" class="profile-image">' +
                    '<div><strong>AI:</strong> ' + aiResponse + '</div></div>'
                );

                $('#user_input').val(''); // Clear input field after submission
            },
            error: function(xhr, status, error) {
                // Handle errors
                alert("Error: " + error); // Show a simple error message
                console.error("Error: " + status + " " + error);
            },
            complete: function() {
                $('#loading').hide(); // Hide the loading indicator regardless of success or error
            }
        });
    }
    // function uploadCharacterCard(file) {
    //     var formData = new FormData();
    //     formData.append('character_card', file);
    
    //     $('#loading').css('display', 'block');
    //     $.ajax({
    //         type: "POST",
    //         url: "/interact",
    //         data: formData,
    //         processData: false,
    //         contentType: false,
    //         success: function(response) {
    //             alert("Character card uploaded successfully!");
    //             // Optionally, you can clear the form or provide feedback to the user
    //             $('#character_card').val(''); // Clear file input
    //         },
    //         error: function(xhr, status, error) {
    //             alert("Error uploading file: " + error);
    //             alert("Error uploading file: " + xhr.responseText);
    //         },
    //         complete: function() {
    //             $('#loading').css('display', 'none');
    //         }
    //     });
    // }
    function uploadCharacterCard(file) {
        var formData = new FormData();
        formData.append('character_card', file);
        // Add a dummy user_input if your backend expects it
        formData.append('user_input', 'Dummy message for file upload.');
    
        $('#loading').css('display', 'block');
        $.ajax({
            type: "POST",
            url: "/interact",
            data: formData,
            processData: false,  // tell jQuery not to process the data
            contentType: false,  // tell jQuery not to set contentType
            success: function(response) {
                alert("Character card uploaded successfully!");
                $('#character_card').val(''); // Clear file input
            },
            error: function(xhr, status, error) {
                alert("Error uploading file: " + xhr.responseText);
            },
            complete: function() {
                $('#loading').css('display', 'none');
            }
        });
    }
});