// Voice Assistant powered by native HTML5 Web Speech API
document.addEventListener('DOMContentLoaded', () => {
    const speakBtn = document.getElementById('speak-btn');
    const listenBtn = document.getElementById('listen-btn');
    const speechStatus = document.getElementById('speech-status');
    const waveContainer = document.querySelector('.voice-wave');
    
    // Config values (passed from HTML attributes if present)
    const container = document.getElementById('voice-assistant-config');
    const studentName = container ? container.getAttribute('data-name') : 'Student';
    const todayFocus = container ? container.getAttribute('data-focus') : '';

    // TTS (Speech Synthesis)
    function speak(text) {
        if (!('speechSynthesis' in window)) {
            console.warn("Speech synthesis not supported in this browser.");
            return;
        }
        
        // Cancel current speak tasks
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.05;
        
        // Use a high-quality English voice if available
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            voice.name.includes('Google US English') || 
            voice.name.includes('Microsoft Zira') || 
            voice.lang.startsWith('en')
        );
        if (preferredVoice) utterance.voice = preferredVoice;
        
        window.speechSynthesis.speak(utterance);
    }

    // Auto-greet on AI Advisor load
    if (container && container.getAttribute('data-autogreet') === 'true') {
        setTimeout(() => {
            let greeting = `Good morning ${studentName}! `;
            if (todayFocus) {
                greeting += `Today's study focus is ${todayFocus}. Let's make it a productive session!`;
            } else {
                greeting += "Welcome back. Let's analyze your study weaknesses today.";
            }
            speak(greeting);
        }, 800);
    }

    if (speakBtn) {
        speakBtn.addEventListener('click', () => {
            let message = `Hello ${studentName}. `;
            if (todayFocus) {
                message += `Today your schedule focuses on ${todayFocus}. `;
            }
            message += "I am here to guide your study routine. Keep up the consistency!";
            speak(message);
        });
    }

    // STT (Speech Recognition)
    if (listenBtn) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            listenBtn.style.display = 'none';
            if (speechStatus) {
                speechStatus.textContent = "Speech recognition is not supported in this browser (Use Chrome/Edge).";
            }
            return;
        }
        
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        
        recognition.onstart = () => {
            if (waveContainer) waveContainer.classList.add('active');
            if (speechStatus) speechStatus.textContent = "Listening for command...";
        };
        
        recognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error);
            if (speechStatus) speechStatus.textContent = "Error: " + event.error;
            if (waveContainer) waveContainer.classList.remove('active');
        };
        
        recognition.onend = () => {
            if (waveContainer) waveContainer.classList.remove('active');
        };
        
        recognition.onresult = (event) => {
            const resultText = event.results[0][0].transcript.toLowerCase();
            if (speechStatus) {
                speechStatus.textContent = `You said: "${resultText}"`;
            }
            
            // Handle voice commands
            handleVoiceCommand(resultText);
        };
        
        listenBtn.addEventListener('click', () => {
            try {
                recognition.start();
            } catch (err) {
                recognition.stop();
            }
        });
    }

    function handleVoiceCommand(command) {
        // Redirection Commands
        if (command.includes('dashboard') || command.includes('home') || command.includes('main page')) {
            speak("Redirecting to dashboard.");
            setTimeout(() => window.location.href = '/dashboard', 1000);
        }
        else if (command.includes('calendar') || command.includes('schedule') || command.includes('timetable')) {
            speak("Opening your 30-day study calendar.");
            setTimeout(() => window.location.href = '/calendar', 1000);
        }
        else if (command.includes('progress') || command.includes('chart') || command.includes('graph')) {
            speak("Loading your progress reports.");
            setTimeout(() => window.location.href = '/progress', 1000);
        }
        else if (command.includes('advisor') || command.includes('ai') || command.includes('weakness')) {
            speak("Opening AI weakness analysis.");
            setTimeout(() => window.location.href = '/ai-advisor', 1000);
        }
        // Pomodoro Commands
        else if (command.includes('start timer') || command.includes('start pomodoro') || command.includes('focus timer')) {
            speak("Starting your Pomodoro timer.");
            if (window.vocalTriggerStartPomodoro) {
                window.vocalTriggerStartPomodoro();
            }
        }
        else if (command.includes('hello') || command.includes('hi ')) {
            speak(`Hello ${studentName}! How can I help you today?`);
        }
        else {
            speak("Command not recognized. Try saying 'open schedule' or 'start timer'.");
        }
    }
});
