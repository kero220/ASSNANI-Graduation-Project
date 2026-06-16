class SymptomAnalyzer:
    """
    Analyzes patient-reported dental symptoms using a weighted scoring system.
    Returns a risk level (low / moderate / high) and recommendation.
    """

    # Scoring weights for each symptom factor
    WEIGHTS = {
        # Pain factors
        "has_pain": 10,
        "pain_spontaneous": 30,
        "pain_on_biting": 25,
        "pain_sensitivity": 15,
        "pain_throbbing": 20,
        "pain_sharp": 15,
        "pain_intensity_high": 25,       # intensity >= 7
        "pain_intensity_moderate": 12,    # intensity 4-6
        "pain_duration_long": 20,         # > 3 days
        "pain_duration_medium": 10,       # 1-3 days

        # Swelling factors
        "has_swelling": 30,
        "swelling_with_fever": 40,
        "swelling_severe": 20,
        "difficulty_opening_mouth": 25,

        # History factors
        "history_trauma": 30,
        "history_previous_root_canal": 15,
        "history_no_recent_visit": 10,    # no visit in 1+ year
        "history_recent_extraction": 10,
        "history_broken_tooth": 25,
    }

    # Risk thresholds
    LOW_THRESHOLD = 25
    HIGH_THRESHOLD = 50

    def analyze(self, symptoms: dict) -> dict:
        """
        Analyze symptoms and return risk assessment.

        Args:
            symptoms: dict with keys matching symptom factors, values are booleans
                      or specific values like:
                - pain_location: str (e.g., "lower-left", "upper-right")
                - pain_type: str (e.g., "throbbing", "sharp", "dull", "sensitivity")
                - pain_intensity: int (1-10)
                - pain_duration: str (e.g., "today", "1-3 days", "3-7 days", "1+ week")
                - pain_triggers: list[str] (e.g., ["hot", "cold", "biting", "spontaneous"])
                - has_swelling: bool
                - swelling_severity: str ("mild", "moderate", "severe")
                - has_fever: bool
                - difficulty_opening: bool
                - has_trauma: bool
                - has_broken_tooth: bool
                - previous_root_canal: bool
                - last_visit: str ("< 6 months", "6-12 months", "1+ year", "never")

        Returns:
            dict with score, risk_level, recommendation, and detailed breakdown
        """
        score = 0
        factors = []

        # --- Input Sanitization ---
        if "pain_intensity" in symptoms:
            symptoms["pain_intensity"] = max(0, min(10, int(symptoms.get("pain_intensity", 0) or 0)))
        for str_key in ("pain_location", "pain_type", "pain_duration", "swelling_severity", "last_visit"):
            if str_key in symptoms and isinstance(symptoms[str_key], str):
                symptoms[str_key] = symptoms[str_key].strip()[:200]

        # --- Pain Assessment ---
        if symptoms.get("has_pain"):
            score += self.WEIGHTS["has_pain"]
            factors.append(("Dental pain reported", self.WEIGHTS["has_pain"]))

            # Pain type scoring
            pain_type = symptoms.get("pain_type", "").lower()
            if pain_type == "throbbing":
                score += self.WEIGHTS["pain_throbbing"]
                factors.append(("Throbbing pain (possible pulpitis)", self.WEIGHTS["pain_throbbing"]))
            elif pain_type == "sharp":
                score += self.WEIGHTS["pain_sharp"]
                factors.append(("Sharp pain", self.WEIGHTS["pain_sharp"]))
            elif pain_type == "sensitivity":
                score += self.WEIGHTS["pain_sensitivity"]
                factors.append(("Temperature sensitivity", self.WEIGHTS["pain_sensitivity"]))

            # Pain triggers
            triggers = symptoms.get("pain_triggers", [])
            if "spontaneous" in triggers:
                score += self.WEIGHTS["pain_spontaneous"]
                factors.append(("Spontaneous pain (possible nerve involvement)", self.WEIGHTS["pain_spontaneous"]))
            if "biting" in triggers:
                score += self.WEIGHTS["pain_on_biting"]
                factors.append(("Pain on biting (possible crack/fracture)", self.WEIGHTS["pain_on_biting"]))
            if "hot" in triggers or "cold" in triggers:
                s = self.WEIGHTS["pain_sensitivity"]
                # Avoid double-counting if already scored as sensitivity type
                if pain_type != "sensitivity":
                    score += s
                    factors.append(("Sensitivity to temperature", s))

            # Pain intensity
            intensity = symptoms.get("pain_intensity", 0)
            if intensity >= 7:
                score += self.WEIGHTS["pain_intensity_high"]
                factors.append((f"High pain intensity ({intensity}/10)", self.WEIGHTS["pain_intensity_high"]))
            elif intensity >= 4:
                score += self.WEIGHTS["pain_intensity_moderate"]
                factors.append((f"Moderate pain intensity ({intensity}/10)", self.WEIGHTS["pain_intensity_moderate"]))

            # Pain duration
            duration = symptoms.get("pain_duration", "").lower()
            if duration in ["3-7 days", "1+ week"]:
                score += self.WEIGHTS["pain_duration_long"]
                factors.append(("Pain persisting > 3 days", self.WEIGHTS["pain_duration_long"]))
            elif duration == "1-3 days":
                score += self.WEIGHTS["pain_duration_medium"]
                factors.append(("Pain for 1-3 days", self.WEIGHTS["pain_duration_medium"]))

        # --- Swelling Assessment ---
        if symptoms.get("has_swelling"):
            score += self.WEIGHTS["has_swelling"]
            factors.append(("Swelling present", self.WEIGHTS["has_swelling"]))

            severity = symptoms.get("swelling_severity", "").lower()
            if severity == "severe":
                score += self.WEIGHTS["swelling_severe"]
                factors.append(("Severe swelling", self.WEIGHTS["swelling_severe"]))

            if symptoms.get("has_fever"):
                score += self.WEIGHTS["swelling_with_fever"]
                factors.append(("Swelling with fever (possible abscess/infection)", self.WEIGHTS["swelling_with_fever"]))

            if symptoms.get("difficulty_opening"):
                score += self.WEIGHTS["difficulty_opening_mouth"]
                factors.append(("Difficulty opening mouth (trismus)", self.WEIGHTS["difficulty_opening_mouth"]))

        # --- History Assessment ---
        if symptoms.get("has_trauma"):
            score += self.WEIGHTS["history_trauma"]
            factors.append(("History of dental trauma", self.WEIGHTS["history_trauma"]))

        if symptoms.get("has_broken_tooth"):
            score += self.WEIGHTS["history_broken_tooth"]
            factors.append(("Broken/chipped tooth", self.WEIGHTS["history_broken_tooth"]))

        if symptoms.get("previous_root_canal"):
            score += self.WEIGHTS["history_previous_root_canal"]
            factors.append(("Previous root canal on affected tooth", self.WEIGHTS["history_previous_root_canal"]))

        last_visit = symptoms.get("last_visit", "").lower()
        if last_visit in ["1+ year", "never"]:
            score += self.WEIGHTS["history_no_recent_visit"]
            factors.append(("No dental visit in over a year", self.WEIGHTS["history_no_recent_visit"]))

        if symptoms.get("recent_extraction"):
            score += self.WEIGHTS["history_recent_extraction"]
            factors.append(("Recent extraction history", self.WEIGHTS["history_recent_extraction"]))

        # --- Determine Risk Level ---
        if score >= self.HIGH_THRESHOLD:
            risk_level = "high"
            recommendation = (
                "Based on your symptoms, an X-ray examination is strongly recommended as soon as possible. "
                "Your symptoms suggest a condition that may require prompt dental attention."
            )
            emoji = "🔴"
        elif score >= self.LOW_THRESHOLD:
            risk_level = "moderate"
            recommendation = (
                "Your symptoms suggest a moderate concern. An X-ray examination is recommended "
                "within the next few days to properly assess the situation."
            )
            emoji = "🟡"
        else:
            risk_level = "low"
            recommendation = (
                "Your symptoms appear to be mild. While an X-ray may not be urgently needed, "
                "consider scheduling a routine dental checkup. In the meantime, maintain good "
                "oral hygiene and monitor for any changes."
            )
            emoji = "🟢"

        # --- Home Care Tips ---
        home_care = self._get_home_care_tips(symptoms, risk_level)

        return {
            "score": score,
            "risk_level": risk_level,
            "risk_emoji": emoji,
            "recommendation": recommendation,
            "factors": factors,
            "home_care": home_care,
            "xray_recommended": risk_level in ["moderate", "high"],
        }

    def _get_home_care_tips(self, symptoms: dict, risk_level: str) -> list:
        """Generate relevant home care tips based on symptoms."""
        tips = []

        if symptoms.get("has_pain"):
            tips.append("Take over-the-counter pain relief (Ibuprofen 400mg) as needed.")
            tips.append("Avoid very hot or cold foods/drinks on the affected side.")
            pain_type = symptoms.get("pain_type", "").lower()
            if pain_type == "sensitivity":
                tips.append("Use a desensitizing toothpaste (e.g., Sensodyne).")

        if symptoms.get("has_swelling"):
            tips.append("Apply a cold compress on the outside of the cheek for 15 minutes.")
            if symptoms.get("has_fever"):
                tips.append("Monitor your temperature. If fever exceeds 38.5°C, seek emergency care.")
            tips.append("Rinse gently with warm salt water (½ tsp salt in a cup of water).")

        if not tips:
            tips.append("Maintain regular brushing twice daily with fluoride toothpaste.")
            tips.append("Floss daily and consider using an antiseptic mouthwash.")

        if risk_level == "high":
            tips.append("⚠️ Do not delay seeking professional dental care.")

        return tips
