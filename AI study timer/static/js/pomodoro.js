document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('pomodoro-start');
    const pauseBtn = document.getElementById('pomodoro-pause');
    const resetBtn = document.getElementById('pomodoro-reset');
    const timerLabel = document.getElementById('pomodoro-label');
    const minutesDisplay = document.getElementById('pomodoro-minutes');
    const secondsDisplay = document.getElementById('pomodoro-seconds');
    const progressCircle = document.getElementById('pomodoro-progress');
    
    if (!startBtn) return; // Not on dashboard page

    let timerInterval = null;
    let isRunning = false;
    let isStudyMode = true; // true = study (25m), false = break (5m)
    
    const STUDY_TIME = 25 * 60; // 25 minutes
    const BREAK_TIME = 5 * 60;  // 5 minutes
    let timeRemaining = STUDY_TIME;
    let totalTime = STUDY_TIME;

    // SVG dasharray configuration
    const circleLength = 603; // 2 * PI * 96

    // Web Audio Synthesizer for alarm (no external asset needed)
    function playAlarm() {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            
            // Double beep sound
            const playBeep = (delay, frequency, duration) => {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                
                osc.type = 'sine';
                osc.frequency.value = frequency;
                
                gain.gain.setValueAtTime(0, audioCtx.currentTime + delay);
                gain.gain.linearRampToValueAtTime(0.3, audioCtx.currentTime + delay + 0.05);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + delay + duration);
                
                osc.start(audioCtx.currentTime + delay);
                osc.stop(audioCtx.currentTime + delay + duration);
            };
            
            playBeep(0, 880, 0.3);
            playBeep(0.4, 880, 0.3);
        } catch (e) {
            console.error("Audio error:", e);
        }
    }

    function updateDisplay() {
        const mins = Math.floor(timeRemaining / 60);
        const secs = timeRemaining % 60;
        
        minutesDisplay.textContent = String(mins).padStart(2, '0');
        secondsDisplay.textContent = String(secs).padStart(2, '0');
        
        // Progress ring logic
        const fraction = timeRemaining / totalTime;
        const offset = circleLength * (1 - fraction);
        progressCircle.style.strokeDashoffset = offset;
    }

    function switchMode() {
        playAlarm();
        isStudyMode = !isStudyMode;
        
        if (isStudyMode) {
            timeRemaining = STUDY_TIME;
            totalTime = STUDY_TIME;
            timerLabel.textContent = "Focus Time";
            timerLabel.style.color = "#3b82f6";
            progressCircle.style.stroke = "#3b82f6";
            alert("Break finished! Starting a new 25-minute Study Session.");
        } else {
            timeRemaining = BREAK_TIME;
            totalTime = BREAK_TIME;
            timerLabel.textContent = "Short Break";
            timerLabel.style.color = "#10b981";
            progressCircle.style.stroke = "#10b981";
            
            // Sync with DB
            syncCompletedPomodoro();
            alert("Focus session complete! Time for a 5-minute break.");
        }
        
        updateDisplay();
        startTimer();
    }

    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        
        isRunning = true;
        startBtn.style.display = 'none';
        pauseBtn.style.display = 'inline-block';
        
        timerInterval = setInterval(() => {
            timeRemaining--;
            if (timeRemaining <= 0) {
                clearInterval(timerInterval);
                switchMode();
            } else {
                updateDisplay();
            }
        }, 1000);
    }

    function pauseTimer() {
        clearInterval(timerInterval);
        isRunning = false;
        startBtn.style.display = 'inline-block';
        pauseBtn.style.display = 'none';
    }

    function resetTimer() {
        clearInterval(timerInterval);
        isRunning = false;
        isStudyMode = true;
        timeRemaining = STUDY_TIME;
        totalTime = STUDY_TIME;
        timerLabel.textContent = "Focus Time";
        timerLabel.style.color = "#3b82f6";
        progressCircle.style.stroke = "#3b82f6";
        
        startBtn.style.display = 'inline-block';
        pauseBtn.style.display = 'none';
        
        updateDisplay();
    }

    function syncCompletedPomodoro() {
        // Post to backend to record completed pomodoro
        fetch('/api/log_pomodoro', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Logged Pomodoro to database successfully.");
                // Dynamically update metrics if elements exist
                const pomodoroCountEl = document.getElementById('metric-pomodoros');
                if (pomodoroCountEl) {
                    pomodoroCountEl.textContent = data.today_count;
                }
                const streakEl = document.getElementById('metric-streak');
                if (streakEl) {
                    streakEl.textContent = data.streak;
                }
            }
        })
        .catch(err => console.error("Error syncing pomodoro:", err));
    }

    // Trigger start from vocal commands
    window.vocalTriggerStartPomodoro = function() {
        if (!isRunning) {
            startTimer();
        }
    };

    startBtn.addEventListener('click', startTimer);
    pauseBtn.addEventListener('click', pauseTimer);
    resetBtn.addEventListener('click', resetTimer);

    // Initial load
    resetTimer();
});
