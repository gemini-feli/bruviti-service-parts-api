
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.catalogue import PartsCatalogue


BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "templates" / "index.html"

# Build the catalogue once at application startup.
catalogue = PartsCatalogue()

app = FastAPI(
    title="Arcadia Service Parts Catalogue API",
    description="Bruviti Applied AI Engineering - Use Case 5",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/validation")
def get_validation():
    return catalogue.validation()


@app.get("/api/parts/{part_number}/paths")
def get_part_paths(part_number: str):
    try:
        return catalogue.get_paths(part_number)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Part not found in machine catalogue",
        )


@app.get("/api/parts/{part_number}")
def get_part_details(part_number: str):
    try:
        return catalogue.get_part(part_number)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Part not found in machine catalogue",
        )


@app.get("/api/serial/{serial}")
def check_serial(serial: str):
    if re.fullmatch(r"[0-9]+", serial) is None:
        raise HTTPException(
            status_code=422,
            detail="Serial must be a whole number",
        )

    try:
        serial_number = int(serial)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid serial number",
        )

    return catalogue.applicable_parts(serial_number)


@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(
        HTML_FILE,
        media_type="text/html",
    )
