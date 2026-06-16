"""
Assnani Dental Chatbot — FastAPI Backend
Serves the frontend, proxies YOLO API calls, runs the symptom
analysis + correlation engine, and generates AI-powered reports.
"""

import os
import io
import asyncio
import base64
import httpx
import fitz  # PyMuPDF
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

from symptom_analyzer import SymptomAnalyzer
from correlation_engine import CorrelationEngine
from dental_expert_system import DentalTreatmentRecommender

# --- Configuration ---
YOLO_API_URL = os.environ.get(
    "YOLO_API_URL",
    "https://0xker-dental-x-ray-detection.hf.space/predict"
)
TREAT_API_URL = os.environ.get(
    "TREAT_API_URL",
    "https://0xker-treat-recommend.hf.space/api/analyze"
)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds

# --- App Setup ---
app = FastAPI(
    title="Assnani Dental AI Chatbot",
    description="""
## 🦷 Assnani Dental AI — API Documentation

A clinical AI backend that combines **symptom analysis**, **X-ray detection (YOLO)**, 
**symptom-to-finding correlation**, and **AI-generated treatment reports** for dental diagnosis support.

### Features
- **Symptom Analysis** — Risk-stratified assessment from patient-reported symptoms
- **X-ray Detection** — YOLO-based dental pathology detection (caries, periapical lesions, bone loss, etc.)
- **Correlation Engine** — Maps detected X-ray findings to reported symptoms
- **Treatment Planning** — Rule-based expert system for treatment recommendations
- **AI Report** — Gemini-powered narrative clinical report from X-ray images

### Notes
- All image endpoints accept `image/*` files or PDFs (images are extracted automatically from PDFs)
- The YOLO and Gemini APIs are external HuggingFace Space services
""",
    version="1.0.0",
    contact={
        "name": "Assnani Dental AI Team",
        "email": "contact@assnani-dental.ai",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Service health and availability checks.",
        },
        {
            "name": "Symptoms",
            "description": "Patient symptom intake and risk analysis.",
        },
        {
            "name": "X-ray",
            "description": "Dental X-ray image upload and YOLO-based pathology detection.",
        },
        {
            "name": "Correlation",
            "description": "Cross-reference symptom data with X-ray detection findings.",
        },
        {
            "name": "Treatment",
            "description": "Rule-based treatment plan generation from detection results.",
        },
        {
            "name": "AI Report",
            "description": "Gemini-powered AI narrative report from X-ray images.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Initialize Engines ---
symptom_analyzer = SymptomAnalyzer()
correlation_engine = CorrelationEngine()
expert_system = DentalTreatmentRecommender(large_cavity_threshold=5000)


# --- Retry Helper ---
async def _request_with_retry(client, url, max_retries=MAX_RETRIES, **kwargs):
    """
    Send a POST request with exponential backoff retry logic.
    Retries on timeout, connection, and read errors.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            response = await client.post(url, **kwargs)
            return response
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = RETRY_BACKOFF_BASE ** attempt  # 1s, 2s, 4s
                print(f"[Retry {attempt + 1}/{max_retries}] {url} — {e}. Waiting {wait}s...")
                await asyncio.sleep(wait)
    raise last_error


# --- Helpers ---
def extract_images_from_pdf(pdf_bytes: bytes) -> list:
    """
    Extract all images from a PDF file.
    Returns a list of tuples: (filename, image_bytes, content_type)
    """
    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            for img_idx, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    img_bytes = base_image["image"]
                    ext = base_image.get("ext", "png")
                    content_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                    filename = f"pdf_page{page_num + 1}_img{img_idx + 1}.{ext}"
                    images.append((filename, img_bytes, content_type))

            # If no embedded images found, render the page as an image
            if not image_list:
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                filename = f"pdf_page{page_num + 1}.png"
                images.append((filename, img_bytes, "image/png"))

        doc.close()
    except Exception as e:
        print(f"PDF extraction error: {e}")
    return images


async def process_uploaded_files(files: List[UploadFile]) -> list:
    """
    Process uploaded files — extract images from PDFs and pass through image files.
    Returns list of tuples: (filename, image_bytes, content_type)
    """
    all_images = []
    for f in files:
        file_bytes = await f.read()
        content_type = f.content_type or ""

        if content_type == "application/pdf" or (f.filename and f.filename.lower().endswith(".pdf")):
            pdf_images = extract_images_from_pdf(file_bytes)
            if pdf_images:
                all_images.extend(pdf_images)
            else:
                print(f"No images found in PDF: {f.filename}")
        elif content_type.startswith("image/") or (f.filename and f.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))):
            ct = content_type if content_type.startswith("image/") else "image/jpeg"
            all_images.append((f.filename or "image.jpg", file_bytes, ct))
        else:
            print(f"Skipping unsupported file type: {f.filename} ({content_type})")

    return all_images


# --- Pydantic Models ---

class SymptomData(BaseModel):
    """Patient-reported symptom intake form."""

    has_pain: bool = Field(False, description="Whether the patient is experiencing dental pain.")
    pain_location: str = Field("", description="Location of pain (e.g., 'upper left molar', 'lower right').")
    pain_type: str = Field("", description="Nature of pain (e.g., 'sharp', 'throbbing', 'dull ache').")
    pain_intensity: int = Field(0, ge=0, le=10, description="Pain intensity on a scale of 0 (none) to 10 (worst).")
    pain_duration: str = Field("", description="How long the patient has had the pain (e.g., '3 days', '2 weeks').")
    pain_triggers: list = Field(default_factory=list, description="Triggers that worsen pain (e.g., ['cold', 'biting', 'sweet']).")
    has_swelling: bool = Field(False, description="Whether facial or gum swelling is present.")
    swelling_severity: str = Field("", description="Severity of swelling: 'mild', 'moderate', or 'severe'.")
    has_fever: bool = Field(False, description="Whether the patient has a fever, indicating possible infection.")
    difficulty_opening: bool = Field(False, description="Whether the patient has difficulty opening the mouth (trismus).")
    has_trauma: bool = Field(False, description="Whether recent dental or facial trauma occurred.")
    has_broken_tooth: bool = Field(False, description="Whether the patient has a visibly broken or chipped tooth.")
    previous_root_canal: bool = Field(False, description="Whether the patient has had a previous root canal treatment.")
    last_visit: str = Field("", description="When the patient last visited a dentist (e.g., '6 months ago', '2 years').")
    recent_extraction: bool = Field(False, description="Whether the patient had a recent tooth extraction.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "has_pain": True,
                "pain_location": "upper left molar",
                "pain_type": "throbbing",
                "pain_intensity": 7,
                "pain_duration": "3 days",
                "pain_triggers": ["cold", "biting"],
                "has_swelling": True,
                "swelling_severity": "moderate",
                "has_fever": False,
                "difficulty_opening": False,
                "has_trauma": False,
                "has_broken_tooth": False,
                "previous_root_canal": False,
                "last_visit": "1 year ago",
                "recent_extraction": False,
            }
        }
    }

    @field_validator('pain_intensity')
    @classmethod
    def clamp_intensity(cls, v):
        """Ensure pain intensity is within 0–10 range."""
        return max(0, min(10, v))

    @field_validator('pain_location', 'pain_type', 'pain_duration', 'swelling_severity', 'last_visit')
    @classmethod
    def sanitize_string(cls, v):
        """Strip whitespace and limit string length."""
        if isinstance(v, str):
            return v.strip()[:200]
        return v


class CorrelationRequest(BaseModel):
    """Request body for correlating symptoms with X-ray detections."""

    symptoms: dict = Field(
        ...,
        description="Symptom data dictionary — same structure as SymptomData.",
        example={
            "has_pain": True,
            "pain_location": "lower right",
            "pain_intensity": 6,
            "has_swelling": False,
        },
    )
    detections: list = Field(
        ...,
        description="List of detection objects returned by /api/detect-xray.",
        example=[
            {"label": "caries", "confidence": 0.91, "bbox": [120, 80, 200, 160]},
            {"label": "periapical_lesion", "confidence": 0.76, "bbox": [300, 150, 380, 230]},
        ],
    )
    image_width: int = Field(0, description="Width of the X-ray image in pixels (used for spatial correlation).")
    image_height: int = Field(0, description="Height of the X-ray image in pixels (used for spatial correlation).")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symptoms": {
                    "has_pain": True,
                    "pain_location": "lower right",
                    "pain_intensity": 6,
                    "has_swelling": False,
                },
                "detections": [
                    {"label": "caries", "confidence": 0.91, "bbox": [120, 80, 200, 160]},
                ],
                "image_width": 512,
                "image_height": 512,
            }
        }
    }


class TreatmentRequest(BaseModel):
    """Request body for generating a treatment plan."""

    api_response: Optional[dict] = Field(
        None,
        description=(
            "Full YOLO API response object (from /api/detect-xray). "
            "Provide either this or `detections`."
        ),
    )
    detections: Optional[list] = Field(
        None,
        description=(
            "Flat list of detection objects. "
            "Provide either this or `api_response`."
        ),
        example=[
            {"label": "caries", "confidence": 0.88, "bbox": [100, 90, 180, 170]},
            {"label": "bone_loss", "confidence": 0.72, "bbox": [200, 110, 290, 210]},
        ],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "detections": [
                    {"label": "caries", "confidence": 0.88, "bbox": [100, 90, 180, 170]},
                    {"label": "bone_loss", "confidence": 0.72, "bbox": [200, 110, 290, 210]},
                ]
            }
        }
    }


# ─── Response Models ────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    service: str = Field(..., example="Assnani Dental Chatbot")


class ErrorResponse(BaseModel):
    error: str = Field(..., example="Descriptive error message.")


# --- Routes ---

@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def serve_index():
    """Serve the main chatbot HTML page."""
    return FileResponse("static/index.html")


@app.get(
    "/health",
    tags=["Health"],
    summary="Service health check",
    response_model=HealthResponse,
    responses={
        200: {
            "description": "Service is running normally.",
            "content": {"application/json": {"example": {"status": "healthy", "service": "Assnani Dental Chatbot"}}},
        }
    },
)
async def health_check():
    """
    Returns a simple JSON payload confirming the service is up.
    Useful for HuggingFace Space uptime monitors and load-balancer probes.
    """
    return {"status": "healthy", "service": "Assnani Dental Chatbot"}


@app.post(
    "/api/analyze-symptoms",
    tags=["Symptoms"],
    summary="Analyze patient symptoms",
    description="""
Accepts a structured symptom questionnaire and returns a **risk assessment** with:
- Overall urgency level (`low` / `moderate` / `high` / `emergency`)
- Likely diagnoses ranked by probability
- Recommended next steps

All string fields are sanitised and capped at 200 characters.
`pain_intensity` is clamped to 0–10 regardless of the value submitted.
""",
    responses={
        200: {
            "description": "Symptom analysis result with risk level and probable diagnoses.",
            "content": {
                "application/json": {
                    "example": {
                        "risk_level": "high",
                        "urgency": "See a dentist within 24 hours",
                        "probable_diagnoses": ["Acute pulpitis", "Periapical abscess"],
                        "recommendations": ["Avoid cold/hot foods", "Prescribed analgesics if needed"],
                    }
                }
            },
        },
        422: {"description": "Validation error — check field types and constraints."},
    },
)
async def analyze_symptoms(data: SymptomData):
    """Analyze patient symptoms and return risk assessment."""
    symptoms = data.model_dump()
    result = symptom_analyzer.analyze(symptoms)
    return JSONResponse(content=result)


@app.post(
    "/api/detect-xray",
    tags=["X-ray"],
    summary="Detect dental pathologies in X-ray image(s)",
    description="""
Upload one or more dental X-ray images (JPEG, PNG, WebP) **or** a PDF containing X-ray scans.

**PDF handling:** all embedded images are extracted automatically; if a page has no embedded image, the page itself is rasterised at 200 DPI.

Each image is forwarded to an external **YOLO detection API** with up to **3 automatic retries** (exponential backoff: 1 s → 2 s → 4 s).

The response includes per-image detection results and, when available, a **base64-encoded annotated image** (`annotated_image_b64`) ready to display in an `<img>` tag.

Detectable classes include (but are not limited to):
`caries`, `periapical_lesion`, `bone_loss`, `calculus`, `root_fragment`, `implant`, `crown`, `filling`.
""",
    responses={
        200: {
            "description": "Combined detection results for all uploaded images.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "total_images": 1,
                        "total_detections": 2,
                        "results": [
                            {
                                "filename": "xray.jpg",
                                "total_detections": 2,
                                "detections": [
                                    {"label": "caries", "confidence": 0.91, "bbox": [120, 80, 200, 160]},
                                    {"label": "periapical_lesion", "confidence": 0.76, "bbox": [300, 150, 380, 230]},
                                ],
                                "annotated_image_b64": "<base64-encoded PNG string>",
                            }
                        ],
                    }
                }
            },
        },
        400: {"description": "No valid images found in the uploaded files.", "model": ErrorResponse},
        504: {"description": "YOLO API timed out after all retries.", "model": ErrorResponse},
        500: {"description": "Internal server error during image processing.", "model": ErrorResponse},
    },
)
async def detect_xray(images: List[UploadFile] = File(..., description="One or more X-ray image files or PDFs.")):
    """
    Receive X-ray image(s) or PDF uploads, forward each image to the YOLO API,
    and return combined detection results.
    """
    try:
        all_images = await process_uploaded_files(images)

        if not all_images:
            return JSONResponse(
                status_code=400,
                content={"error": "No valid images found in the uploaded files."}
            )

        all_results = []
        annotated_images_b64 = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            for filename, img_bytes, content_type in all_images:
                files = {"image": (filename, img_bytes, content_type)}
                response = await _request_with_retry(client, YOLO_API_URL, files=files)

                if response.status_code != 200:
                    all_results.append({
                        "filename": filename,
                        "detections": [],
                        "total_detections": 0,
                        "error": f"YOLO API returned {response.status_code}"
                    })
                    continue

                det_data = response.json()

                if det_data.get("results"):
                    result_entry = det_data["results"][0]
                    if result_entry.get("result_image_b64") and not result_entry.get("annotated_image_b64"):
                        result_entry["annotated_image_b64"] = result_entry["result_image_b64"]
                    all_results.append(result_entry)
                    annotated_images_b64.append(result_entry.get("annotated_image_b64"))

        total_detections = sum(r.get("total_detections", len(r.get("detections", []))) for r in all_results)
        combined = {
            "results": all_results,
            "success": True,
            "total_images": len(all_results),
            "total_detections": total_detections,
        }

        return JSONResponse(content=combined)

    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content={"error": "YOLO API timed out after retries. Please try again."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error processing X-ray: {str(e)}"})


@app.post(
    "/api/correlate",
    tags=["Correlation"],
    summary="Correlate symptoms with X-ray findings",
    description="""
Cross-references **patient symptoms** (from `/api/analyze-symptoms`) with **YOLO detection results** 
(from `/api/detect-xray`) to produce a clinically coherent combined assessment.

Optionally accepts image dimensions (`image_width`, `image_height`) so the engine can 
perform spatial reasoning — e.g., mapping a detection in the lower-right quadrant to 
a patient complaint about the lower-right molar.
""",
    responses={
        200: {
            "description": "Correlation result linking symptoms to radiographic findings.",
            "content": {
                "application/json": {
                    "example": {
                        "correlation_score": 0.84,
                        "matched_findings": [
                            {
                                "symptom": "throbbing pain upper left",
                                "detection": "periapical_lesion",
                                "confidence": 0.76,
                                "clinical_note": "Periapical lesion consistent with irreversible pulpitis.",
                            }
                        ],
                        "unmatched_detections": [],
                        "unmatched_symptoms": [],
                        "overall_assessment": "High correlation — radiographic findings align with reported symptoms.",
                    }
                }
            },
        },
        422: {"description": "Validation error.", "model": ErrorResponse},
    },
)
async def correlate_findings(data: CorrelationRequest):
    """Correlate patient symptoms with YOLO detection results."""
    result = correlation_engine.correlate(
        symptoms=data.symptoms,
        detections=data.detections,
        image_width=data.image_width,
        image_height=data.image_height,
    )
    return JSONResponse(content=result)


@app.post(
    "/api/treatment-plan",
    tags=["Treatment"],
    summary="Generate a treatment plan from detections",
    description="""
Uses the built-in **rule-based dental expert system** to generate prioritised treatment 
recommendations from YOLO detection data.

Supply **one** of:
- `api_response` — the full JSON object returned by `/api/detect-xray`
- `detections` — a flat list of detection objects

The expert system applies clinical thresholds (e.g., large cavity area > 5,000 px²) 
to decide between restoration options (filling vs. crown vs. extraction).
""",
    responses={
        200: {
            "description": "Prioritised treatment recommendations.",
            "content": {
                "application/json": {
                    "example": {
                        "treatment_plan": [
                            {
                                "priority": 1,
                                "finding": "caries",
                                "treatment": "Composite resin restoration",
                                "urgency": "Within 2 weeks",
                                "notes": "Early-stage caries — conservative restoration indicated.",
                            },
                            {
                                "priority": 2,
                                "finding": "bone_loss",
                                "treatment": "Periodontal scaling and root planing",
                                "urgency": "Within 1 month",
                                "notes": "Moderate horizontal bone loss detected.",
                            },
                        ],
                        "total_findings": 2,
                    }
                }
            },
        },
        400: {"description": "Neither `api_response` nor `detections` was provided.", "model": ErrorResponse},
        422: {"description": "Validation error.", "model": ErrorResponse},
    },
)
async def get_treatment_plan(data: TreatmentRequest):
    """Generate treatment recommendations from YOLO detections."""
    if data.api_response:
        result = expert_system.analyze_api_response(data.api_response)
    elif data.detections:
        result = expert_system.analyze_detections(data.detections)
    else:
        return JSONResponse(status_code=400, content={"error": "Provide 'api_response' or 'detections'."})
    return JSONResponse(content=result)


@app.post(
    "/api/ai-report",
    tags=["AI Report"],
    summary="Generate an AI narrative clinical report",
    description="""
Sends uploaded X-ray image(s) or PDFs to a **Gemini-powered** treatment recommendation service 
and returns a structured AI-generated clinical narrative.

The report typically includes:
- Identified pathologies with confidence levels
- Clinical interpretation
- Recommended treatments with urgency ratings
- Follow-up advice

⚠️ **Note:** This endpoint calls an external Gemini API. Cold-start delays may occur on 
HuggingFace Spaces. The request timeout is **120 seconds** with up to 3 retries.
""",
    responses={
        200: {
            "description": "AI-generated clinical report.",
            "content": {
                "application/json": {
                    "example": {
                        "report": "The panoramic radiograph reveals moderate caries in the upper left first molar...",
                        "findings": ["Caries — UR6", "Periapical radiolucency — LR7"],
                        "recommendations": ["Root canal therapy — LR7", "Composite restoration — UL6"],
                        "follow_up": "Review in 3 months post-treatment.",
                    }
                }
            },
        },
        400: {"description": "No valid images found in the uploaded files.", "model": ErrorResponse},
        502: {"description": "Upstream AI (Gemini) API returned an error.", "model": ErrorResponse},
        504: {"description": "AI report request timed out — Gemini Space may be loading.", "model": ErrorResponse},
        500: {"description": "Internal error during AI report generation.", "model": ErrorResponse},
    },
)
async def get_ai_report(images: List[UploadFile] = File(..., description="One or more X-ray image files or PDFs.")):
    """
    Send X-ray image(s) / PDFs to the Gemini-powered treatment recommendation API.
    Returns an AI-generated clinical report.
    """
    try:
        all_images = await process_uploaded_files(images)

        if not all_images:
            return JSONResponse(status_code=400, content={"error": "No valid images found."})

        async with httpx.AsyncClient(timeout=120.0) as client:
            files_list = [("image", (fn, img_bytes, ct)) for fn, img_bytes, ct in all_images]
            data = {"model": "gemini-2.5-flash"}
            response = await _request_with_retry(client, TREAT_API_URL, files=files_list, data=data)

            if response.status_code != 200:
                return JSONResponse(
                    status_code=502,
                    content={"error": f"Treatment API returned {response.status_code}", "detail": response.text[:500]}
                )

            return JSONResponse(content=response.json())

    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content={"error": "AI report timed out. Gemini may be loading — try again."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error generating AI report: {str(e)}"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
