from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import librosa
import soundfile as sf
import os
from pydub import AudioSegment
from music21 import stream, note, chord, midi

app = FastAPI()

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    input_path = f"temp_{file.filename}"
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # המרה ל-WAV אם הקובץ אינו בפורמט WAV
    converted_path = input_path
    if not input_path.lower().endswith(".wav"):
        audio = AudioSegment.from_file(input_path)
        converted_path = input_path.rsplit(".", 1)[0] + ".wav"
        audio.export(converted_path, format="wav")

    # עיבוד אודיו עם librosa
    y, sr = librosa.load(converted_path)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    melody = []
    for i in range(pitches.shape[1]):
        index = magnitudes[:, i].argmax()
        pitch = pitches[index, i]
        if pitch > 0:
            melody.append(librosa.hz_to_note(pitch))

    # יצירת הרמוניה בסיסית
    midi_stream = stream.Stream()
    for pitch_name in melody[:16]:
        try:
            n = note.Note(pitch_name)
            c = chord.Chord([n, n.transpose(4), n.transpose(7)])
            midi_stream.append(c)
        except:
            continue

    midi_fp = "output.mid"
    mf = midi.translate.streamToMidiFile(midi_stream)
    mf.open(midi_fp, 'wb')
    mf.write()
    mf.close()

    # המרת MIDI ל-MP3
    audio = AudioSegment.from_file(midi_fp, format="mid")
    mp3_fp = "output.mp3"
    audio.export(mp3_fp, format="mp3")

    # ניקוי קבצים זמניים
    os.remove(input_path)
    if converted_path != input_path:
        os.remove(converted_path)
    os.remove(midi_fp)

    return FileResponse(mp3_fp, media_type="audio/mp3", filename="harmonized.mp3")
