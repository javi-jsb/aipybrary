from fastapi import FastAPI

app = FastAPI(title="aipybrary")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
