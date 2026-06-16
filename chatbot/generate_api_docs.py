"""
Generate a comprehensive API Reference PDF for the Assnani Dental AI Chatbot.
Uses PyMuPDF (fitz) which is already in requirements.txt — no extra installs needed.
Run:  python generate_api_docs.py
Output: Chatbot_API_Reference.pdf  (in the same directory)
"""

import fitz  # PyMuPDF
import json
import os
import textwrap
from datetime import datetime

# ── Colour palette ──────────────────────────────────────────────
WHITE        = (1, 1, 1)
BG_DARK      = (0.07, 0.08, 0.12)  # Premium deep space gray
BG_CARD      = (0.11, 0.13, 0.20)  # Subtle lighter gray card bg
TEXT_PRIMARY = (0.96, 0.96, 0.98)  # Crisp clean white
TEXT_SEC     = (0.62, 0.66, 0.75)  # Soft slate gray
ACCENT       = (0.28, 0.48, 0.92)  # Sleek modern blue/indigo
ACCENT_TEAL  = (0.08, 0.72, 0.66)  # Radiant medical teal
METHOD_GET   = (0.08, 0.62, 0.38)  # Emerald green for GET
METHOD_POST  = (0.46, 0.32, 0.88)  # Indigo/purple for POST
DIVIDER      = (0.16, 0.18, 0.26)  # Subtle divider gray
CODE_BG      = (0.10, 0.11, 0.17)  # Editor code background
TABLE_HEAD   = (0.14, 0.16, 0.24)  # Table header block color
TABLE_ROW1   = (0.09, 0.10, 0.15)  # Zebra table row 1
TABLE_ROW2   = (0.11, 0.12, 0.18)  # Zebra table row 2
SEVERITY_HI  = (0.88, 0.28, 0.28)  # Clean crimson error color

# ── Page constants ──────────────────────────────────────────────
W, H = 595, 842          # A4 points
MARGIN_L, MARGIN_R = 50, 50
MARGIN_T, MARGIN_B = 55, 55
CONTENT_W = W - MARGIN_L - MARGIN_R

# ── Helpers ─────────────────────────────────────────────────────

def draw_rect(page, x, y, w, h, color, radius=0):
    rect = fitz.Rect(x, y, x + w, y + h)
    shape = page.new_shape()
    if radius > 0:
        shape.draw_rect(rect, radius=radius)
    else:
        shape.draw_rect(rect)
    shape.finish(fill=color, color=color)
    shape.commit()


# ── Endpoint data ───────────────────────────────────────────────

