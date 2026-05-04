# Senior Project Report Template

## Introduction
This project presents a Privacy-First Edge AI Smart Access System that performs face-based access analysis and risk classification locally on a laptop.

## Problem
Traditional cloud-based smart access systems can expose sensitive biometric data and increase privacy risks. A local-first architecture is needed.

## Solution
The system uses webcam input, local face recognition, a lightweight risk engine, SQLite logging, and a local FastAPI backend to avoid cloud dependency.

## System Architecture
- Camera Module captures frames
- Face Recognition Module detects and identifies faces
- Risk Engine assigns risk levels
- Database stores events
- API layer exposes logs for analysis/testing

## Implementation
1. Environment setup with Python dependencies
2. Camera capture pipeline with OpenCV
3. Face matching with `face_recognition`
4. Rule-based risk scoring
5. SQLite event logging
6. FastAPI `/logs` endpoint
7. Optional Docker packaging

## UML Diagrams
Reference and include the diagrams from `docs/UML_DIAGRAMS.md`.

## Results
- Real-time local recognition pipeline implemented
- Event risk scoring operational
- Logs persisted and retrievable via API
- System validated using Postman endpoint testing
