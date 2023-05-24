const microphoneButton = document.getElementById('microphoneButton');
const startSpeakingButton = document.getElementById('startSpeakingButton');
const nextQuestionButton = document.getElementById('nextQuestionButton');
const completePracticeButton = document.getElementById('completePracticeButton');
const questionText = document.getElementById('questionText');
const timeLimitText = document.getElementById('timeLimitText');
const recordingDot = document.querySelector('.recording-dot');
const questionCount = document.getElementById('questionCount');
const timer = document.getElementById('timer');
const timerContainer = document.getElementById('timerContainer');
let currentQuestionIndex = 0;
let timerInterval;

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

  // Display question count and first question
  questionCount.style.display = 'block';
  questionCount.textContent = `Question ${currentQuestionIndex + 1} of ${questionSet.length}`;
  questionText.textContent = questionSet[currentQuestionIndex];

  // Hide start speaking button and show next question button
  startSpeakingButton.style.display = 'none';
  nextQuestionButton.style.display = 'block';

  // Show timer and start countdown
  timerContainer.style.visibility = 'visible';
  startTimer(5 * 60, timer);
});

// Timer function
function startTimer(duration, display) {
  let timer = duration, minutes, seconds;
  timerInterval = setInterval(function () {
    minutes = parseInt(timer / 60, 10);
    seconds = parseInt(timer % 60, 10);

    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;

    display.textContent = minutes + ":" + seconds;

    if (--timer < 0) {
      // Timer has finished
      clearInterval(timerInterval);

      // Place for your code to execute after the timer finishes
    }
  }, 1000);
}

// Next question button click event listener
nextQuestionButton.addEventListener('click', function() {
  // Increment question index
  currentQuestionIndex++;

  // Display question count and next question
  questionCount.textContent = `Question ${currentQuestionIndex + 1} of ${questionSet.length}`;

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
  // Stop recording, reset time limit text, and stop the timer
  timeLimitText.textContent = "Time limit: 5 minutes";
  recordingDot.style.display = 'none';
  clearInterval(timerInterval);

  // Here goes the rest of your code for completing the practice...
});
