from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings
from core.db import init_db

settings = get_settings()

# Import your routers FIRST (this loads your new models into memory)
from routers import auth, trading, finance_monitor, options

# Initialize DB + run any lightweight migrations
init_db()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PLUG IN THE ROUTERS
app.include_router(auth.router)
app.include_router(trading.router)
app.include_router(finance_monitor.router)
app.include_router(options.router)

@app.get("/")
def home():
    return {"status": "Global Server Engine Online"}