ENDPOINTS = [
    {
        "method": "GET",
        "path": "/",
        "summary": "Serve Main Chatbot Page",
        "description": "Returns the static index.html file that contains the full chatbot UI (HTML + CSS + JS). This is the entry point for the web application.",
        "request_body": None,
        "example_request": None,
        "response": {
            "type": "HTML",
            "description": "The full index.html page rendered in the browser.",
        },
        "example_response": "<!DOCTYPE html><html>...full chatbot UI...</html>",
    },
    {
        "method": "GET",
        "path": "/health",
        "summary": "Health Check",
        "description": "Simple health check endpoint to verify the API is running. Used by monitoring tools and Hugging Face Spaces to check service availability.",
        "request_body": None,
        "example_request": None,
        "response": {
            "type": "JSON",
            "keys": {
                "status": {"type": "string", "example": "healthy", "desc": "Service status indicator"},
                "service": {"type": "string", "example": "Assnani Dental Chatbot", "desc": "Service name identifier"},
            },
        },
        "example_response": json.dumps({"status": "healthy", "service": "Assnani Dental Chatbot"}, indent=2),
    },
    {
        "method": "POST",
        "path": "/api/analyze-symptoms",
        "summary": "Analyze Patient Symptoms",
        "description": "Receives patient symptom data from the chatbot interview and runs the weighted scoring algorithm to produce a risk assessment (low / moderate / high) with recommendations and home-care tips.",
        "request_body": {
            "content_type": "application/json",
            "model": "SymptomData",
            "keys": {
                "has_pain":              {"type": "boolean", "example": True,                    "desc": "Whether the patient reports dental pain"},
                "pain_location":         {"type": "string",  "example": "lower-left",            "desc": "Quadrant/area of pain (e.g. upper-right, lower-left)"},
                "pain_type":             {"type": "string",  "example": "throbbing",             "desc": "Type of pain: throbbing | sharp | dull | sensitivity"},
                "pain_intensity":        {"type": "integer", "example": 7,                       "desc": "Pain severity on a 0-10 scale (clamped)"},
                "pain_duration":         {"type": "string",  "example": "3-7 days",              "desc": "How long pain has lasted: today | 1-3 days | 3-7 days | 1+ week"},
                "pain_triggers":         {"type": "list[str]","example": '["hot","cold","biting","spontaneous"]', "desc": "What triggers the pain"},
                "has_swelling":          {"type": "boolean", "example": True,                    "desc": "Whether swelling is present"},
                "swelling_severity":     {"type": "string",  "example": "severe",                "desc": "Severity: mild | moderate | severe"},
                "has_fever":             {"type": "boolean", "example": False,                   "desc": "Whether the patient has a fever"},
                "difficulty_opening":    {"type": "boolean", "example": False,                   "desc": "Whether the patient has trismus (difficulty opening mouth)"},
                "has_trauma":            {"type": "boolean", "example": False,                   "desc": "History of dental trauma / injury"},
                "has_broken_tooth":      {"type": "boolean", "example": True,                    "desc": "Whether a tooth is visibly broken or chipped"},
                "previous_root_canal":   {"type": "boolean", "example": False,                   "desc": "Whether the affected tooth had a previous root canal"},
                "last_visit":            {"type": "string",  "example": "1+ year",               "desc": "Last dental visit: < 6 months | 6-12 months | 1+ year | never"},
                "recent_extraction":     {"type": "boolean", "example": False,                   "desc": "Whether the patient had a recent tooth extraction"},
            },
        },
        "example_request": json.dumps({
            "has_pain": True,
            "pain_location": "lower-left",
            "pain_type": "throbbing",
            "pain_intensity": 7,
            "pain_duration": "3-7 days",
            "pain_triggers": ["hot", "cold", "biting"],
            "has_swelling": True,
            "swelling_severity": "severe",
            "has_fever": False,
            "difficulty_opening": False,
            "has_trauma": False,
            "has_broken_tooth": True,
            "previous_root_canal": False,
            "last_visit": "1+ year",
            "recent_extraction": False
        }, indent=2),
        "example_request_info": {
            "method": "POST",
            "url": "http://localhost:7860/api/analyze-symptoms",
            "content_type": "application/json",
        },
        "response": {
            "type": "JSON",
            "keys": {
                "score":            {"type": "integer",   "example": 72,                        "desc": "Total weighted symptom score"},
                "risk_level":       {"type": "string",    "example": "high",                    "desc": "Risk level: low | moderate | high"},
                "risk_emoji":       {"type": "string",    "example": "\u0001f534",                      "desc": "Colour-coded emoji for the risk level"},
                "recommendation":   {"type": "string",    "example": "Based on your symptoms, an X-ray examination is strongly recommended as soon as possible.", "desc": "Human-readable recommendation text"},
                "factors":          {"type": "list[tuple]","example": '[["Dental pain reported", 10], ["Throbbing pain", 20]]', "desc": "List of [description, score] factor tuples"},
                "home_care":        {"type": "list[str]",  "example": '["Take Ibuprofen 400mg as needed", "Avoid hot/cold foods"]', "desc": "Personalised home-care tips"},
                "xray_recommended": {"type": "boolean",   "example": True,                     "desc": "Whether an X-ray is recommended based on risk"},
            },
        },
        "example_response": json.dumps({
            "score": 72,
            "risk_level": "high",
            "risk_emoji": "\u0001f534",
            "recommendation": "Based on your symptoms, an X-ray examination is strongly recommended as soon as possible.",
            "factors": [["Dental pain reported", 10], ["Throbbing pain (possible pulpitis)", 20], ["Spontaneous pain (possible nerve involvement)", 30], ["High pain intensity (7/10)", 25]],
            "home_care": ["Take over-the-counter pain relief (Ibuprofen 400mg) as needed.", "Avoid very hot or cold foods/drinks on the affected side.", "Do not delay seeking professional dental care."],
            "xray_recommended": True,
        }, indent=2),
    },
    {
        "method": "POST",
        "path": "/api/detect-xray",
        "summary": "Detect Dental Conditions from X-ray",
        "description": "Accepts dental X-ray image(s) or PDF uploads, extracts images from PDFs via PyMuPDF, forwards each to the external YOLOv8-XL detection API with retry logic, and returns combined detection results with annotated images.",
        "request_body": {
            "content_type": "multipart/form-data",
            "model": "File Upload",
            "keys": {
                "images": {"type": "List[UploadFile]", "example": "<binary file data>", "desc": "One or more image files (PNG, JPG, JPEG, WebP) or PDF files containing dental X-rays"},
            },
        },
        "example_request": "# Using cURL:\ncurl -X POST http://localhost:7860/api/detect-xray \\\n  -F \"images=@dental_xray.jpg\"\n\n# Using Python (requests):\nimport requests\n\nurl = \"http://localhost:7860/api/detect-xray\"\nfiles = {\"images\": open(\"dental_xray.jpg\", \"rb\")}\nresponse = requests.post(url, files=files)\nprint(response.json())\n\n# Multiple files:\nfiles = [\n    (\"images\", open(\"xray1.jpg\", \"rb\")),\n    (\"images\", open(\"xray2.jpg\", \"rb\"))\n]\nresponse = requests.post(url, files=files)",
        "example_request_info": {
            "method": "POST",
            "url": "http://localhost:7860/api/detect-xray",
            "content_type": "multipart/form-data",
        },
        "response": {
            "type": "JSON",
            "keys": {
                "results": {"type": "list[dict]", "example": "[{...result per image...}]", "desc": "Array of per-image result objects"},
                "results[].detections": {"type": "list[dict]", "example": '[{"class_name":"cavity","confidence":0.92,"x1":120,"y1":80,"x2":200,"y2":160,"width":80,"height":80}]', "desc": "List of detected dental conditions with bounding boxes"},
                "results[].detections[].class_name": {"type": "string", "example": "cavity", "desc": "Detected class: cavity | filling | implant | impacted"},
                "results[].detections[].confidence": {"type": "float", "example": 0.92, "desc": "Model confidence score (0.0 - 1.0)"},
                "results[].detections[].x1, y1, x2, y2": {"type": "int", "example": "120, 80, 200, 160", "desc": "Bounding box coordinates (pixels)"},
                "results[].detections[].width, height": {"type": "int", "example": "80, 80", "desc": "Bounding box dimensions (pixels)"},
                "results[].filename": {"type": "string", "example": "xray_001.jpg", "desc": "Original filename of the processed image"},
                "results[].annotated_image_b64": {"type": "string", "example": "iVBORw0KGgo...", "desc": "Base64-encoded annotated X-ray image with bounding boxes drawn"},
                "results[].total_detections": {"type": "integer", "example": 3, "desc": "Number of detections found in this image"},
                "success": {"type": "boolean", "example": True, "desc": "Overall success status"},
                "total_images": {"type": "integer", "example": 2, "desc": "Total number of images processed"},
                "total_detections": {"type": "integer", "example": 5, "desc": "Sum of all detections across all images"},
            },
        },
        "example_response": json.dumps({
            "results": [{
                "detections": [
                    {"class_name": "cavity", "confidence": 0.92, "x1": 120, "y1": 80, "x2": 200, "y2": 160, "width": 80, "height": 80},
                    {"class_name": "filling", "confidence": 0.87, "x1": 300, "y1": 100, "x2": 370, "y2": 170, "width": 70, "height": 70},
                ],
                "filename": "xray_001.jpg",
                "annotated_image_b64": "iVBORw0KGgoAAAANSUhEUg...(truncated)",
                "total_detections": 2,
            }],
            "success": True,
            "total_images": 1,
            "total_detections": 2,
        }, indent=2),
    },
    {
        "method": "POST",
        "path": "/api/correlate",
        "summary": "Correlate Symptoms with X-ray Findings",
        "description": "Matches patient-reported symptoms (from the chatbot interview) with YOLO detection results. Produces natural-language explanations linking complaints to specific findings, sorted by match strength and severity.",
        "request_body": {
            "content_type": "application/json",
            "model": "CorrelationRequest",
            "keys": {
                "symptoms": {"type": "dict", "example": '{"has_pain":true,"pain_location":"lower-left","pain_type":"throbbing","has_swelling":true}', "desc": "Patient symptom data (same structure as SymptomData fields)"},
                "detections": {"type": "list[dict]", "example": '[{"class_name":"cavity","confidence":0.92,"x1":120,"y1":80,"x2":200,"y2":160}]', "desc": "YOLO detection results array"},
                "image_width": {"type": "integer", "example": 800, "desc": "Width of the original X-ray image in pixels (for quadrant mapping)"},
                "image_height": {"type": "integer", "example": 600, "desc": "Height of the original X-ray image in pixels (for quadrant mapping)"},
            },
        },
        "example_request": json.dumps({
            "symptoms": {
                "has_pain": True,
                "pain_location": "lower-left",
                "pain_type": "throbbing",
                "has_swelling": True,
                "swelling_severity": "moderate"
            },
            "detections": [
                {
                    "class_name": "cavity",
                    "confidence": 0.92,
                    "x1": 120, "y1": 80,
                    "x2": 200, "y2": 160
                }
            ],
            "image_width": 800,
            "image_height": 600
        }, indent=2),
        "example_request_info": {
            "method": "POST",
            "url": "http://localhost:7860/api/correlate",
            "content_type": "application/json",
        },
        "response": {
            "type": "JSON",
            "keys": {
                "correlations": {"type": "list[dict]", "example": "[{...}]", "desc": "Array of correlation objects sorted by match strength"},
                "correlations[].detection_index": {"type": "integer", "example": 0, "desc": "Index of the detection in the original detections array"},
                "correlations[].class_name": {"type": "string", "example": "cavity", "desc": "YOLO detection class name"},
                "correlations[].clinical_name": {"type": "string", "example": "Dental Caries (Cavity)", "desc": "Human-readable clinical term"},
                "correlations[].confidence": {"type": "float", "example": 0.92, "desc": "Detection confidence score"},
                "correlations[].confidence_label": {"type": "string", "example": "high confidence", "desc": "Human-readable confidence label"},
                "correlations[].detection_region": {"type": "string", "example": "Lower Left (Quadrant 3, teeth 31-38)", "desc": "Mapped dental quadrant of detection"},
                "correlations[].location_match": {"type": "boolean", "example": True, "desc": "Whether symptom location matches detection quadrant"},
                "correlations[].match_type": {"type": "string", "example": "strong", "desc": "Match strength: strong | swelling | location | additional"},
                "correlations[].severity": {"type": "string", "example": "high", "desc": "Severity level: high | moderate | low"},
                "correlations[].explanation": {"type": "string", "example": "You mentioned throbbing pain in the lower-left region. Our AI detected tooth decay...", "desc": "Natural-language correlation explanation"},
                "correlations[].urgency": {"type": "string", "example": "Prompt treatment recommended to prevent further nerve damage.", "desc": "Urgency recommendation"},
                "unmatched_symptoms": {"type": "list[str]", "example": '["You reported sharp pain in upper-right region, but no findings detected..."]', "desc": "Symptoms that could not be matched to any detection"},
                "total_detections": {"type": "integer", "example": 3, "desc": "Total number of YOLO detections processed"},
                "total_correlations": {"type": "integer", "example": 2, "desc": "Number of correlations with location match"},
            },
        },
        "example_response": json.dumps({
            "correlations": [{
                "detection_index": 0,
                "class_name": "cavity",
                "clinical_name": "Dental Caries (Cavity)",
                "confidence": 0.92,
                "confidence_label": "high confidence",
                "detection_region": "Lower Left (Quadrant 3, teeth 31-38)",
                "location_match": True,
                "match_type": "strong",
                "severity": "high",
                "explanation": "You mentioned throbbing pain in the lower-left region. Our AI detected tooth decay that has damaged the tooth structure in the same area (92% confidence). The cavity may have reached the tooth nerve (pulp), causing inflammation (pulpitis) and throbbing pain.",
                "urgency": "Prompt treatment recommended to prevent further nerve damage.",
            }],
            "unmatched_symptoms": [],
            "total_detections": 1,
            "total_correlations": 1,
        }, indent=2),
    },
    {
        "method": "POST",
        "path": "/api/treatment-plan",
        "summary": "Generate Treatment Recommendations",
        "description": "Takes YOLO detection results and produces structured treatment recommendations using a rule-based expert system. Maps each finding to a treatment plan, severity, and specialist referral. Accepts either a full API response or a raw detections list.",
        "request_body": {
            "content_type": "application/json",
            "model": "TreatmentRequest",
            "keys": {
                "api_response": {"type": "dict | null", "example": '{"results":[{"detections":[...],"filename":"xray.jpg","total_detections":2}],"success":true,"total_images":1}', "desc": "Full YOLO API response object (preferred). Mutually exclusive with 'detections'."},
                "detections": {"type": "list[dict] | null", "example": '[{"class_name":"cavity","confidence":0.92,"width":80,"height":80}]', "desc": "Raw detection list (alternative input). Used if api_response is null."},
            },
        },
        "example_request": json.dumps({
            "detections": [
                {
                    "class_name": "cavity",
                    "confidence": 0.92,
                    "width": 80,
                    "height": 80
                },
                {
                    "class_name": "filling",
                    "confidence": 0.85,
                    "width": 70,
                    "height": 70
                }
            ]
        }, indent=2),
        "example_request_info": {
            "method": "POST",
            "url": "http://localhost:7860/api/treatment-plan",
            "content_type": "application/json",
        },
        "response": {
            "type": "JSON",
            "keys": {
                "patient_file": {"type": "string", "example": "xray_001.jpg", "desc": "Filename of the analyzed image"},
                "total_detections": {"type": "integer", "example": 3, "desc": "Total number of detections"},
                "summary": {"type": "dict", "example": '{"cavity":2,"filling":1,"implant":0,"impacted":0}', "desc": "Count of each detection class found"},
                "recommendations": {"type": "list[dict]", "example": "[{...}]", "desc": "Array of treatment recommendation objects"},
                "recommendations[].finding": {"type": "string", "example": "Large/Deep Cavity", "desc": "Detection finding label"},
                "recommendations[].confidence": {"type": "string", "example": "92%", "desc": "Formatted detection confidence"},
                "recommendations[].area": {"type": "integer", "example": 6400, "desc": "Bounding box area (width×height) in pixels²"},
                "recommendations[].severity": {"type": "string", "example": "high", "desc": "Severity level: high | moderate | low"},
                "recommendations[].treatment": {"type": "string", "example": "Root Canal Treatment (Endodontics) followed by a Crown restoration.", "desc": "Recommended treatment plan"},
                "recommendations[].specialist": {"type": "string", "example": "Endodontist", "desc": "Specialist referral type"},
                "recommendations[].icon": {"type": "string", "example": "🦷", "desc": "Visual icon for the finding type"},
                "specialists": {"type": "list[str]", "example": '["Endodontist","General Dentist","Oral & Maxillofacial Surgeon"]', "desc": "Unique list of specialists to refer to"},
                "disclaimer": {"type": "string", "example": "⚠️ This is an AI-assisted preliminary analysis...", "desc": "Medical disclaimer text"},
            },
        },
        "example_response": json.dumps({
            "patient_file": "xray_001.jpg",
            "total_detections": 3,
            "summary": {"cavity": 2, "filling": 1, "implant": 0, "impacted": 0},
            "recommendations": [
                {"finding": "Large/Deep Cavity", "confidence": "92%", "area": 6400, "severity": "high", "treatment": "Root Canal Treatment (Endodontics) followed by a Crown restoration. Vitality test recommended.", "specialist": "Endodontist", "icon": "🦷"},
                {"finding": "Small/Medium Cavity", "confidence": "78%", "area": 3200, "severity": "moderate", "treatment": "Dental Restoration — Composite or Amalgam filling to restore tooth structure.", "specialist": "General Dentist", "icon": "🔧"},
                {"finding": "Existing Filling", "confidence": "85%", "area": 4900, "severity": "low", "treatment": "Routine monitoring. Check margins clinically and radiographically for secondary caries.", "specialist": "General Dentist", "icon": "✅"},
            ],
            "specialists": ["Endodontist", "General Dentist"],
            "disclaimer": "⚠️ This is an AI-assisted preliminary analysis. Final diagnosis and treatment plan must be verified by a licensed dental professional.",
        }, indent=2),
    },
    {
        "method": "POST",
        "path": "/api/ai-report",
        "summary": "Generate AI Clinical Report (Gemini-powered)",
        "description": "Sends dental X-ray image(s) or PDFs to an external Gemini-powered treatment recommendation API. Returns a full AI-generated clinical report with HTML-formatted analysis, detection counts by class, and an annotated image.",
        "request_body": {
            "content_type": "multipart/form-data",
            "model": "File Upload",
            "keys": {
                "images": {"type": "List[UploadFile]", "example": "<binary file data>", "desc": "One or more dental X-ray images (PNG, JPG) or PDF files"},
            },
            "_note": "Internally also sends: model='gemini-2.5-flash' as form data to the external API.",
        },
        "example_request": "# Using cURL:\ncurl -X POST http://localhost:7860/api/ai-report \\\n  -F \"images=@dental_xray.jpg\"\n\n# Using Python (requests):\nimport requests\n\nurl = \"http://localhost:7860/api/ai-report\"\nfiles = {\"images\": open(\"dental_xray.jpg\", \"rb\")}\nresponse = requests.post(url, files=files)\nprint(response.json())",
        "example_request_info": {
            "method": "POST",
            "url": "http://localhost:7860/api/ai-report",
            "content_type": "multipart/form-data",
        },
        "response": {
            "type": "JSON (proxied from external Treatment API)",
            "keys": {
                "results": {"type": "dict", "example": '{"xray_001.jpg": {...}}', "desc": "Dictionary keyed by filename with analysis results"},
                "results.<filename>.total": {"type": "integer", "example": 3, "desc": "Total detections for this image"},
                "results.<filename>.by_class": {"type": "dict", "example": '{"cavity":2,"filling":1}', "desc": "Detection counts grouped by class"},
                "results.<filename>.image_b64": {"type": "string", "example": "iVBORw0KGgo...", "desc": "Base64-encoded annotated result image"},
                "results.<filename>.report": {"type": "string (HTML)", "example": "<h2>Clinical Chart Note</h2><p>Findings: ...</p>", "desc": "HTML-formatted AI clinical report generated by Gemini"},
                "results.<filename>.error": {"type": "string | null", "example": None, "desc": "Error message if analysis failed for this image, else null"},
            },
        },
        "example_response": json.dumps({
            "results": {
                "xray_001.jpg": {
                    "total": 3,
                    "by_class": {"cavity": 2, "filling": 1},
                    "image_b64": "iVBORw0KGgoAAAANSUhEUg...(truncated)",
                    "report": "<h2>Clinical Chart Note</h2><p><strong>Patient:</strong> Unknown</p><p><strong>Chief Complaint:</strong> Dental evaluation</p><h3>Radiographic Findings</h3><ul><li>Two carious lesions detected</li><li>One existing restoration noted</li></ul><h3>Assessment</h3><p>Moderate dental pathology requiring intervention.</p><h3>Treatment Plan</h3><ol><li>Restore carious lesions with composite resin</li><li>Monitor existing filling at next recall</li></ol>",
                    "error": None,
                }
            }
        }, indent=2),
    },
]

