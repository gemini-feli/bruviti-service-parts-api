
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.catalogue import PartsCatalogue


# Build the catalogue once when the application starts.
# All API requests use the same preprocessed data.
catalogue = PartsCatalogue()

app = FastAPI(
    title="Arcadia Service Parts Catalogue API",
    description="Bruviti Applied AI Engineering - Use Case 5",
    version="1.0.0"
)


# ---------------------------------------
# 1. Health Check
# ---------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}


# ---------------------------------------
# 2. Catalogue Validation
# ---------------------------------------

@app.get("/api/validation")
def get_validation():
    return catalogue.validation()


# ---------------------------------------
# 3. Part Paths
# ---------------------------------------

@app.get("/api/parts/{part_number}/paths")
def get_part_paths(part_number: str):
    try:
        return catalogue.get_paths(part_number)

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Part not found in machine catalogue"
        )


# ---------------------------------------
# 4. Part Information
# ---------------------------------------

@app.get("/api/parts/{part_number}")
def get_part_details(part_number: str):
    try:
        return catalogue.get_part(part_number)

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Part not found in machine catalogue"
        )


# ---------------------------------------
# 5. Serial Compatibility
# ---------------------------------------

@app.get("/api/serial/{serial}")
def check_serial(serial: str):

    # Reject decimals, negatives, letters,
    # and other non-whole-number inputs.
    if re.fullmatch(r"[0-9]+", serial) is None:
        raise HTTPException(
            status_code=422,
            detail="Serial must be a whole number"
        )

    try:
        serial_number = int(serial)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid serial number"
        )

    return catalogue.applicable_parts(serial_number)


# ---------------------------------------
# 6. Homepage (temporary)
# ---------------------------------------

@app.get("/", response_class=HTMLResponse)
def homepage():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Arcadia Parts Catalogue</title>
    </head>
    <body>
        <h1>Arcadia Service Parts Catalogue</h1>

        <p>AM-700 Service Parts API is running.</p>

        <h3>Available features</h3>

        <ul>
            <li>Machine catalogue validation</li>
            <li>Part information lookup</li>
            <li>Machine assembly paths</li>
            <li>Serial number compatibility</li>
        </ul>

        <a href="/docs">Explore API Documentation</a>
    </body>
    </html>
    """
