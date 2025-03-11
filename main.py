import os
from flask import Flask, request, jsonify
import yt_dlp
import uuid
import os
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def serialize_word(word):
    """Convert a SpeechToTextWordResponseModel object to a JSON-serializable dictionary."""
    return {
        "text": word.text,
        "type": word.type,
        "start": word.start,
        "end": word.end,
        "speaker_id": word.speaker_id,
        "characters": [
            {
                "text": char.text,
                "start": char.start,
                "end": char.end
            } for char in (word.characters or [])
        ]
    }

@app.route("/transcript", methods=["GET"])
def get_transcript():
    youtube_url = request.args.get("url")
    if not youtube_url:
        return {"error": "Missing 'url' parameter"}, 400
    
    try:
        ydl_opts = {
            "format": "m4a/bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }],
            "paths": {
                "home": DOWNLOAD_DIR,
            },
            "outtmpl": f"%(id)s.%(ext)s",
            "noplaylist": True,
            "ffmpeg_location": "/usr/bin/ffmpeg",
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            video_id = info.get("id", str(uuid.uuid4()))
            audio_filename = f"{DOWNLOAD_DIR}/{video_id}.m4a"
            
            if not os.path.exists(audio_filename):
                ydl.download([youtube_url])
        
        with open(audio_filename, "rb") as audio_file:
            transcript = elevenlabs.speech_to_text.convert(
                model_id="scribe_v1",
                file=audio_file,
            )
        
        words_data = [serialize_word(word) for word in (transcript.words or [])]
        
        response_data = {
            "transcript": transcript.text if transcript.text else "",
            "words": words_data,
            "video": {
                "id": video_id,
                "title": info.get("title", ""),
                "duration": info.get("duration"),
                "channel": info.get("channel", ""),
                "thumbnail": info.get("thumbnail", "")
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(audio_filename):
            try:
                os.remove(audio_filename)
            except:
                pass

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")