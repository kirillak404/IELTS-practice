const microphoneButton = document.getElementById('microphoneButton');
const startSpeakingButton = document.getElementById('startSpeakingButton');
const nextQuestionButton = document.getElementById('nextQuestionButton');
const completePracticeButton = document.getElementById('completePracticeButton');
const questionText = document.getElementById('questionText');
const timeLimitText = document.getElementById('timeLimitText');
const recordingDot = document.querySelector('.recording-dot');
let currentQuestionIndex = 0;

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

// Start speaking button click event listener
startSpeakingButton.addEventListener('click', function() {

  // Change the time limit text and show the recording dot
  timeLimitText.textContent = "Recording in progress...";
  recordingDot.style.display = 'inline-block';

  // Display first question
  questionText.textContent = questionSet[currentQuestionIndex];

  // Hide start speaking button and show next question button
  startSpeakingButton.style.display = 'none';
  nextQuestionButton.style.display = 'block';
});

// Next question button click event listener
nextQuestionButton.addEventListener('click', function() {
  // Increment question index
  currentQuestionIndex++;

  if (currentQuestionIndex < questionSet.length) {
    // Display next question
    questionText.textContent = questionSet[currentQuestionIndex];
  }

  // Show complete practice button if we are at the last question
  if (currentQuestionIndex == questionSet.length - 1) {
    nextQuestionButton.style.display = 'none';
    completePracticeButton.style.display = 'block';
  }
});

// Complete practice button click event listener
completePracticeButton.addEventListener('click', function() {
  // Stop recording and reset time limit text
  timeLimitText.textContent = "Time limit: 5 minutes";
  recordingDot.style.display = 'none';

  // Here goes the rest of your code for completing the practice...
});