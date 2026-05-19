from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base

# 1. Import your routers FIRST (this loads your new models into memory)
from routers import auth, trading 

# 2. Tell SQLite to generate all the tables NOW (after they are loaded)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Scalable Stock Simulator Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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