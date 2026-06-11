from fastapi import FastAPI
from apis.auth import router as auth_router
from apis.assessment import router as assessment_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(assessment_router)

@app.get("/")
def read_root():
    return {"message": "hello World"}