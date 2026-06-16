---
title: Assnani Dental AI Chatbot
emoji: 🦷
colorFrom: indigo
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
---

# 🦷 Assnani — Dental AI Chatbot

**Symptom-to-X-ray Correlation Chatbot** for the Assnani Dental Clinic Management System.

## Features

- **Symptom Interview**: Guided conversation about pain, swelling, and dental history
- **Smart Risk Assessment**: AI-powered scoring to determine if an X-ray is needed
- **X-ray Analysis**: Upload dental X-rays for automated detection (cavity, filling, implant, impacted)
- **Symptom Correlation**: Matches patient complaints with AI detection findings
- **Treatment Recommendations**: Expert system suggests treatments and specialist referrals

## How It Works

1. The chatbot asks you about your dental symptoms (pain location, intensity, type, swelling, etc.)
2. Based on a weighted scoring algorithm, it determines if an X-ray examination is recommended
3. If you upload a dental X-ray, it sends it to our YOLOv8-XL detection model
4. The correlation engine matches your symptoms with detected findings
5. You receive a personalized report with explanations and treatment suggestions

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **AI Model**: YOLOv8-XL (dental X-ray detection)
- **Deployment**: Docker on Hugging Face Spaces

## Environment Variables

| Variable | Description |
|---|---|
| `YOLO_API_URL` | URL of the YOLO detection API endpoint |
| `TREAT_API_URL` | URL of the Gemini-powered treatment recommendation API endpoint |
