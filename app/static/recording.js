const button = document.getElementById('microphoneButton');

// asking user permission to use microphone
button.addEventListener('click', function () {
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(function(stream) {
    // здесь вы можете использовать поток
    console.log('Access granted');
  })
  .catch(function(err) {
    // ошибка обработки запроса
    console.log('Access denied');
  });
});