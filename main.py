from fastapi import FastAPI

app = FastAPI(title="Orquestra API")

@app.get("/")
def read_root():
    return {"message": "Orquestra backend is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}