const recordButton = document.getElementById("recordButton");
const recordText = document.getElementById("recordText");
const spinner = document.getElementById("spinner");
const loadingText = document.getElementById("loadingText");
let chunks = [];
let mediaRecorder;
let audioStream;
let isRecording = false;

recordButton.addEventListener("click", () => {
  if (!isRecording) {
    startRecording();
  } else {
    stopRecording();
  }
});

async function startRecording() {
  isRecording = true;
  recordText.textContent = "Stop Recording";

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioStream = stream;
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    mediaRecorder.ondataavailable = (event) => {
      chunks.push(event.data);
    };
  } catch (err) {
    console.error("Error: ", err);
  }
}

async function stopRecording() {
  isRecording = false;
  recordButton.disabled = true;
  recordText.style.display = "none";
  spinner.style.display = "inline-block";
  loadingText.style.display = "inline";
  mediaRecorder.stop();
  mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(chunks, { type: "audio/webm" });
    chunks = [];
    audioStream.getTracks().forEach(track => track.stop());
    await sendAudioFile(audioBlob);
  };
}


async function sendAudioFile(blob) {
  const formData = new FormData();
  formData.append("audio", blob, "recording.webm");

  try {
    const response = await fetch("/upload_audio", {
      method: "POST",
      body: formData,
    });
    if (response.status === 200) {
      const resultPage = await response.text();
      const parser = new DOMParser();
      const resultDocument = parser.parseFromString(resultPage, "text/html");
      const resultBody = resultDocument.body.innerHTML;
      document.body.innerHTML = resultBody;

    } else {
      console.error("Error: Failed to process audio file.");
    }
  } catch (err) {
    console.error("Error: ", err);
  }
}


$(document).ready(function() {
    $('input').on('input', function() {
        $(this).removeClass('is-invalid is-valid');
    });
});

