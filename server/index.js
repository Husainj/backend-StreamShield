// server.js
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const { spawn } = require('child_process');

const app = express();
const server = http.createServer(app);
const io = socketIo(server , {
    cors: {
      origin: 'http://localhost:5173', // or '*' to allow any origin
      methods: ['GET', 'POST'],
    },
  });

// --- Configuration ---
// Replace with your YouTube live stream key.
const STREAM_KEY = 'cgfh-7gcv-0d5c-7r2t-fvf2';
const YOUTUBE_RTMP_URL = `rtmp://a.rtmp.youtube.com/live2/${STREAM_KEY}`;

// This variable will hold the FFmpeg process instance.
let ffmpegProcess = null;

// Serve static files from the "public" folder.
app.use(express.static('public'));

// Socket.IO connection handler.
io.on('connection', (socket) => {
  console.log('Client connected');

  // When the client indicates that streaming is about to begin.
  socket.on('start-stream', () => {
    if (!ffmpegProcess) {
      console.log('Starting FFmpeg process to stream to YouTube...');
      ffmpegProcess = spawn('ffmpeg', [
        '-re', // Read input at native frame rate.
        '-f', 'webm', // Input format is webm.
        '-i', 'pipe:0', // Read from STDIN.
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-tune', 'zerolatency',
        '-c:a', 'aac',
        '-ar', '44100',
        '-b:a', '128k',
        '-f', 'flv', // Output format is flv (RTMP).
        YOUTUBE_RTMP_URL
      ]);

      // Log FFmpeg messages.
      ffmpegProcess.stderr.on('data', (data) => {
        console.log(`FFmpeg stderr: ${data}`);
      });

      ffmpegProcess.on('close', (code) => {
        console.log(`FFmpeg process closed with code ${code}`);
        ffmpegProcess = null;
      });
    }
  });

  // Receive video chunks from the client.
  socket.on('stream-data', (chunk) => {
    // chunk is an ArrayBuffer; convert it to a Buffer and write to FFmpeg STDIN.
    if (ffmpegProcess && ffmpegProcess.stdin.writable) {
      ffmpegProcess.stdin.write(Buffer.from(chunk));
    }
  });

  // When the client stops streaming.
  socket.on('stop-stream', () => {
    if (ffmpegProcess) {
      console.log('Stopping FFmpeg process...');
      ffmpegProcess.stdin.end();
      ffmpegProcess = null;
    }
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected');
    if (ffmpegProcess) {
      ffmpegProcess.stdin.end();
      ffmpegProcess = null;
    }
  });
});

// Start the server.
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
