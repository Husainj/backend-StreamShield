// src/App.js
import React, { useState, useRef, useEffect } from 'react';
import { io } from 'socket.io-client';
import './App.css';

// Connect to the backend (adjust the URL if your backend is hosted elsewhere)
const socket = io('http://localhost:3000');

function App() {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);

  // Initialize user media (webcam & mic) on mount.
  useEffect(() => {
    async function initMedia() {
      try {
        const userMedia = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        });
        setStream(userMedia);
        if (videoRef.current) {
          videoRef.current.srcObject = userMedia;
        }
      } catch (err) {
        console.error('Error accessing media devices.', err);
        alert('Could not access webcam/microphone.');
      }
    }
    initMedia();
  }, []);

  // Start streaming: signal the server, then begin recording in chunks.
  const startStreaming = () => {
    if (!stream) return;

    // Tell the backend to start its FFmpeg process.
    socket.emit('start-stream');

    // Create a MediaRecorder. The MIME type might need adjustment based on browser support.
    const recorder = new MediaRecorder(stream, {
      mimeType: 'video/webm; codecs=vp8,opus',
    });

    // When a data chunk is available, read it as an ArrayBuffer and send it to the backend.
    recorder.addEventListener('dataavailable', (event) => {
      if (event.data && event.data.size > 0) {
        const reader = new FileReader();
        reader.onload = () => {
          socket.emit('stream-data', reader.result);
        };
        reader.readAsArrayBuffer(event.data);
      }
    });

    // Start recording. The parameter (in ms) specifies how often dataavailable events are triggered.
    recorder.start(1000);
    setMediaRecorder(recorder);
    setIsStreaming(true);
  };

  // Stop streaming: stop the recorder and signal the backend.
  const stopStreaming = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      socket.emit('stop-stream');
      setMediaRecorder(null);
      setIsStreaming(false);
    }
  };

  return (
    <div className="App">
      <h1>YouTube Live Streaming (React)</h1>
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        style={{ width: '640px', height: '480px', border: '1px solid #ccc' }}
      ></video>
      <div style={{ marginTop: '20px' }}>
        <button onClick={startStreaming} disabled={isStreaming}>
          Start Streaming
        </button>
        <button onClick={stopStreaming} disabled={!isStreaming}>
          Stop Streaming
        </button>
      </div>
    </div>
  );
}

export default App;
