const socket = io();

const logContainer = document.getElementById('log-container');
const transcriptText = document.getElementById('transcript');
const currentEmotion = document.getElementById('current-emotion');
const emotionProgress = document.getElementById('emotion-progress');
const confidenceValue = document.getElementById('conf-value');
const statusText = document.getElementById('status-text');
const heart = document.getElementById('heart');
const emotionTag = document.getElementById('emotion-tag');
const aiContainer = document.querySelector('.ai-container');

socket.on('connect', () => {
    console.log('Connected to CAS-E Backend');
    addLog('SYSTEM: Connection Established', 'system-log');
});

socket.on('new_log', (data) => {
    const type = data.text.startsWith('👤 You:') ? 'user-log' : 'ai-log';
    addLog(data.text, type);
    
    if (type === 'ai-log') {
        speakAnimation(true);
    }
});

socket.on('transcript', (data) => {
    transcriptText.innerText = `"${data.text}"`;
    statusText.innerText = "PROCESSING...";
});

socket.on('speaking_status', (data) => {
    speakAnimation(data.speaking);
    if (!data.speaking) {
        statusText.innerText = "IDLE";
    } else {
        statusText.innerText = "SPEAKING...";
    }
});

socket.on('emotion_update', (data) => {
    // data: { emotion: 'HAPPY', confidence: 0.95 }
    currentEmotion.innerText = data.emotion;
    emotionTag.innerText = data.emotion;
    const confPercent = Math.round(data.confidence * 100);
    confidenceValue.innerText = confPercent;
    emotionProgress.style.width = `${confPercent}%`;
    heart.className = `heart ${data.emotion.toLowerCase()}`;
});

function addLog(text, className) {
    const p = document.createElement('p');
    p.className = className;
    p.innerText = text;
    logContainer.appendChild(p);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function speakAnimation(isSpeaking) {
    if (isSpeaking) {
        aiContainer.classList.add('speaking');
    } else {
        aiContainer.classList.remove('speaking');
    }
}
