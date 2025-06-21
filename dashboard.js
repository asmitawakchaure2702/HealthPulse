// Medical Chat Application
document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Initialize DOM elements
    const messagesContainer = document.getElementById('messages');
    const messageForm = document.getElementById('messageForm');
    const userInput = document.getElementById('userInput');
    const voiceButton = document.getElementById('voiceButton');
    const voiceStatus = document.getElementById('voiceStatus');
    let isProcessing = false;

    // Message handling functions
    function addMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        if (type === 'medical-response') {
            messageDiv.innerHTML = DOMPurify.sanitize(formatMedicalResponse(message));
        } else {
            messageDiv.textContent = message;
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function formatMedicalResponse(response) {
        return response.replace(/\n/g, '<br>');
    }

    async function sendMessage(message) {
        if (isProcessing) return;
        isProcessing = true;

        try {
            const response = await fetch('http://localhost:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            addMessage(data.response, 'medical-response');
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request. Please try again.', 'error');
        } finally {
            isProcessing = false;
        }
    }

    // Setup voice recognition
    function setupVoiceRecognition() {
        if (!('webkitSpeechRecognition' in window)) {
            console.log('Speech Recognition not available');
            voiceButton.style.display = 'none';
            return;
        }

        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        function startListening() {
            try {
                recognition.start();
                voiceButton.classList.add('listening');
                voiceStatus.style.display = 'block';
            } catch (error) {
                console.error('Error starting recognition:', error);
                alert('Could not start voice recognition. Please try again.');
            }
        }

        function stopListening() {
            voiceButton.classList.remove('listening');
            voiceStatus.style.display = 'none';
            try {
                recognition.stop();
            } catch (error) {
                console.error('Error stopping recognition:', error);
            }
        }

        voiceButton.addEventListener('click', startListening);

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            stopListening();
            messageForm.dispatchEvent(new Event('submit'));
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            stopListening();
            alert('Speech recognition error. Please try again.');
        };

        recognition.onend = function() {
            stopListening();
        };
    }

    // Setup event listeners
    function setupEventListeners() {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = userInput.value.trim();
            if (message) {
                addMessage(message, 'user');
                userInput.value = '';
                sendMessage(message);
            }
        });

        userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                messageForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    // Initialize everything
    setupVoiceRecognition();
    setupEventListeners();
});
