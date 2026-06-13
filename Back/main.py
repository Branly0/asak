from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apis.auth import router as auth_router
from apis.assessment import router as assessment_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(assessment_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","*","http://localhost:5173","*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "hello World"}