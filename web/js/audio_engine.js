/**
 * Causalyn Procedural Acoustic Engine (Web Audio API)
 * Inspired by Lightricks LTX audiovisual synchronization principles.
 */

let audioCtx = null;
let masterGain = null;
let analyser = null;
let isMuted = false;
let canvas = null;
let canvasCtx = null;

export function initAudioEngine() {
    canvas = document.getElementById('audio-spectrum-canvas');
    if (canvas) {
        canvasCtx = canvas.getContext('2d');
        renderSpectrum();
    }
}

function getAudioContext() {
    if (!audioCtx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioContextClass();
        masterGain = audioCtx.createGain();
        masterGain.gain.setValueAtTime(0.3, audioCtx.currentTime);

        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        
        masterGain.connect(analyser);
        analyser.connect(audioCtx.destination);
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    return audioCtx;
}

export function toggleMute() {
    isMuted = !isMuted;
    if (masterGain && audioCtx) {
        masterGain.gain.setValueAtTime(isMuted ? 0.0 : 0.3, audioCtx.currentTime);
    }
    return isMuted;
}

/**
 * Crystalline harmonic chord played on invariant satisfaction (κ = 0)
 */
export function playEquilibriumChime() {
    if (isMuted) return;
    try {
        const ctx = getAudioContext();
        const now = ctx.currentTime;

        // Frequencies for a crystalline Emaj9 chord
        const freqs = [659.25, 830.61, 987.77, 1318.51, 1479.98]; // E5, G#5, B5, E6, F#6

        freqs.forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const noteGain = ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, now + idx * 0.03);

            // Soft attack and smooth exponential decay
            noteGain.gain.setValueAtTime(0.001, now + idx * 0.03);
            noteGain.gain.exponentialRampToValueAtTime(0.12, now + idx * 0.03 + 0.04);
            noteGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.2 + idx * 0.1);

            osc.connect(noteGain);
            noteGain.connect(masterGain);

            osc.start(now + idx * 0.03);
            osc.stop(now + 1.5);
        });
    } catch (e) {
        console.warn("[AudioEngine] Playback interrupted:", e);
    }
}

/**
 * Dissonant synthetic glitch played on Paradox Spikes (κ > 0)
 */
export function playParadoxGlitch() {
    if (isMuted) return;
    try {
        const ctx = getAudioContext();
        const now = ctx.currentTime;

        // Low saw oscillator for sub-impact
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const filter = ctx.createBiquadFilter();
        const glitchGain = ctx.createGain();

        osc1.type = 'sawtooth';
        osc1.frequency.setValueAtTime(110, now); // A2
        osc1.frequency.exponentialRampToValueAtTime(45, now + 0.35);

        osc2.type = 'square';
        osc2.frequency.setValueAtTime(155.56, now); // D#3 tritone dissonance

        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(1800, now);
        filter.frequency.exponentialRampToValueAtTime(200, now + 0.3);
        filter.Q.setValueAtTime(8, now);

        glitchGain.gain.setValueAtTime(0.2, now);
        glitchGain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

        osc1.connect(filter);
        osc2.connect(filter);
        filter.connect(glitchGain);
        glitchGain.connect(masterGain);

        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 0.45);
        osc2.stop(now + 0.45);
    } catch (e) {
        console.warn("[AudioEngine] Playback interrupted:", e);
    }
}

/**
 * CEGAR Synthesis resonant upward sweep
 */
export function playSynthesisSweep() {
    if (isMuted) return;
    try {
        const ctx = getAudioContext();
        const now = ctx.currentTime;

        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(300, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.25);

        gain.gain.setValueAtTime(0.01, now);
        gain.gain.linearRampToValueAtTime(0.1, now + 0.05);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

        osc.connect(gain);
        gain.connect(masterGain);

        osc.start(now);
        osc.stop(now + 0.3);
    } catch (e) {
        console.warn("[AudioEngine] Sweep interrupted:", e);
    }
}

/**
 * Live Audio Spectrum Visualizer
 */
function renderSpectrum() {
    requestAnimationFrame(renderSpectrum);
    if (!canvas || !canvasCtx) return;

    canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

    if (!analyser || isMuted) {
        // Draw resting idle line
        canvasCtx.fillStyle = '#CBD5E1';
        for (let i = 0; i < 8; i++) {
            const h = 3;
            canvasCtx.fillRect(i * 6 + 2, canvas.height - h - 2, 4, h);
        }
        return;
    }

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);

    const barWidth = 4;
    let x = 2;

    for (let i = 0; i < 8; i++) {
        const value = dataArray[i * 2] || 0;
        const percent = value / 255;
        const barHeight = Math.max(3, percent * (canvas.height - 4));

        canvasCtx.fillStyle = percent > 0.4 ? '#4F46E5' : '#0284C7';
        canvasCtx.fillRect(x, canvas.height - barHeight - 2, barWidth, barHeight);
        x += barWidth + 2;
    }
}
