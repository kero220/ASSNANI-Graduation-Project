import os
import time
import requests
import markdown
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from google.genai.types import HarmCategory, HarmBlockThreshold
from collections import defaultdict

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6LWfs6Z5xwx8D-XsQBBqhZeQo-vdW3r_sQGxzSJCYISyw")
DETECTION_ENDPOINT  = os.environ.get(
    "DETECTION_ENDPOINT",
    "https://0xker-dental-x-ray-detection.hf.space/predict"
)
GEMINI_MODEL        = "gemini-2.5-flash"

CLASS_INFO = {
    "cavity"  : "dental caries / tooth decay",
    "filling" : "existing dental restoration / composite or amalgam filling",
    "implant" : "osseointegrated dental implant (titanium post)",
    "impacted": "impacted tooth (failed to fully erupt through the gum line)",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_gemini_client():
    key = GEMINI_API_KEY
    if not key or not key.strip():
        raise ValueError("GEMINI_API_KEY environment variable is not set or empty.")
    return genai.Client(api_key=key)

def b64_to_data_uri(b64_string: str, mime_type: str = "image/jpeg") -> str:
    if b64_string and not b64_string.startswith("data:"):
        return f"data:{mime_type};base64,{b64_string}"
    return b64_string or ""

def parse_detections(api_response: dict) -> dict:
    if "data" in api_response and isinstance(api_response["data"], list) and len(api_response["data"]) > 0:
        api_response = api_response["data"][0]

    results_array = api_response.get("results", [])
    if not results_array or not isinstance(results_array, list):
        raise ValueError("Could not find valid 'results' array in payload")

    inner_payload = results_array[0]
    if not isinstance(inner_payload, dict):
        raise ValueError("First item in 'results' is not a valid JSON object")

    raw_detections = inner_payload.get("detections", [])
    if not isinstance(raw_detections, list):
        raise ValueError("'detections' field is missing or not a valid list")

    filename       = inner_payload.get("filename", "unknown.jpg")
    image_b64      = inner_payload.get("result_image_b64", None)

    by_class = defaultdict(list)
    for det in raw_detections:
        if not isinstance(det, dict) or "class_name" not in det or "confidence" not in det:
            continue
        by_class[det["class_name"]].append(det)

    summary_lines = []
    for cls, items in by_class.items():
        confidences = [d.get("confidence", 0.0) for d in items]
        avg_conf  = sum(confidences) / len(items) if items else 0.0
        locations = [
            f"(conf={d.get('confidence', 0.0):.0%})"
            for d in items
        ]
        desc = CLASS_INFO.get(cls, cls)
        summary_lines.append(
            f"  • {cls.upper()} [{desc}]\n"
            f"    Count: {len(items)}, Avg confidence: {avg_conf:.1%}\n"
        )

    if not summary_lines:
        summary_lines = ["  • No pathologies detected."]

    return {
        "filename" : filename,
        "total"    : len(raw_detections),
        "by_class" : dict(by_class),
        "summary"  : summary_lines,
        "image_b64": image_b64,
        "raw"      : raw_detections,
    }

def build_system_prompt() -> str:
    return (
        "You are an expert Dental Radiologist and Maxillofacial Specialist reviewing a patient's X-ray data. "
        "Generate a highly realistic, professional clinical chart note based on the provided YOLOv8 detections. "
        "Assume the role of the attending clinician. Use advanced dental and anatomical terminology "
        "(e.g., radiolucency, osseointegration, pericoronitis, mesioangular impaction, dentin involvement). "
        "Your report must be structured professionally and include:\n\n"
        "1. **Radiographic Findings:** A detailed clinical breakdown of each detection, assessing likely severity, depth, and spatial context.\n"
        "2. **Clinical Impression:** A realistic diagnostic assessment based strictly on the provided findings.\n"
        "3. **Proposed Treatment Plan:** Specific, actionable restorative, surgical, or preventative interventions (e.g., 'Class II composite restoration', 'Surgical extraction with bone grafting', 'Monitor for arrestment').\n\n"
        "Format the output strictly as a formal medical chart note using markdown headings."
    )

def build_user_message(parsed: dict) -> str:
    lines = "\n".join(parsed["summary"])
    return (
        f"X-Ray File: {parsed['filename']}\n"
        f"Total Findings: {parsed['total']}\n\n"
        f"Detection Data:\n{lines}\n\n"
        "Generate the complete clinical chart note based on these findings."
    )

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        files = request.files.getlist("image")
        if not files or len(files) == 0:
            return jsonify({"error": "No images uploaded"}), 400

        # NEW: Read the model chosen by the user from the frontend
        # Default to "gemini-2.5-flash" if something goes wrong
        selected_model = request.form.get("model", "gemini-2.5-flash")

        try:
            gemini = get_gemini_client()
        except Exception as e:
            return jsonify({"error": f"Failed to initialize Gemini Client: {str(e)}"}), 500

        system = build_system_prompt()
        all_results = {}

        for image_file in files:
            image_bytes = image_file.read()
            if not image_bytes: continue
            
            mime  = image_file.content_type or "image/jpeg"
            fname = image_file.filename or "xray.jpg"

            # Validate file extension
            ext = os.path.splitext(fname)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
                all_results[fname] = {
                    "error": f"Unsupported file type '{ext}'. Please upload JPG, PNG, WEBP, or BMP images."
                }
                continue

            try:
                # 1. Call YOLOv8 API
                try:
                    det_resp = requests.post(
                        DETECTION_ENDPOINT,
                        files={"image": (fname, image_bytes, mime)},
                        timeout=60,
                    )
                    if not det_resp.ok:
                        raise Exception(f"Detection API returned status code {det_resp.status_code}")
                    try:
                        det_json = det_resp.json()
                    except Exception as json_err:
                        raise Exception(f"Detection API returned invalid JSON: {json_err}")

                    parsed = parse_detections(det_json)
                    parsed["filename"] = fname 
                except requests.exceptions.Timeout:
                    raise Exception("Detection API timed out. The server took too long to respond.")
                except requests.exceptions.ConnectionError:
                    raise Exception("Failed to connect to the Detection API. The server might be offline.")
                except Exception as det_err:
                    raise Exception(f"Detection failed: {det_err}")

                # 2. Call Gemini
                report_html = ""
                try:
                    user = build_user_message(parsed)
                    response = gemini.models.generate_content(
                        model=selected_model,   # <--- NEW: Uses the dynamic dropdown model!
                        contents=[
                            types.Part.from_bytes(data=image_bytes, mime_type=mime),
                            system + "\n\n" + user,
                        ],
                        config=types.GenerateContentConfig(
                            max_output_tokens=4096, 
                            temperature=0.3,
                            safety_settings=[
                                types.SafetySetting(
                                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                    threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
                                )
                            ]
                        ),
                    )
                    
                    # Robust Cut-off Error Handling
                    report_text = response.text if response.text else ""
                    
                    if response.candidates and response.candidates[0].finish_reason != types.FinishReason.STOP:
                        stop_reason = response.candidates[0].finish_reason.name
                        report_text += f"\n\n> ⚠️ **Notice:** This report was cut off early. Reason: `{stop_reason}`"
                    elif not report_text:
                        report_text = "⚠️ Report generation was completely blocked by safety filters."

                    report_html = markdown.markdown(report_text, extensions=['extra', 'nl2br'])
                except Exception as gemini_err:
                    import traceback
                    print(f"Gemini API error for {fname}: {traceback.format_exc()}")
                    report_html = (
                        f"<div class='error-box show' style='margin: 0; padding: 1rem; border-radius: 6px;'>"
                        f"<strong>AI Report Generation Failed:</strong> {str(gemini_err)}"
                        f"</div>"
                    )

                annotated_uri = b64_to_data_uri(parsed["image_b64"])

                # CHANGED: Map data directly to the filename key
                all_results[fname] = {
                    "total"    : parsed["total"],
                    "by_class" : {cls: len(items) for cls, items in parsed["by_class"].items()},
                    "image_b64": annotated_uri,
                    "report"   : report_html,
                    "error"    : None
                }
                
                # Pause to prevent rate limiting on batch uploads
                time.sleep(5)

            except Exception as e:
                import traceback
                print(f"Error processing {fname}: {traceback.format_exc()}")
                all_results[fname] = {
                    "error": str(e)
                }

        return jsonify({"results": all_results})

    except Exception as exc:
        import traceback
        print(f"ERROR in /api/analyze: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(exc)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, debug=False)