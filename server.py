from fastapi import FastAPI, HTTPException
  from pydantic import BaseModel
  from youtube_transcript_api import YouTubeTranscriptApi
  from youtube_transcript_api._errors import CouldNotRetrieveTranscript

  app = FastAPI()
  ytt_api = YouTubeTranscriptApi()


  class TranscriptRequest(BaseModel):
      videoId: str


  @app.post("/transcript")
  def get_transcript(req: TranscriptRequest):
      try:
          transcript_list = ytt_api.list(req.videoId)

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
              {"text": s.text, "start": s.start, "dur": s.duration}
              for s in data
          ]
          return {"segments": segments, "language": data.language_code}

      except HTTPException:
          raise
      except CouldNotRetrieveTranscript as e:
          raise HTTPException(status_code=404, detail=str(e))
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))


  @app.get("/health")
  def health():
      return {"ok": True}