# ── PDF Generation ──────────────────────────────────────────────

class PDFWriter:
    def __init__(self, doc):
        self.doc = doc
        self.page = None
        self.y = 0
        self.page_num_map = {}
        self.default_font = "helv"
        self.bold_font = "hebo"
        self.mono_font = "cour"

    def add_page(self, title=None, ep_idx=None):
        self.page = self.doc.new_page(width=W, height=H)
        draw_rect(self.page, 0, 0, W, H, BG_DARK)
        # Top gradient/accent border
        draw_rect(self.page, 0, 0, W, 8, ACCENT)
        self.y = MARGIN_T
        if ep_idx is not None:
            self.page_num_map[ep_idx] = len(self.doc) - 1

        # Draw base running header
        if title:
            self.page.insert_text(fitz.Point(MARGIN_L, 32), "Assnani Dental AI Chatbot — API Reference", fontsize=8, fontname=self.default_font, color=TEXT_SEC)
            self.page.insert_text(fitz.Point(W - MARGIN_R - 180, 32), title, fontsize=8, fontname=self.bold_font, color=ACCENT_TEAL)
            # Draw thin divider line
            shape = self.page.new_shape()
            shape.draw_line(fitz.Point(MARGIN_L, 38), fitz.Point(W - MARGIN_R, 38))
            shape.finish(color=DIVIDER, width=0.5)
            shape.commit()

    def ensure_space(self, needed, title=None):
        if self.y + needed > H - MARGIN_B:
            self.add_page(title)
            return True
        return False

    def draw_text_at(self, x, y, text, fontsize=10, color=TEXT_PRIMARY, fontname="helv", max_width=None):
        if max_width and len(text) * fontsize * 0.5 > max_width:
            chars_per_line = int(max_width / (fontsize * 0.42))
            lines = textwrap.wrap(text, width=chars_per_line)
        else:
            lines = [text]

        curr_y = y
        for line in lines:
            self.page.insert_text(
                fitz.Point(x, curr_y),
                line,
                fontsize=fontsize,
                fontname=fontname,
                color=color,
            )
            curr_y += fontsize * 1.25
        return curr_y - y

    def draw_method_badge(self, x, y, method):
        text_color = WHITE
        bg_color = METHOD_GET if method == "GET" else METHOD_POST
        fontsize = 9
        tw = len(method) * fontsize * 0.55 + 12
        h = fontsize + 6
        rect = fitz.Rect(x, y - fontsize - 2, x + tw, y - fontsize - 2 + h)
        shape = self.page.new_shape()
        shape.draw_rect(rect, radius=0.25)
        shape.finish(fill=bg_color, color=bg_color)
        shape.commit()
        self.page.insert_text(fitz.Point(x + 6, y - 1), method, fontsize=fontsize, fontname=self.bold_font, color=text_color)
        return tw

    def draw_table_section(self, section_title, keys, col_widths, headers, ep_title=None):
        self.ensure_space(45, title=ep_title)
        self.y += 10
        self.page.insert_text(fitz.Point(MARGIN_L, self.y), section_title, fontsize=11, fontname=self.bold_font, color=ACCENT_TEAL)
        self.y += 16

        # Draw Table Headers
        self.ensure_space(20, title=ep_title)
        draw_rect(self.page, MARGIN_L, self.y - 11, CONTENT_W, 16, TABLE_HEAD, radius=0.15)
        x = MARGIN_L + 6
        for hi, hw in zip(headers, col_widths):
            self.page.insert_text(fitz.Point(x, self.y), hi, fontsize=8, fontname=self.bold_font, color=ACCENT)
            x += hw
        self.y += 14

        # Draw rows
        for ri, (key, info) in enumerate(keys.items()):
            desc_str = info.get("desc", "")
            ex_str = str(info.get("example", ""))

            desc_chars = int((col_widths[3] - 10) / 4.2)
            desc_lines = max(1, (len(desc_str) // desc_chars) + 1)
            key_chars = int((col_widths[0] - 10) / 4.5)
            key_lines = max(1, (len(key) // key_chars) + 1)

            row_h = max(desc_lines, key_lines) * 12 + 6

            page_changed = self.ensure_space(row_h + 10, title=ep_title)
            if page_changed:
                draw_rect(self.page, MARGIN_L, self.y - 11, CONTENT_W, 16, TABLE_HEAD, radius=0.15)
                x = MARGIN_L + 6
                for hi, hw in zip(headers, col_widths):
                    self.page.insert_text(fitz.Point(x, self.y), hi, fontsize=8, fontname=self.bold_font, color=ACCENT)
                    x += hw
                self.y += 14

            row_color = TABLE_ROW1 if ri % 2 == 0 else TABLE_ROW2
            draw_rect(self.page, MARGIN_L, self.y - 10, CONTENT_W, row_h, row_color)

            x = MARGIN_L + 6
            self.draw_text_at(x, self.y - 1, key, fontsize=7.5, color=TEXT_PRIMARY, fontname=self.bold_font, max_width=col_widths[0] - 10)
            x += col_widths[0]
            self.draw_text_at(x, self.y - 1, info["type"], fontsize=7.5, color=TEXT_SEC, fontname=self.default_font, max_width=col_widths[1] - 10)
            x += col_widths[1]
            ex_display = ex_str[:30] + "..." if len(ex_str) > 32 else ex_str
            self.draw_text_at(x, self.y - 1, ex_display, fontsize=7, color=ACCENT_TEAL, fontname=self.mono_font, max_width=col_widths[2] - 10)
            x += col_widths[2]
            self.draw_text_at(x, self.y - 1, desc_str, fontsize=7.5, color=TEXT_SEC, fontname=self.default_font, max_width=col_widths[3] - 10)

            self.y += row_h

        self.y += 10

    def draw_code_block(self, title, code_text, ep_title=None):
        self.ensure_space(45, title=ep_title)
        self.y += 10
        self.page.insert_text(fitz.Point(MARGIN_L, self.y), title, fontsize=11, fontname=self.bold_font, color=ACCENT_TEAL)
        self.y += 16

        max_code_chars = int((CONTENT_W - 20) / 4.2)
        code_lines = code_text.split("\n")

        wrapped_lines = []
        for line in code_lines:
            if len(line) > max_code_chars:
                wrapped = textwrap.wrap(line, width=max_code_chars, break_long_words=True, break_on_hyphens=False)
                wrapped_lines.extend(wrapped if wrapped else [""])
            else:
                wrapped_lines.append(line)

        for wline in wrapped_lines:
            self.ensure_space(14, title=ep_title)
            draw_rect(self.page, MARGIN_L, self.y - 10, CONTENT_W, 13, CODE_BG)
            draw_rect(self.page, MARGIN_L, self.y - 10, 3, 13, ACCENT)
            self.page.insert_text(fitz.Point(MARGIN_L + 10, self.y - 1), wline, fontsize=7, fontname=self.mono_font, color=TEXT_PRIMARY)
            self.y += 13

        self.y += 10

    def build_cover_page(self):
        page = self.doc[0]
        # Background
        draw_rect(page, 0, 0, W, H, BG_DARK)
        
        # Left thick vertical accent stripe
        draw_rect(page, 0, 0, 15, H, ACCENT)
        draw_rect(page, 15, 0, 5, H, ACCENT_TEAL)
        
        # Top gradient/accent border
        draw_rect(page, 0, 0, W, 8, ACCENT)
        
        # Decorative abstract shape in top right corner
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(W - 120, -20, W + 20, 120), radius=0.2)
        shape.finish(fill=(0.12, 0.15, 0.23), color=(0.12, 0.15, 0.23))
        shape.commit()
        
        # Draw stylized dental cross logo (replacement for non-rendering 🦷 emoji)
        logo_x = MARGIN_L + 10
        logo_y = 180
        draw_rect(page, logo_x, logo_y, 70, 70, ACCENT, radius=0.25)
        draw_rect(page, logo_x + 28, logo_y + 15, 14, 40, WHITE, radius=0.1)
        draw_rect(page, logo_x + 15, logo_y + 28, 40, 14, WHITE, radius=0.1)
        
        y = 290
        page.insert_text(fitz.Point(MARGIN_L + 10, y), "Assnani Dental AI Chatbot", fontsize=30, fontname=self.bold_font, color=TEXT_PRIMARY)
        y += 36
        page.insert_text(fitz.Point(MARGIN_L + 10, y), "API Reference & Endpoint Documentation", fontsize=15, fontname=self.default_font, color=ACCENT_TEAL)
        y += 45
        
        shape = page.new_shape()
        shape.draw_line(fitz.Point(MARGIN_L + 10, y), fitz.Point(W - MARGIN_R, y))
        shape.finish(color=DIVIDER, width=1)
        shape.commit()
        y += 30
        
        card_h = 110
        draw_rect(page, MARGIN_L + 10, y, CONTENT_W - 10, card_h, BG_CARD, radius=0.08)
        
        meta_lines = [
            f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            "Version: 1.0.0",
            "Framework: FastAPI (Python)",
            "Base URL: http://localhost:7860  |  HF Spaces Port 7860",
            f"Total Endpoints: {len(ENDPOINTS)}",
        ]
        
        meta_y = y + 20
        for line in meta_lines:
            page.insert_text(fitz.Point(MARGIN_L + 25, meta_y), line, fontsize=9.5, fontname=self.default_font, color=TEXT_SEC)
            meta_y += 18
            
        page.insert_text(fitz.Point(MARGIN_L + 10, H - 45), "Assnani Dental Clinic Management System", fontsize=9.5, fontname=self.bold_font, color=TEXT_PRIMARY)
        page.insert_text(fitz.Point(MARGIN_L + 10, H - 32), "Graduation Project — Faculty of Dentistry & Computer Science", fontsize=8.5, fontname=self.default_font, color=TEXT_SEC)

    def build_toc_page(self):
        page = self.doc[1]
        draw_rect(page, 0, 0, W, H, BG_DARK)
        draw_rect(page, 0, 0, W, 8, ACCENT)
        
        y = MARGIN_T + 10
        page.insert_text(fitz.Point(MARGIN_L, y), "Table of Contents", fontsize=22, fontname=self.bold_font, color=TEXT_PRIMARY)
        y += 12
        page.insert_text(fitz.Point(MARGIN_L, y), "Overview of available API endpoints and integration routes", fontsize=9.5, fontname=self.default_font, color=TEXT_SEC)
        y += 30
        
        shape = page.new_shape()
        shape.draw_line(fitz.Point(MARGIN_L, y), fitz.Point(W - MARGIN_R, y))
        shape.finish(color=DIVIDER, width=1)
        shape.commit()
        y += 25
        
        timeline_x = MARGIN_L + 12
        timeline_start_y = y
        
        for i, ep in enumerate(ENDPOINTS):
            page_num = self.page_num_map.get(i, 0) + 1
            method = ep["method"]
            method_color = METHOD_GET if method == "GET" else METHOD_POST
            
            dot_shape = page.new_shape()
            dot_shape.draw_circle(fitz.Point(timeline_x, y + 4), 3.5)
            dot_shape.finish(fill=method_color, color=method_color)
            dot_shape.commit()
            
            badge_x = timeline_x + 15
            tw = len(method) * 8 * 0.55 + 10
            rect = fitz.Rect(badge_x, y - 6, badge_x + tw, y + 10)
            b_shape = page.new_shape()
            b_shape.draw_rect(rect, radius=0.25)
            b_shape.finish(fill=method_color, color=method_color)
            b_shape.commit()
            page.insert_text(fitz.Point(badge_x + 5, y + 5), method, fontsize=8, fontname=self.bold_font, color=WHITE)
            
            path_x = badge_x + tw + 10
            page.insert_text(fitz.Point(path_x, y + 6), ep["path"], fontsize=10.5, fontname=self.bold_font, color=TEXT_PRIMARY)
            
            page_str = f"Page {page_num}"
            page.insert_text(fitz.Point(W - MARGIN_R - 50, y + 6), page_str, fontsize=9.5, fontname=self.bold_font, color=ACCENT_TEAL)
            
            y += 18
            page.insert_text(fitz.Point(path_x, y + 3), ep["summary"], fontsize=8.5, fontname=self.default_font, color=TEXT_SEC)
            y += 26
            
        line_shape = page.new_shape()
        line_shape.draw_line(fitz.Point(timeline_x, timeline_start_y), fitz.Point(timeline_x, y - 26))
        line_shape.finish(color=DIVIDER, width=1.5)
        line_shape.commit()

    def draw_error_table(self):
        self.add_page(title="Appendix: Error Responses")
        self.y += 10
        self.page.insert_text(fitz.Point(MARGIN_L, self.y), "Appendix: Error Responses", fontsize=16, fontname=self.bold_font, color=TEXT_PRIMARY)
        self.y += 24
        
        errors = [
            ("400", "Bad Request", "Missing or invalid input data", '{"error": "No valid images found in the uploaded files."}'),
            ("400", "Bad Request", "No detection input provided", '{"error": "Provide \'api_response\' or \'detections\'."}'),
            ("500", "Internal Server Error", "Unexpected processing error", '{"error": "Error processing X-ray: <details>"}'),
            ("502", "Bad Gateway", "External API returned non-200", '{"error": "Treatment API returned 502", "detail": "<response text>"}'),
            ("504", "Gateway Timeout", "External API timed out after retries", '{"error": "YOLO API timed out after retries. Please try again."}'),
            ("504", "Gateway Timeout", "AI report generation timed out", '{"error": "AI report timed out. Gemini may be loading — try again."}'),
        ]
        
        headers = ["Status", "Meaning", "Cause", "Example Body"]
        col_widths = [50, 90, 140, CONTENT_W - 280]
        
        draw_rect(self.page, MARGIN_L, self.y - 11, CONTENT_W, 16, TABLE_HEAD, radius=0.15)
        x = MARGIN_L + 6
        for hi, hw in zip(headers, col_widths):
            self.page.insert_text(fitz.Point(x, self.y), hi, fontsize=8, fontname=self.bold_font, color=ACCENT)
            x += hw
        self.y += 14
        
        for ri, (code, meaning, cause, body) in enumerate(errors):
            body_chars = int((col_widths[3] - 10) / 3.8)
            body_lines = max(1, (len(body) // body_chars) + 1)
            row_h = body_lines * 12 + 6
            
            self.ensure_space(row_h + 10, title="Appendix: Error Responses")
            row_color = TABLE_ROW1 if ri % 2 == 0 else TABLE_ROW2
            draw_rect(self.page, MARGIN_L, self.y - 10, CONTENT_W, row_h, row_color)
            
            x = MARGIN_L + 6
            self.page.insert_text(fitz.Point(x, self.y - 1), code, fontsize=8, fontname=self.bold_font, color=SEVERITY_HI)
            x += col_widths[0]
            self.page.insert_text(fitz.Point(x, self.y - 1), meaning, fontsize=8, fontname=self.default_font, color=TEXT_PRIMARY)
            x += col_widths[1]
            self.draw_text_at(x, self.y - 1, cause, fontsize=7.5, color=TEXT_SEC, fontname=self.default_font, max_width=col_widths[2] - 10)
            x += col_widths[2]
            self.draw_text_at(x, self.y - 1, body, fontsize=6.5, color=ACCENT_TEAL, fontname=self.mono_font, max_width=col_widths[3] - 10)
            
            self.y += row_h

    def draw_external_apis_table(self):
        self.ensure_space(150, title="Appendix: External APIs")
        self.y += 20
        self.page.insert_text(fitz.Point(MARGIN_L, self.y), "Appendix: External APIs", fontsize=16, fontname=self.bold_font, color=TEXT_PRIMARY)
        self.y += 24
        
        ext_apis = [
            ("YOLO Detection", "POST", "https://0xker-dental-x-ray-detection.hf.space/predict", "image (multipart)", "JSON with detections + annotated image (b64)"),
            ("YOLO Annotated", "POST", "...predict?format=image", "image (multipart)", "Raw annotated image bytes"),
            ("Treatment / AI", "POST", "https://0xker-treat-recommend.hf.space/api/analyze", "image + model (multipart)", "JSON with report (HTML), by_class, image_b64"),
        ]
        
        headers = ["API", "Method", "URL", "Request Key", "Response"]
        col_widths = [85, 40, 165, 80, CONTENT_W - 370]
        
        draw_rect(self.page, MARGIN_L, self.y - 11, CONTENT_W, 16, TABLE_HEAD, radius=0.15)
        x = MARGIN_L + 6
        for hi, hw in zip(headers, col_widths):
            self.page.insert_text(fitz.Point(x, self.y), hi, fontsize=8, fontname=self.bold_font, color=ACCENT)
            x += hw
        self.y += 14
        
        for ri, (name, method, url, req_key, resp) in enumerate(ext_apis):
            row_h = 24
            self.ensure_space(row_h + 10, title="Appendix: External APIs")
            row_color = TABLE_ROW1 if ri % 2 == 0 else TABLE_ROW2
            draw_rect(self.page, MARGIN_L, self.y - 10, CONTENT_W, row_h, row_color)
            
            x = MARGIN_L + 6
            self.page.insert_text(fitz.Point(x, self.y + 2), name, fontsize=7.5, fontname=self.bold_font, color=TEXT_PRIMARY)
            x += col_widths[0]
            
            method_color = METHOD_GET if method == "GET" else METHOD_POST
            rect = fitz.Rect(x, self.y - 3, x + 30, self.y + 9)
            m_shape = self.page.new_shape()
            m_shape.draw_rect(rect, radius=0.25)
            m_shape.finish(fill=method_color, color=method_color)
            m_shape.commit()
            self.page.insert_text(fitz.Point(x + 4, self.y + 6), method, fontsize=6.5, fontname=self.bold_font, color=WHITE)
            x += col_widths[1]
            
            self.draw_text_at(x, self.y + 2, url, fontsize=6.5, color=ACCENT_TEAL, fontname=self.mono_font, max_width=col_widths[2] - 10)
            x += col_widths[2]
            
            self.page.insert_text(fitz.Point(x, self.y + 2), req_key, fontsize=7.5, fontname=self.default_font, color=TEXT_SEC)
            x += col_widths[3]
            
            self.draw_text_at(x, self.y + 2, resp, fontsize=7, color=TEXT_SEC, fontname=self.default_font, max_width=col_widths[4] - 10)
            
            self.y += row_h

def build_pdf():
    doc = fitz.open()

    cover_page = doc.new_page(width=W, height=H)
    toc_page = doc.new_page(width=W, height=H)

    writer = PDFWriter(doc)

    for ep_idx, ep in enumerate(ENDPOINTS):
        title_for_header = f"Endpoint: {ep['path']}"
        writer.add_page(title=title_for_header, ep_idx=ep_idx)
        
        writer.page.insert_text(fitz.Point(MARGIN_L, writer.y), f"ENDPOINT {ep_idx + 1} OF {len(ENDPOINTS)}", fontsize=8, fontname=writer.bold_font, color=TEXT_SEC)
        writer.y += 14
        
        badge_w = writer.draw_method_badge(MARGIN_L, writer.y, ep["method"])
        writer.page.insert_text(fitz.Point(MARGIN_L + badge_w + 10, writer.y), ep["path"], fontsize=18, fontname=writer.bold_font, color=TEXT_PRIMARY)
        writer.y += 18
        
        writer.page.insert_text(fitz.Point(MARGIN_L, writer.y), ep["summary"], fontsize=12, fontname=writer.bold_font, color=ACCENT)
        writer.y += 20
        
        writer.y += 4
        writer.draw_text_at(MARGIN_L, writer.y, ep["description"], fontsize=9.5, color=TEXT_SEC, fontname=writer.default_font, max_width=CONTENT_W)
        chars_per_line = int(CONTENT_W / (9.5 * 0.42))
        desc_lines = len(textwrap.wrap(ep["description"], width=chars_per_line))
        writer.y += desc_lines * 12 + 16
        
        shape = writer.page.new_shape()
        shape.draw_line(fitz.Point(MARGIN_L, writer.y), fitz.Point(W - MARGIN_R, writer.y))
        shape.finish(color=DIVIDER, width=0.5)
        shape.commit()
        writer.y += 16
        
        if ep["request_body"]:
            keys = ep["request_body"]["keys"]
            col_widths = [150, 80, 140, CONTENT_W - 370]
            headers = ["Key", "Type", "Example", "Description"]
            writer.draw_table_section(
                f"REQUEST BODY ({ep['request_body']['model']})",
                keys, col_widths, headers,
                ep_title=title_for_header
            )
            
        if ep.get("example_request"):
            writer.draw_code_block("EXAMPLE REQUEST", ep["example_request"], ep_title=title_for_header)
            
        if ep.get("response") and ep["response"].get("keys"):
            keys = ep["response"]["keys"]
            col_widths = [155, 75, 140, CONTENT_W - 370]
            headers = ["Key", "Type", "Example", "Description"]
            writer.draw_table_section(
                f"RESPONSE BODY ({ep['response']['type']})",
                keys, col_widths, headers,
                ep_title=title_for_header
            )
            
        if ep.get("example_response"):
            writer.draw_code_block("EXAMPLE RESPONSE", ep["example_response"], ep_title=title_for_header)

    writer.draw_error_table()
    writer.draw_external_apis_table()

    writer.build_cover_page()
    writer.build_toc_page()

    total_pages = len(doc)
    for idx in range(1, total_pages):
        page = doc[idx]
        shape = page.new_shape()
        shape.draw_line(fitz.Point(MARGIN_L, H - 36), fitz.Point(W - MARGIN_R, H - 36))
        shape.finish(color=DIVIDER, width=0.5)
        shape.commit()
        
        page.insert_text(
            fitz.Point(MARGIN_L, H - 24),
            "Assnani Dental AI Chatbot — Graduation Project Document",
            fontsize=8,
            fontname="helv",
            color=TEXT_SEC,
        )
        page.insert_text(
            fitz.Point(W - MARGIN_R - 60, H - 24),
            f"Page {idx + 1} of {total_pages}",
            fontsize=8,
            fontname="helv",
            color=TEXT_SEC,
        )

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Chatbot_API_Reference.pdf")
    doc.save(output_path)
    doc.close()
    print(f"[OK] PDF generated: {output_path}")
    temp_doc = fitz.open(output_path)
    print(f"     Pages: {len(temp_doc)}")
    temp_doc.close()
    return output_path


if __name__ == "__main__":
    build_pdf()

