import React, { useState } from "react";
import axios from "axios";

const HandleAudio = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // Base URL for your backend (adjust this if your server runs on a different port or domain)
  const baseUrl = "http://localhost:3000";

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "http://localhost:3000/api/upload",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      setResult(response.data);
      console.log("Response from server: ", response.data);
    } catch (err) {
      setError("An error occurred while processing the file");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to extract filename from path
  const getFileName = (filePath) => {
    return filePath.split("/").pop();
  };

  const handleDownload = (url, fileName) => {
    // Create a temporary link and trigger a download for Cloudinary URLs
    fetch(url)
      .then((response) => response.blob())
      .then((blob) => {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = fileName; // Use the filename from the URL or a custom name
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link); // Clean up
      })
      .catch((err) => {
        console.error("Download failed:", err);
        setError("Failed to download the file");
      });
  };

  return (
    <div className="file-upload">
      <form onSubmit={handleSubmit}>
        <input type="file" accept="audio/*,video/*" onChange={handleFileChange} />
        <button type="submit" disabled={loading}>
          {loading ? "Processing..." : "Upload & Censor"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {result && (
        <div className="result">
          <p>{result.message}</p>
          {/* <a
            href={`${baseUrl}${result.censoredFile}`}
            download={getFileName(result.censoredFile)}
          >
            Download Censored File
          </a> */}
          <button
            onClick={() => handleDownload(result.censoredFile, getFileName(result.censoredFile))}
          >
            Download Censored Video
          </button>
          <br />
          {/* <a
            href={`${baseUrl}${result.transcript}`}
            download={getFileName(result.transcript)}
          >
            Download Transcript
          </a> */}
    </div>
      )}
    </div>
  );
};

export default HandleAudio;