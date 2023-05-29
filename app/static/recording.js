// Button elements
const microphoneButton = document.getElementById('microphoneButton');
const startSpeakingButton = document.getElementById('startSpeakingButton');
const nextQuestionButton = document.getElementById('nextQuestionButton');
const completePracticeButton = document.getElementById('completePracticeButton');
const startCardAnswerButton = document.getElementById('startCardAnswerButton');

// Timer elements
const timer = document.getElementById('timer');
const timerContainer = document.getElementById('timerContainer');
const timeLimit = practice['answer_time_limit']

// Card elements
const cardHeader = document.getElementById('cardHeader');
const cardTitle = document.getElementById('cardTitle');
const cardText = document.getElementById('cardText');
const cardFooterText = document.getElementById('cardFooterText');
const topicQuestions = document.getElementById('topicQuestions');
const recordingIndicator = document.getElementById('recordingIndicator');

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
      toggleButtons();

      // Create MediaRecorder instance
      mediaRecorder = new MediaRecorder(stream);

      // Start event
      mediaRecorder.onstart = function() {
        // Show the recording dot
        cardFooterText.style.display = 'none';
        recordingIndicator.style.display = 'block';
      };

      // Collect recorded audio data
      mediaRecorder.ondataavailable = function(e) {
        recordedChunks.push(e.data);
      };

      // Event triggered when recording is stopped
      mediaRecorder.onstop = function() {
        // Hide the recording dot
        recordingIndicator.style.display = 'none';

        // Create a blob from the recorded audio data
        const recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' });

        // Create a FormData instance
        let formData = new FormData();

        // Append the audio file and question_set_id to the form
        formData.append('audio', recordedBlob);
        formData.append('question_set_id', practice['question_id']);

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
  startSpeakingButton.style.display = 'inline-block';
}

// Start speaking button click event listener
startSpeakingButton.addEventListener('click', function() {
  if (practice.part == 1) {
    // Start recording
    mediaRecorder.start();

    // Display question count and first question
    cardHeader.textContent = `Question ${currentQuestionIndex + 1} of ${practice.questions.length}`;
    cardTitle.textContent = practice.questions[currentQuestionIndex];

    // Hide start speaking button and show next question button
    startSpeakingButton.style.display = 'none';
    nextQuestionButton.style.display = 'inline-block';
    cardText.style.display = 'none';

    // Show timer and start countdown
    timerContainer.style.visibility = 'visible';
    startTimer(timeLimit * 60, timer);
  }
  else if (practice.part == 2) {
  // Display card and hide other elements
    startCardAnswerButton.style.display = 'inline-block';
    topicQuestions.style.display = 'block';
    cardTitle.textContent = practice.topic
    cardText.textContent = "You should say:"
    startSpeakingButton.style.display = 'none';

    // Show timer and start countdown
    clearInterval(timerInterval);
    timerContainer.style.visibility = 'visible';
    startTimer(60, timer);

  }
});

// Start cue card answer button click event listener
startCardAnswerButton.addEventListener('click', function() {
  // Update button
  startCardAnswerButton.style.display = 'none';
  completePracticeButton.style.display = 'inline-block';

  // Show timer and start countdown
  clearInterval(timerInterval);
  timerContainer.style.visibility = 'visible';
  startTimer(120, timer);
  cardFooterText.textContent = "Recording in progress...";

  // Start recording
  mediaRecorder.start();

});

// Timer function
function startTimer(duration, display) {
  let timer = duration, minutes, seconds;

  // Calculate and display initial time
  minutes = parseInt(timer / 60, 10);
  seconds = parseInt(timer % 60, 10);
  minutes = minutes < 10 ? "0" + minutes : minutes;
  seconds = seconds < 10 ? "0" + seconds : seconds;
  display.textContent = minutes + ":" + seconds;

  // Start countdown
  timerInterval = setInterval(function () {
    // Decrement timer first before recalculating minutes and seconds
    --timer;

    minutes = parseInt(timer / 60, 10);
    seconds = parseInt(timer % 60, 10);
    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;
    display.textContent = minutes + ":" + seconds;

    if (timer < 0) {
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
  cardHeader.textContent = `Question ${currentQuestionIndex + 1} of ${practice.questions.length}`;

  if (currentQuestionIndex < practice.questions.length) {
    // Display next question
    cardTitle.textContent = practice.questions[currentQuestionIndex];
  }

  // Show complete practice button if we are at the last question
  if (currentQuestionIndex == practice.questions.length - 1) {
    nextQuestionButton.style.display = 'none';
    completePracticeButton.style.display = 'inline-block';
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
  cardFooterText.style.display = 'inline-block';
  cardFooterText.textContent = "Just in time!";
  clearInterval(timerInterval);

  // Here goes the rest of your code for completing the practice...
});