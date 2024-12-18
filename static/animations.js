const avatar = document.getElementById('avatar');
const userInput = document.getElementById('user-input');
const outputArea = document.getElementById('text-output');
let voiceButton = null;
let audioStream = null; // to handle voice input
let clearButton = null;

function updateAvatar(state) {
    let imgSrc;
    switch (state) {
        case 'typing':
            imgSrc = '/static/avatar/typing.webp';
            break;
        case 'listening':
            imgSrc = '/static/avatar/listening.webp';
            break;
        case 'speaking':
            imgSrc = '/static/avatar/speaking.webp';
            break;
        default:
            imgSrc = '/static/avatar/idle.webp';
    }
    avatar.src = imgSrc;
}

function sendInput() {
    updateAvatar('typing');
    const message = userInput.value.trim();
    if (message) {
        fetch('/process', {
            method: 'POST',
            headers: {
                 'Content-Type': 'application/json',
             },
           body: JSON.stringify({ message: message }),
        })
           .then(response => response.json())
            .then(data => {
               updateAvatar('speaking');
              addTextToOutput(data.response);
            })
            .catch(error => {
                 console.error('Error:', error);
                  updateAvatar('idle');
             })
            .finally(() => {
                 userInput.value = '';
            });
    }
}

function startVoiceInput(){
    updateAvatar('listening');
           fetch('/voice', {
                method: 'POST',
            })
                .then(response => response.json())
                .then(data => {
                    updateAvatar('speaking');
                    if(data.command){
                      addTextToOutput(data.command);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                      updateAvatar('idle');
                });
}

function addTextToOutput(text) {
    const newParagraph = document.createElement('p');
    newParagraph.textContent = text;
    outputArea.appendChild(newParagraph);
    outputArea.scrollTop = outputArea.scrollHeight; // Scroll to the bottom
}

function clearOutput(){
    outputArea.innerHTML = "";
    updateAvatar('idle');
     // Clear the input box
    userInput.value = '';
      // Stop the Speech if it's talking
     if (window.speechSynthesis) {
          window.speechSynthesis.cancel();
     }
       // Stop the listening and make sure the avatar will stop listening
      if (audioStream) {
        if (audioStream.getTracks) { // check if getTracks method exists
         audioStream.getTracks().forEach(track => track.stop());
         }
        audioStream = null;
       }
      fetch('/clear', {
                method: 'POST',
            }).catch(error => {
                 console.error('Error:', error);
             }); // Send stop to backend

}
// Typing animation
userInput.addEventListener('input', function () {
    if(userInput.value.trim().length > 0){
         updateAvatar('typing');
     }else{
         updateAvatar('idle');
     }
});

// Keep Listening animation for voice button
document.addEventListener('DOMContentLoaded', function() {
    voiceButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent === "Voice"); // gets the voice button
    voiceButton.addEventListener('click', function () {
        updateAvatar('listening');
        setTimeout(() => {
            updateAvatar('idle');
        }, 1000);
    });
     clearButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent === "Clear");
     clearButton.addEventListener('click', clearOutput);
});