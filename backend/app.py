from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import soundfile as sf
import sounddevice as sd
import os
import threading
import numpy as np
from datetime import datetime as dt
from pydantic import BaseModel
import signal
import time

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audio_dir = "audio"
if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)

duration = 5 # [] second recording chunks
sample_rate = 44100  # samples of a waveform per second to create an accurate signal
energy_threshold = 0.1  # volume threshold to record

audio_files = []
recording_active = False

def detect_sound():
    global recording_active
    while True:
        if recording_active:
            print("Listening")

            audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
            sd.wait()

            if np.isnan(audio).any():
                print("Warning: audio contains NaN values, skipping detection")
                continue

            rms_energy = np.sqrt(np.mean(audio**2))

            if rms_energy > energy_threshold:
                print(f"Sound detected: Energy: {rms_energy}")

                file_name = get_file_name()
                sf.write(file_name, audio, sample_rate)
                print(f"Audio file saved to {file_name}")

                audio_files.append(file_name)
            else:
                print(f"No significant sound detected. Energy: {rms_energy}")
        time.sleep(0.5)

def get_file_name():
    now = dt.now().strftime("%m-%d_%Hh-%Mm-%Ss")
    file_name = os.path.join(audio_dir, f"{now}.wav")
    return file_name

# api request body model for playing audio
class PlayAudioRequest(BaseModel):
    file: str

app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

# Route to get the list of audio files
@app.get("/api/audio-files")
async def get_audio_files():
    files = [f for f in os.listdir(audio_dir) if os.path.isfile(os.path.join(audio_dir, f))]
    return {
        "files": files
    }


# Route to play a selected audio file
@app.post("/api/play-audio")
async def play_audio(request: PlayAudioRequest):
    file_name = "audio/" + request.file

    if not os.path.exists(file_name):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        audio_data, sample_rate = sf.read(file_name)
        sd.play(audio_data, sample_rate)
        sd.wait()
        return {"message": f"Played audio from {file_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/start-recording")
async def start_recording():
    global recording_active
    if recording_active:
        return {"message": "Recording is already active"}
    recording_active = True
    return {"message": "Recording started"}

@app.post("/api/stop-recording")
async def stop_recording():
    global recording_active
    if not recording_active:
        return {"message": "Recording is already inactive"}
    recording_active = False
    return {"message": "Recording stopped"}

def handle_exit(sig, frame):
    print("Shutting down")
    sd.stop()
    os._exit(0)

signal.signal(signal.SIGINT, handle_exit)


if __name__ == "__main__":
    detection_thread = threading.Thread(target=detect_sound, daemon=True)
    detection_thread.start()

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)