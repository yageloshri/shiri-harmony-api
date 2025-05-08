# Dockerfile (מתוקן)
FROM python:3.11-slim

# התקנת תלות מערכת נדרשת: curl, fluidsynth ו־ffmpeg
RUN apt-get update && \
    apt-get install -y curl fluidsynth ffmpeg && \
    apt-get clean

# התקנת ספריות פייתון
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# הורדת קובץ SoundFont מ־Google Drive
RUN curl -L -o soundfont.sf2 "https://drive.google.com/uc?export=download&id=1BSjV97xDdRv4J_CPsUi_TDqpbNk0iOVx"

# העתקת קוד האפליקציה
COPY . .

# הפעלת האפליקציה
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
