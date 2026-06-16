"""
Assnani Dental Chatbot — Symptom-to-X-ray Correlation Engine
Matches patient-reported symptoms with YOLO detection findings
and generates natural language explanations.
"""


class CorrelationEngine:
    """
    Correlates patient symptoms with YOLO X-ray detection results.
    Produces human-readable explanations linking complaints to findings.
    """

    # Mapping of detection classes to symptom-relevant conditions
    CONDITION_MAP = {
        "cavity": {
            "clinical_name": "Dental Caries (Cavity)",
            "description": "tooth decay that has damaged the tooth structure",
            "pain_correlations": {
                "throbbing": {
                    "explanation": "The cavity may have reached the tooth nerve (pulp), causing inflammation (pulpitis) and throbbing pain.",
                    "severity": "high",
                    "urgency": "Prompt treatment recommended to prevent further nerve damage."
                },
                "sharp": {
                    "explanation": "The cavity has exposed sensitive tooth layers (dentin), causing sharp pain when stimulated.",
                    "severity": "moderate",
                    "urgency": "Treatment recommended within a few days."
                },
                "dull": {
                    "explanation": "The cavity may be causing chronic low-grade inflammation in the tooth.",
                    "severity": "moderate",
                    "urgency": "Schedule a dental visit for evaluation."
                },
                "sensitivity": {
                    "explanation": "The cavity has likely penetrated the enamel, exposing the dentin layer which is sensitive to temperature changes.",
                    "severity": "moderate",
                    "urgency": "A dental filling can resolve this sensitivity."
                },
            },
            "swelling_correlation": {
                "explanation": "Deep decay may have led to an infection at the tooth root (periapical abscess), causing swelling.",
                "severity": "high",
                "urgency": "Urgent dental care is needed. Antibiotics and root canal treatment may be required."
            },
            "default_correlation": {
                "explanation": "Dental caries (cavity) was detected on this tooth. Even without current symptoms, untreated cavities can progress and cause pain.",
                "severity": "moderate",
                "urgency": "Treatment with a dental filling is recommended."
            }
        },
        "impacted": {
            "clinical_name": "Impacted Tooth",
            "description": "a tooth that has not fully erupted and is trapped in the jawbone or gum tissue",
            "pain_correlations": {
                "throbbing": {
                    "explanation": "The impacted tooth may be pressing against adjacent teeth or causing inflammation in surrounding tissue (pericoronitis).",
                    "severity": "high",
                    "urgency": "Surgical extraction may be necessary to relieve pressure."
                },
                "sharp": {
                    "explanation": "The impacted tooth may be causing pressure on the nerve of an adjacent tooth.",
                    "severity": "moderate",
                    "urgency": "Evaluation for possible extraction recommended."
                },
                "dull": {
                    "explanation": "The impacted tooth is causing chronic pressure in the jaw area.",
                    "severity": "moderate",
                    "urgency": "Monitor and consult with an oral surgeon."
                },
                "sensitivity": {
                    "explanation": "Partial eruption of the impacted tooth may be trapping food and causing decay on adjacent teeth.",
                    "severity": "moderate",
                    "urgency": "Evaluation for extraction recommended."
                },
            },
            "swelling_correlation": {
                "explanation": "The impacted tooth has likely caused pericoronitis — an infection of the gum tissue around the partially erupted tooth, resulting in swelling.",
                "severity": "high",
                "urgency": "Antibiotics may be needed, followed by surgical extraction."
            },
            "default_correlation": {
                "explanation": "An impacted tooth was detected. Impacted teeth can cause problems over time including cysts, infection, or damage to neighboring teeth.",
                "severity": "moderate",
                "urgency": "Consultation with an oral surgeon is recommended."
            }
        },
        "filling": {
            "clinical_name": "Existing Dental Filling",
            "description": "a previously placed dental restoration",
            "pain_correlations": {
                "throbbing": {
                    "explanation": "The existing filling may have developed secondary caries (new decay) underneath, potentially reaching the nerve.",
                    "severity": "high",
                    "urgency": "The filling may need to be replaced. Root canal treatment might be necessary."
                },
                "sharp": {
                    "explanation": "The filling may have a marginal gap or fracture, allowing stimuli to reach the underlying tooth structure.",
                    "severity": "moderate",
                    "urgency": "The filling should be evaluated and possibly replaced."
                },
                "dull": {
                    "explanation": "The existing filling may be deteriorating, causing low-grade irritation to the tooth.",
                    "severity": "low",
                    "urgency": "Schedule an evaluation to assess filling integrity."
                },
                "sensitivity": {
                    "explanation": "The filling margins may have opened, allowing temperature changes to reach the sensitive dentin layer.",
                    "severity": "moderate",
                    "urgency": "The filling may need replacement with a new restoration."
                },
            },
            "swelling_correlation": {
                "explanation": "Secondary infection may have developed beneath the existing filling, causing swelling.",
                "severity": "high",
                "urgency": "Urgent evaluation needed. The filling must be removed and the tooth assessed."
            },
            "default_correlation": {
                "explanation": "An existing dental filling was detected. Regular monitoring is recommended to check for secondary caries and filling integrity.",
                "severity": "low",
                "urgency": "Routine clinical monitoring at regular checkups."
            }
        },
        "implant": {
            "clinical_name": "Dental Implant",
            "description": "a previously placed dental implant",
            "pain_correlations": {
                "throbbing": {
                    "explanation": "Throbbing pain near an implant may indicate peri-implantitis — inflammation and possible bone loss around the implant.",
                    "severity": "high",
                    "urgency": "Urgent evaluation by a periodontist is recommended."
                },
                "sharp": {
                    "explanation": "Sharp pain near the implant area may indicate the implant is affecting adjacent tooth nerves or has a loose component.",
                    "severity": "moderate",
                    "urgency": "Evaluation to check implant stability and adjacent structures."
                },
                "dull": {
                    "explanation": "Dull discomfort around an implant may indicate early signs of peri-implant mucositis (gum inflammation).",
                    "severity": "moderate",
                    "urgency": "Schedule evaluation to assess implant health."
                },
                "sensitivity": {
                    "explanation": "While implants themselves don't have nerves, sensitivity near the implant may be from adjacent natural teeth being affected.",
                    "severity": "low",
                    "urgency": "Monitor and report if symptoms worsen."
                },
            },
            "swelling_correlation": {
                "explanation": "Swelling around the implant strongly suggests peri-implantitis — a serious condition that can lead to implant failure and bone loss.",
                "severity": "high",
                "urgency": "Immediate evaluation by a periodontist or implant specialist is critical."
            },
            "default_correlation": {
                "explanation": "A dental implant was detected. Regular maintenance is important to prevent peri-implantitis and ensure long-term success.",
                "severity": "low",
                "urgency": "Routine monitoring of bone levels and implant stability."
            }
        }
    }

    # Quadrant mapping based on X-ray image coordinates
    # Standard dental X-ray: upper teeth at top, lower at bottom
    # Patient's right = image left, Patient's left = image right (mirrored)
    QUADRANT_MAP = {
        "upper-right": "Upper Right (Quadrant 1, teeth 11-18)",
        "upper-left": "Upper Left (Quadrant 2, teeth 21-28)",
        "lower-left": "Lower Left (Quadrant 3, teeth 31-38)",
        "lower-right": "Lower Right (Quadrant 4, teeth 41-48)",
    }

    def correlate(self, symptoms: dict, detections: list, image_width: int = 0, image_height: int = 0) -> dict:
        """
        Correlate patient symptoms with YOLO detection results.

        Args:
            symptoms: Patient symptom data from the chatbot conversation
            detections: List of detection dicts from YOLO API
            image_width: Width of the X-ray image (for quadrant mapping)
            image_height: Height of the X-ray image (for quadrant mapping)

        Returns:
            dict with correlations, unmatched symptoms, and unmatched findings
        """
        pain_location = symptoms.get("pain_location", "").lower()
        pain_type = symptoms.get("pain_type", "").lower()
        has_swelling = symptoms.get("has_swelling", False)
        has_pain = symptoms.get("has_pain", False)

        correlations = []
        matched_detection_indices = set()

        for idx, det in enumerate(detections):
            cls = det.get("class_name", "").lower()
            conf = det.get("confidence", 0.0)
            condition = self.CONDITION_MAP.get(cls)

            if not condition:
                continue

            # Determine detection quadrant from bounding box position
            det_quadrant = self._get_quadrant(det, image_width, image_height)
            det_region_label = self.QUADRANT_MAP.get(det_quadrant, det_quadrant)

            # Check if symptom location matches detection region
            location_match = self._locations_match(pain_location, det_quadrant)

            correlation_entry = {
                "detection_index": idx,
                "class_name": cls,
                "clinical_name": condition["clinical_name"],
                "confidence": conf,
                "confidence_label": self._confidence_label(conf),
                "detection_region": det_region_label,
                "location_match": location_match,
                "severity": "low",
                "explanation": "",
                "urgency": "",
            }

            if location_match and has_pain and pain_type in condition["pain_correlations"]:
                # Strong correlation: location + pain type match
                corr_data = condition["pain_correlations"][pain_type]
                correlation_entry["explanation"] = (
                    f"You mentioned {pain_type} pain in the {pain_location} region. "
                    f"Our AI detected {condition['description']} in the same area "
                    f"({conf:.0%} confidence). {corr_data['explanation']}"
                )
                correlation_entry["severity"] = corr_data["severity"]
                correlation_entry["urgency"] = corr_data["urgency"]
                correlation_entry["match_type"] = "strong"
                matched_detection_indices.add(idx)

            elif location_match and has_swelling:
                # Swelling correlation
                corr_data = condition["swelling_correlation"]
                correlation_entry["explanation"] = (
                    f"You reported swelling in the {pain_location} region. "
                    f"Our AI detected {condition['description']} in that area "
                    f"({conf:.0%} confidence). {corr_data['explanation']}"
                )
                correlation_entry["severity"] = corr_data["severity"]
                correlation_entry["urgency"] = corr_data["urgency"]
                correlation_entry["match_type"] = "swelling"
                matched_detection_indices.add(idx)

            elif location_match:
                # Location match but no specific symptom correlation
                corr_data = condition["default_correlation"]
                correlation_entry["explanation"] = (
                    f"Our AI detected {condition['description']} in the {pain_location} region "
                    f"({conf:.0%} confidence). {corr_data['explanation']}"
                )
                correlation_entry["severity"] = corr_data["severity"]
                correlation_entry["urgency"] = corr_data["urgency"]
                correlation_entry["match_type"] = "location"
                matched_detection_indices.add(idx)

            else:
                # No location match — still report the finding
                corr_data = condition["default_correlation"]
                correlation_entry["explanation"] = (
                    f"Our AI also detected {condition['description']} in the {det_region_label} "
                    f"({conf:.0%} confidence). {corr_data['explanation']}"
                )
                correlation_entry["severity"] = corr_data["severity"]
                correlation_entry["urgency"] = corr_data["urgency"]
                correlation_entry["match_type"] = "additional"

            correlations.append(correlation_entry)

        # Sort: strong matches first, then by severity
        severity_order = {"high": 0, "moderate": 1, "low": 2}
        match_order = {"strong": 0, "swelling": 1, "location": 2, "additional": 3}
        correlations.sort(key=lambda c: (
            match_order.get(c.get("match_type", "additional"), 4),
            severity_order.get(c["severity"], 3)
        ))

        # Check for unmatched symptoms
        unmatched_symptoms = []
        if has_pain and not any(c.get("match_type") in ["strong", "swelling", "location"] for c in correlations):
            unmatched_symptoms.append(
                f"You reported {pain_type} pain in the {pain_location} region, but our AI "
                f"did not detect any specific findings in that exact area. This could mean "
                f"the condition is not visible on X-ray (e.g., cracked tooth, soft tissue issue) "
                f"or may require a different imaging angle. A clinical examination is recommended."
            )

        return {
            "correlations": correlations,
            "unmatched_symptoms": unmatched_symptoms,
            "total_detections": len(detections),
            "total_correlations": len([c for c in correlations if c.get("match_type") != "additional"]),
        }

    def _get_quadrant(self, detection: dict, img_width: int, img_height: int) -> str:
        """
        Estimate dental quadrant from bounding box position.
        Standard panoramic X-ray orientation:
        - Top half = upper teeth, Bottom half = lower teeth
        - Left side of image = patient's right, Right side = patient's left
        """
        if img_width <= 0 or img_height <= 0:
            # If image dimensions unknown, return generic
            return "unknown"

        cx = detection.get("x", (detection.get("x1", 0) + detection.get("x2", 0)) / 2)
        cy = detection.get("y", (detection.get("y1", 0) + detection.get("y2", 0)) / 2)

        is_upper = cy < img_height / 2
        is_right_side = cx < img_width / 2  # Image left = patient's right

        if is_upper and is_right_side:
            return "upper-right"
        elif is_upper and not is_right_side:
            return "upper-left"
        elif not is_upper and not is_right_side:
            return "lower-left"
        else:
            return "lower-right"

    def _locations_match(self, symptom_location: str, detection_quadrant: str) -> bool:
        """Check if the patient's reported pain location matches the detection quadrant."""
        if not symptom_location or detection_quadrant == "unknown":
            # If no location specified or unknown quadrant, consider it a potential match
            return True

        symptom_loc = symptom_location.lower().replace(" ", "-")

        # Direct match
        if symptom_loc == detection_quadrant:
            return True

        # Partial matches (e.g., "lower" matches both lower-left and lower-right)
        if symptom_loc in ["upper", "top"] and "upper" in detection_quadrant:
            return True
        if symptom_loc in ["lower", "bottom"] and "lower" in detection_quadrant:
            return True
        if symptom_loc in ["left"] and "left" in detection_quadrant:
            return True
        if symptom_loc in ["right"] and "right" in detection_quadrant:
            return True
        if symptom_loc in ["all", "everywhere", "general"]:
            return True

        return False

    def _confidence_label(self, confidence: float) -> str:
        """Return a human-readable confidence label."""
        if confidence >= 0.85:
            return "high confidence"
        elif confidence >= 0.70:
            return "good confidence"
        elif confidence >= 0.50:
            return "moderate confidence"
        else:
            return "low confidence"
