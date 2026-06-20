from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db

# Import your routers FIRST (this loads your new models into memory)
from routers import auth, trading

# Initialize DB + run any lightweight migrations
init_db()

app = FastAPI(title="Scalable Stock Simulator Engine")

# Explicitly list the URLs allowed to talk to your backend API
origins = [
    "https://stock-simulator-predictor.vercel.app",         # Your main live frontend
    "https://stock-simulator-predictor-ipx1c0929.vercel.app", # The specific Vercel preview deployment
    "http://localhost:3000",                                 # Local development fallback
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PLUG IN THE ROUTERS
app.include_router(auth.router)
app.include_router(trading.router)

@app.get("/")
def home():
    return {"status": "Global Server Engine Online"}
