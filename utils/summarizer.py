from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from typing import List

load_dotenv()

class YoutubeHighlight(BaseModel):
    title: str = Field(description="A short, informative title for the summary.")
    summary: str = Field(description="A 60-word standalone short structured blog of the content.")
    tags: List[str] = Field(description="""
    **List of tags or topics covered in the core concepts of the text. MAX 2 TAGS**/n
    **One tag should always be the name of the youtube channel**, **Second one should be the tag which truly defines the video title**
    """)
    category: str = Field(description="A short category like 'Tech', 'Health', 'Education', etc.")

class AnalyticalVidyaHighlight(BaseModel):
    title: str = Field(description="A short, informative title for the summary.")
    summary: str = Field(description="A 60-word standalone short structured blog of the content.")
    tags: List[str] = Field(description="""
    **List of tags or topics covered in the core concepts of the text. MAX 2 TAGS**/n
    """)
    category: str = Field(description="A short category like 'Tech', 'Health', 'Education', etc.")

llm_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

structured_llm_youtube = llm_gemini.with_structured_output(YoutubeHighlight)
structured_llm_analyticalvidya = llm_gemini.with_structured_output(AnalyticalVidyaHighlight)


def summarize_final_summary_youtube(text: str) -> str:
    prompt = ChatPromptTemplate.from_template(
   "From the given transcript, return a structured response with the following:\n"
        "1. A short, engaging **title** (no clickbait).\n"
        "2. A **structured short blog** under 60 words. Do NOT mention source (e.g., video, podcast, etc.).\n"
        "3. A list of **tags** or **topics** covered.**MAX 2 TAGS**\n** Use only common and standardized terms**, **One tag should always be the name of the youtube channel**, **Second one should be the tag which truly defines the video title**"
        "4. A suitable **category** like 'Tech', 'Finance', 'Education', etc.\n\n"
        "Transcript:\n\n{text}"
    )
    chain = prompt | structured_llm_youtube
    response = chain.invoke({"text": text})
    response_dict = response.model_dump()
    return response_dict


def summarize_final_summary_analyticalvidya(text: str) -> str:
    prompt = ChatPromptTemplate.from_template(
   "From the given transcript, return a structured response with the following:\n"
        "1. A short, engaging **title** (no clickbait).\n"
        "2. A **structured short blog** under 60 words. Do NOT mention source (e.g., video, podcast, etc.).\n"
        "3. A list of **tags** or **topics** covered.**MAX 2 TAGS**\n** Use only common and standardized terms**"
        "4. A suitable **category** like 'Tech', 'Finance', 'Education', etc.\n\n"
        "Transcript:\n\n{text}"
    )
    chain = prompt | structured_llm_analyticalvidya
    response = chain.invoke({"text": text})
    response_dict = response.model_dump()
    return response_dict