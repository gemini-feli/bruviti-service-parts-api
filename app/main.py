
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Arcadia Service Parts Catalogue API",
    description="Bruviti Use Case 5",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>Service Parts Catalogue</title>
        </head>
        <body>
            <h1>Arcadia Service Parts Catalogue</h1>
            <p>API server is running successfully.</p>
            <a href="/docs">Open API Documentation</a>
        </body>
    </html>
    """
