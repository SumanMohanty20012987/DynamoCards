from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
from services.genai import YoutubeProcessor, GeminiProcessor
from config import embed_config

class VideoAnalysisRequest(BaseModel):
    youtube_link: HttpUrl


app = FastAPI()

#Config CORs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers=["*"],
)

genai_processor = GeminiProcessor(
        model_name="gemini-pro",
        project=embed_config["project"],
    )

@app.post("/analyze/video")
def analyze_video(request: VideoAnalysisRequest):

    processor = YoutubeProcessor(genai_processor=genai_processor)
    result = processor.retrieve_youtube_documents(str(request.youtube_link), verbose=True)
    

    # summary = genai_processor.generate_document_summary(result, verbose=True)

    key_concepts = processor.find_key_concepts(result, group_size=2)
    return{
        "key_concepts":key_concepts
    }

@app.get("/root")
def status():
    return {"status":"okay"}