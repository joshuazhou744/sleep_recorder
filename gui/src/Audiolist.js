import React, {useState,useEffect} from 'react'
import axios from 'axios'

function Audiolist() {
    const [recording, setRecording] = useState(false)
    const [audioFiles, setAudioFiles] = useState([]);

    // Fetch audio files from FastAPI backend
    useEffect(() => {
        const fetchAudioFiles = async () => {
            try {
                const response = await axios.get('http://localhost:8080/api/audio-files')
                setAudioFiles(response.data.files)
            } catch (error) {
                console.error("Error fetching files", error)
            }
        }
        fetchAudioFiles()
        const interval = setInterval(fetchAudioFiles, 15000); // Fetch every 15 seconds

        return () => clearInterval(interval);
    }, [])

    const startRecording = async () => {
        try {
            await axios.post("http://localhost:8080/api/start-recording")
            setRecording(true)
            console.log("started recording")
        } catch (error) {
            console.error("Error starting recording", error)
        }
    }

    const stopRecording = async () => {
        try {
            await axios.post("http://localhost:8080/api/stop-recording")
            setRecording(false)
            console.log("stopped recording")
        } catch (error) {
            console.error("Error stopping recording", error)
        }
    }

    const playAudio = async (file) => {
        try {
            await axios.post("http://localhost:8080/api/play-audio", {file})
            console.log("Played file " + file)
        } catch (error) {
            console.error("Error playing file", error)
        }
    }

  return (
    <div>
      <h2>Detected Audio Files</h2>
      <button onClick={startRecording}>Start Recording</button>
      <button onClick={stopRecording}>Stop Recording</button>
      {recording && <div className='warn'>Cannot play while recording active</div>}
      <ul>
        {audioFiles.map((file, index) => (
            <li key={index}>
                {file}
                <button onClick={() => playAudio(file)} disabled={recording}>Play</button>
            </li>
        ))}
      </ul>
    </div>
  )
}

export default Audiolist
