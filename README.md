# ASSNANI-Graduation-Project

# AI Components
 
This project integrates three AI-driven features that work together to detect dental conditions from X-ray images, recommend treatments, and guide patients through an interactive diagnostic chatbot.
 
## 1. Dental Disease Detection Model
 
An object detection system that takes one or multiple dental X-ray images and identifies visible dental conditions by drawing bounding boxes around them.
 
- **Dataset:** [Dental X-Ray dataset](https://universe.roboflow.com/gozdes-projects/dental-x-ray-1imfs) from Roboflow Universe.
- **Detected classes:** Cavity, Filling, Impacted, Implant.
- **Confidence filtering:** Any bounding box with a confidence score below 70% is automatically discarded to reduce false positives.
- **Models trained/compared:**
  - YOLOv8
  - YOLOv11
  - YOLOv26
  - Faster R-CNN (FRCNN)
  - RetinaNet
Multiple architectures were trained and evaluated on the same dataset to compare detection accuracy and inference performance, allowing selection of the best-performing model for production use.
 
## 2. AI-Powered Treatment Recommendation
 
This feature builds on the detection model to generate treatment suggestions based on the diagnosed conditions.
 
**Pipeline:**
1. The user uploads one or more dental X-ray images.
2. The images are passed to the Dental Detection Model (Feature 1).
3. The model returns the annotated image(s) (with bounding boxes) and the list of detected findings (classes).
4. The annotated image(s) are sent to a generative AI model via API for clinical interpretation.
5. The selected model returns a treatment recommendation based on the detected findings.
**Supported AI models (selectable):**
- Gemini 2.5 Flash *(default)*
- Gemini 2.0 Flash
- Gemini 1.5 Flash
- Gemini 1.5 Pro
This allows flexibility in balancing speed and recommendation quality depending on the use case.
 
## 3. Decision-Tree Diagnostic Chatbot
 
An interactive chatbot that guides patients through a structured, decision-tree-based conversation to provide an initial diagnosis before confirming it with imaging.
 
**Flow:**
1. The chatbot asks the patient a series of questions with multiple-choice answers.
2. Based on the patient's responses, it traverses a decision tree to estimate the likely dental condition and suggests an initial treatment.
3. The patient is then prompted to upload their dental X-ray image(s).
4. The chatbot sends the image(s) to the Dental Detection Model (Feature 1) and displays the annotated results along with the detected findings.
5. These results are passed to the Treatment Recommendation feature (Feature 2), which generates a final treatment recommendation.
6. The chatbot compiles the findings and recommendations into a downloadable **PDF report** for the patient.
This creates an end-to-end experience: symptom-based triage → image-based confirmation → AI-generated treatment plan → exportable report.
 
## Summary
 
| Feature | Input | Core Technique | Output |
|---|---|---|---|
| Dental Detection | X-ray image(s) | YOLOv8 / YOLOv11 / YOLOv26 / FRCNN / RetinaNet | Annotated image + detected classes |
| Treatment Recommendation | X-ray image(s) | Detection model + Gemini API | Annotated image + treatment advice |
| Diagnostic Chatbot | Patient answers + X-ray image(s) | Decision tree + Detection + Recommendation | Initial diagnosis + final PDF report |
