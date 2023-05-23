const microphoneButton = document.getElementById('microphoneButton');
const startSpeakingButton = document.getElementById('start_speaking_practice');

// Button click event listener
microphoneButton.addEventListener('click', function() {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(function(stream) {
      // Microphone access granted
      console.log('Access granted');
      toggleButtons();
    })
    .catch(function(err) {
      // Microphone access denied or error occurred
      console.log('Access denied');
    });
});

// Checking if microphone access was already granted
if (navigator.permissions) {
  navigator.permissions.query({ name: 'microphone' })
    .then(function(permissionStatus) {
      if (permissionStatus.state === 'granted') {
        // Microphone access already granted
        console.log('Access granted');
        toggleButtons();
      }
    });
}

// Function to toggle buttons
function toggleButtons() {
  microphoneButton.style.display = 'none';
  startSpeakingButton.style.display = 'block';
}
