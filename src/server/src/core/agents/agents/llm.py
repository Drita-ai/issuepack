import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain.chat_models import init_chat_model


load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

llm = init_chat_model("groq:llama-3.3-70b-versatile")