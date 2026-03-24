from fastapi import FastAPI
from dotenv import load_dotenv

from api.main import api_router

# Loading env
load_dotenv()

app = FastAPI()

# Routing
app.include_router(api_router)