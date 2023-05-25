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
let mediaRecorder;
let recordedChunks = [];

// Button click event listener
microphoneButton.addEventListener('click', function() {
  initializeMediaRecorder();
});

// Checking if microphone access was already granted
if (navigator.permissions) {
  navigator.permissions.query({ name: 'microphone' })
    .then(function(permissionStatus) {
      if (permissionStatus.state === 'granted') {
        // Microphone access already granted
        console.log('Access granted');
        initializeMediaRecorder();
        toggleButtons();
      }
    });
}

// Function to initialize MediaRecorder
function initializeMediaRecorder() {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(function(stream) {
      // Microphone access granted
      console.log('Access granted');

      // Create MediaRecorder instance
      mediaRecorder = new MediaRecorder(stream);

      // Collect recorded audio data
      mediaRecorder.ondataavailable = function(e) {
        recordedChunks.push(e.data);
      };

      // Event triggered when recording is stopped
      mediaRecorder.onstop = function() {
        // Create a blob from the recorded audio data
        const recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' });

        // Create a FormData instance
        let formData = new FormData();

        // Append the audio file and question_set_id to the form
        formData.append('audio', recordedBlob);
        formData.append('question_set_id', questionSet['question_id']);

        // Send the POST request
        fetch('/section/speaking/practice', {
          method: 'POST',
          body: formData
        })
        .then(response => {
          if (response.redirected) {
            window.location.href = response.url;
          }
        })
        .catch(error => console.error(error));
      };
    })
    .catch(function(err) {
      // Microphone access denied or error occurred
      console.log('Access denied');
    });
}

// Function to toggle buttons
function toggleButtons() {
  microphoneButton.style.display = 'none';
  startSpeakingButton.style.display = 'block';
}

// Start speaking button click event listener
startSpeakingButton.addEventListener('click', function() {
  // Start recording
  mediaRecorder.start();

  // Change the time limit text and show the recording dot
  timeLimitText.textContent = "Recording in progress...";
  recordingDot.style.display = 'inline-block';

  // Display question count and first question
  questionCount.style.display = 'block';
  questionCount.textContent = `Question ${currentQuestionIndex + 1} of ${questionSet.questions.length}`;
  questionText.textContent = questionSet.questions[currentQuestionIndex];

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
  questionCount.textContent = `Question ${currentQuestionIndex + 1} of ${questionSet.questions.length}`;

  if (currentQuestionIndex < questionSet.questions.length) {
    // Display next question
    questionText.textContent = questionSet.questions[currentQuestionIndex];
  }

  // Show complete practice button if we are at the last question
  if (currentQuestionIndex == questionSet.questions.length - 1) {
    nextQuestionButton.style.display = 'none';
    completePracticeButton.style.display = 'block';
  }
});

// Complete practice button click event listener
completePracticeButton.addEventListener('click', function() {
  // Stop recording
  mediaRecorder.stop();

  // Add spinner to the button
  completePracticeButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing your answers...';
  completePracticeButton.classList.add("disabled");
  completePracticeButton.setAttribute("disabled", "disabled");


  // Reset time limit text, and stop the timer
  timeLimitText.textContent = "Time limit: 5 minutes";
  recordingDot.style.display = 'none';
  clearInterval(timerInterval);

  // Here goes the rest of your code for completing the practice...
});
