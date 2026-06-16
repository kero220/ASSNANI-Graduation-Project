class DentalTreatmentRecommender:
    """
    Takes YOLO detection API results and generates structured
    treatment recommendations with specialist referrals.
    """

    def __init__(self, large_cavity_threshold=5000):
        # Threshold for bounding box area (width * height) to consider a cavity "large"
        self.large_cavity_threshold = large_cavity_threshold

    def analyze_api_response(self, api_response: dict) -> dict:
        """
        Takes the full JSON response from the YOLO detection API
        and returns a structured treatment recommendation plan.

        Expected format:
        {
            "results": [{
                "detections": [...],
                "filename": "...",
                "result_image_b64": "...",
                "total_detections": N
            }],
            "success": true,
            "total_images": 1
        }
        """
        if not api_response.get("success", False):
            return {"error": "The detection API returned an unsuccessful response."}

        if "results" not in api_response or not api_response["results"]:
            return {"error": "No results found in the API response."}

        first_result = api_response["results"][0]
        detections = first_result.get("detections", [])
        filename = first_result.get("filename", "unknown_image")
        total_detections = first_result.get("total_detections", len(detections))

        recommendations = []
        specialists = set()
        counts = {"cavity": 0, "filling": 0, "implant": 0, "impacted": 0}

        for idx, detection in enumerate(detections):
            cls = detection.get("class_name", "").lower()
            conf = detection.get("confidence", 0.0)

            # Calculate bounding box area for severity estimation
            width = detection.get("width", 0)
            height = detection.get("height", 0)

            if width > 0 and height > 0:
                area = width * height
            else:
                x1 = detection.get("x1", 0)
                y1 = detection.get("y1", 0)
                x2 = detection.get("x2", 0)
                y2 = detection.get("y2", 0)
                area = (x2 - x1) * (y2 - y1)

            if cls in counts:
                counts[cls] += 1

            # --- Cavity Logic ---
            if cls == "cavity":
                if area > self.large_cavity_threshold:
                    rec = {
                        "finding": f"Large/Deep Cavity",
                        "confidence": f"{conf:.0%}",
                        "area": area,
                        "severity": "high",
                        "treatment": "Root Canal Treatment (Endodontics) followed by a Crown restoration. Vitality test recommended.",
                        "specialist": "Endodontist",
                        "icon": "🦷"
                    }
                    specialists.add("Endodontist")
                else:
                    rec = {
                        "finding": f"Small/Medium Cavity",
                        "confidence": f"{conf:.0%}",
                        "area": area,
                        "severity": "moderate",
                        "treatment": "Dental Restoration — Composite or Amalgam filling to restore tooth structure.",
                        "specialist": "General Dentist",
                        "icon": "🔧"
                    }
                specialists.add("General Dentist")
                recommendations.append(rec)

            # --- Impacted Tooth Logic ---
            elif cls == "impacted":
                rec = {
                    "finding": "Impacted Tooth",
                    "confidence": f"{conf:.0%}",
                    "area": area,
                    "severity": "high",
                    "treatment": "Surgical Extraction recommended to prevent infection, pain, or damage to adjacent teeth. Pre-operative assessment required.",
                    "specialist": "Oral & Maxillofacial Surgeon",
                    "icon": "⚠️"
                }
                recommendations.append(rec)
                specialists.add("Oral & Maxillofacial Surgeon")

            # --- Existing Filling Logic ---
            elif cls == "filling":
                rec = {
                    "finding": "Existing Filling",
                    "confidence": f"{conf:.0%}",
                    "area": area,
                    "severity": "low",
                    "treatment": "Routine monitoring. Check margins clinically and radiographically for secondary caries. Replace if deteriorating.",
                    "specialist": "General Dentist",
                    "icon": "✅"
                }
                recommendations.append(rec)
                specialists.add("General Dentist")

            # --- Dental Implant Logic ---
            elif cls == "implant":
                rec = {
                    "finding": "Dental Implant",
                    "confidence": f"{conf:.0%}",
                    "area": area,
                    "severity": "low",
                    "treatment": "Routine clinical maintenance. Assess bone levels and check for signs of peri-implantitis. Professional cleaning recommended.",
                    "specialist": "Periodontist",
                    "icon": "🔩"
                }
                recommendations.append(rec)
                specialists.add("Periodontist")

        return {
            "patient_file": filename,
            "total_detections": total_detections,
            "summary": counts,
            "recommendations": recommendations,
            "specialists": list(specialists),
            "disclaimer": "⚠️ This is an AI-assisted preliminary analysis. Final diagnosis and treatment plan must be verified by a licensed dental professional."
        }

    def analyze_detections(self, detections: list) -> dict:
        """
        Convenience method — analyze a list of detections directly
        (without the full API response wrapper).
        """
        wrapped = {
            "results": [{
                "detections": detections,
                "filename": "uploaded_xray",
                "total_detections": len(detections)
            }],
            "success": True,
            "total_images": 1
        }
        return self.analyze_api_response(wrapped)
