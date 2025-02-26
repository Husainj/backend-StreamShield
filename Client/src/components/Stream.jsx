// src/Stream.js
import React, { useState, useRef, useEffect } from 'react';
import { io } from 'socket.io-client';

// Connect to the backend (adjust the URL if your backend is hosted elsewhere)
const socket = io('http://localhost:3000');

function Stream() {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);

  // Initialize screen capture on mount
  useEffect(() => {
    async function initScreenCapture() {
      try {
        // Use getDisplayMedia for screen sharing (request user permission)
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true, // Optional: include system audio if supported
        });
        setStream(screenStream);
        if (videoRef.current) {
          videoRef.current.srcObject = screenStream;
        }

        // Handle screen sharing stop (user closes the sharing dialog)
        screenStream.getVideoTracks()[0].onended = () => {
          stopStreaming();
          setStream(null);
          alert('Screen sharing has ended.');
        };
      } catch (err) {
        console.error('Error accessing screen capture.', err);
        alert('Could not access screen sharing. Please allow screen capture permissions.');
      }
    }
    initScreenCapture();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Start streaming: signal the server, then begin recording screen chunks
  const startStreaming = () => {
    if (!stream) return;

    // Tell the backend to start its FFmpeg and Python processes
    socket.emit('start-stream');

    // Create a MediaRecorder. Use 'video/webm' for compatibility with screen sharing
    const recorder = new MediaRecorder(stream, {
      mimeType: 'video/webm; codecs=vp8,opus', // VP8 video and Opus audio for WebM
    });

    // When a data chunk is available, read it as an ArrayBuffer and send it to the backend
    recorder.addEventListener('dataavailable', (event) => {
      if (event.data && event.data.size > 0) {
        const reader = new FileReader();
        reader.onload = () => {
          socket.emit('stream-data', reader.result);
        };
        reader.readAsArrayBuffer(event.data);
      }
    });

    // Start recording. Send chunks every 1 second (adjust as needed)
    recorder.start(1000);
    setMediaRecorder(recorder);
    setIsStreaming(true);
  };

  // Stop streaming: stop the recorder, end tracks, and signal the backend
  const stopStreaming = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      socket.emit('stop-stream'); // Tell the backend to stop
      setMediaRecorder(null);
      setStream(null);
      setIsStreaming(false);
    }
  };

  return (
    <div className="App">
      <h1>YouTube Live Streaming (Screen Sharing)</h1>
      <video
        ref={videoRef}
        autoPlay
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

export default Stream;