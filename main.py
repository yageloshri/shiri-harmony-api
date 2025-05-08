from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import librosa
import soundfile as sf
import os
from pydub import AudioSegment
from music21 import stream, note, chord, midi
import subprocess
import uuid

app = FastAPI()

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    input_path = f"input_{uid}_{file.filename}"
    converted_path = ""
    midi_fp = f"output_{uid}.mid"
    wav_fp = f"output_{uid}.wav"

    try:
        # שמירת הקובץ
        with open(input_path, "wb") as f:
            f.write(await file.read())
        print("📥 File saved:", input_path)

        # המרה ל-WAV אם צריך
        if not input_path.lower().endswith(".wav"):
            audio = AudioSegment.from_file(input_path)
            converted_path = f"converted_{uid}.wav"
            audio.export(converted_path, format="wav")
            print("🔁 Converted to WAV:", converted_path)
        else:
            converted_path = input_path

        # ניתוח מלודיה עם librosa
        y, sr = librosa.load(converted_path)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        melody = []
        for i in range(pitches.shape[1]):
            index = magnitudes[:, i].argmax()
            pitch = pitches[index, i]
            if pitch > 0:
                try:
                    melody.append(librosa.hz_to_note(pitch))
                except Exception as e:
                    print("⚠️ Failed to parse pitch:", pitch, e)

        if not melody:
            raise Exception("לא זוהתה מלודיה")

        # יצירת הרמוניה
        midi_stream = stream.Stream()
        for pitch_name in melody[:16]:
            try:
                n = note.Note(pitch_name)
                c = chord.Chord([n, n.transpose(4), n.transpose(7)])
                midi_stream.append(c)
            except Exception as e:
                print("⚠️ Chord error:", pitch_name, e)

        mf = midi.translate.streamToMidiFile(midi_stream)
        mf.open(midi_fp, 'wb')
        mf.write()
        mf.close()
        print("🎼 MIDI file created:", midi_fp)

        # המרה ל-WAV עם FluidSynth
        soundfont_path = "soundfont.sf2"
        result = subprocess.run(
            ["fluidsynth", "-ni", soundfont_path, midi_fp, "-F", wav_fp, "-r", "44100"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("❌ FluidSynth error:", result.stderr)
            raise Exception("המרת MIDI ל-WAV נכשלה")

        print("✅ WAV created:", wav_fp)
        return FileResponse(wav_fp, media_type="audio/wav", filename="harmonized.wav")

    except Exception as e:
        print("❌ Exception:", str(e))
        return {"error": str(e)}

    finally:
        # ניקוי קבצים זמניים
        for path in [input_path, converted_path, midi_fp]:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print("⚠️ Failed to delete:", path, e)
