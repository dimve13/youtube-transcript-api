from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api._errors import CouldNotRetrieveTranscript

app = FastAPI()


class TranscriptRequest(BaseModel):
    videoId: str


@app.post("/transcript")
def get_transcript(req: TranscriptRequest):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(req.videoId)

        # Prefer manual English, then auto-generated English, then first available
        transcript = None
        try:
            transcript = transcript_list.find_transcript(["en"])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
            except Exception:
                try:
                    transcript = next(iter(transcript_list))
                except StopIteration:
                    raise HTTPException(status_code=404, detail="No transcripts available")

        data = transcript.fetch()
        segments = [
            {"text": s["text"], "start": s["start"], "dur": s["duration"]}
            for s in data
        ]
        return {"segments": segments, "language": transcript.language_code}

    except HTTPException:
        raise
    except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"ok": True}
