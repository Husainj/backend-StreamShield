// index.js
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const { spawn } = require('child_process');
const multer = require('multer');
const { PythonShell } = require('python-shell');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const cloudinary = require('cloudinary').v2;

// Configure Cloudinary
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET
});

app.use(cors({
  origin: process.env.CORS_ORIGIN,
  credentials: true
}));

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, 'uploads/'),
  filename: (req, file, cb) => cb(null, `${Date.now()}-${file.originalname}`)
});
const upload = multer({ storage });

// Ensure uploads directory exists
if (!fs.existsSync('uploads')) fs.mkdirSync('uploads');

const io = socketIo(server, {
  cors: {
    origin: 'http://localhost:5173', // or '*' to allow any origin
    methods: ['GET', 'POST'],
  },
});

// --- Configuration ---
// Replace with your YouTube live stream key.
const STREAM_KEY = '7q9c-x9e7-7ykj-rs2d-dwbe';
const YOUTUBE_RTMP_URL = `rtmp://a.rtmp.youtube.com/live2/${STREAM_KEY}`;

// This variable will hold the FFmpeg process instance.
let ffmpegProcess = null;

// Socket.IO connection handler for streaming
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

// Update /api/upload endpoint (for file uploads, separate from streaming)
app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    const filePath = req.file.path; // e.g., 'uploads/123456789-rocktest.mp4'
    const originalName = req.file.originalname;
    const outputFileName = `${Date.now()}-censored-${originalName.split('.').slice(0, -1).join('.')}.mp4`;

    const censoredFilePath = path.join('uploads', outputFileName);

    const options = {
      args: [
        path.resolve(filePath),
        path.resolve(censoredFilePath)
      ],
      cwd: path.resolve(__dirname, 'StreamShield') // Run Python in StreamShield directory
    };

    console.log('Running Python script with args:', options.args);
    const pythonResult = await PythonShell.run('main.py', options);
    console.log('Python script output:', pythonResult);

    if (!fs.existsSync(censoredFilePath)) {
      throw new Error(`Output file not found at ${censoredFilePath}`);
    }

    const cloudinaryResult = await cloudinary.uploader.upload(censoredFilePath, {
      resource_type: 'video', // Ensure it's treated as a video
      folder: 'censored_videos', // Optional: organize in a folder
      public_id: outputFileName.split('.mp4')[0] // Optional: set a specific public ID
    });

    fs.unlinkSync(censoredFilePath);

    res.json({
      message: 'File processed successfully',
      censoredFile: cloudinaryResult.secure_url
    });
  } catch (error) {
    console.error('Error processing file:', error);
    res.status(500).json({ error: 'Processing failed', details: error.message });
  }
});

app.use('/uploads', express.static('uploads'));

// Start the server.
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});