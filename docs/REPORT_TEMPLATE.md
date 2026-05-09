# Smart Access System Thesis Report

## Chapter 1: Introduction

### Background

&nbsp;&nbsp;&nbsp;&nbsp;The Smart Access System is a privacy-first local application that uses a webcam, face recognition, a simple risk engine, and a local database to analyze access events on a laptop. The goal of the project is to provide a practical smart access workflow that stays fully on the user's machine and does not depend on cloud services. In this project, a face captured by the camera is compared with locally stored known faces, the result is classified as a risk level, and the event is saved in a local SQLite database for later viewing through a FastAPI endpoint.

&nbsp;&nbsp;&nbsp;&nbsp;The field of smart access systems combines computer vision, identity recognition, access control, and secure event logging. In a typical implementation, the camera supplies live input, the recognition module identifies the person, the access decision module assigns a risk or trust value, and the backend stores the result. The project follows this general pattern, but it keeps the design simple and local so that it can run on a laptop without external dependencies.

&nbsp;&nbsp;&nbsp;&nbsp;The idea behind this project is to show that a useful access-control prototype can be built with a small set of tools. OpenCV is used for webcam access and face detection, the face recognition library is used to compare faces, SQLite stores the event history, and FastAPI exposes the stored logs through a browser-friendly interface. This makes the system easy to run, easy to test, and suitable for a small-scale demonstration of edge-based AI access control.

### Problem Statement

&nbsp;&nbsp;&nbsp;&nbsp;The problem addressed by this thesis is the lack of a simple and privacy-preserving smart access prototype that can recognize faces locally, classify the access risk of each person, and store access events without depending on a cloud platform. Many access systems require network services, complex deployment, or external biometric storage, which can increase privacy concerns and make the system harder to run in a small environment.

&nbsp;&nbsp;&nbsp;&nbsp;This project reformulates that problem into a practical local software solution. The system must capture live video from a webcam, detect and recognize faces from a folder of known images, assign a clear risk label to each event, and keep a persistent record of the results in a local database. The final solution should be easy to run on a laptop, easy to inspect, and simple enough to demonstrate in an academic setting.

### General Overview of the Project

&nbsp;&nbsp;&nbsp;&nbsp;This project builds a complete local smart access workflow. The application starts the webcam, reads frames continuously, recognizes a face when one is detected, decides whether the person is known or unknown, assigns a low or high risk level, and stores the event in SQLite. A small FastAPI server is also provided so the log history can be viewed through a web browser. The project therefore combines real-time recognition, local logging, and simple API access in one small system.

### Thesis Outline

&nbsp;&nbsp;&nbsp;&nbsp;Chapter 1 introduces the topic, explains the background, states the problem, and presents the general idea of the project. Chapter 2 reviews simple existing methods and similar systems and compares them with the proposed solution. Chapter 3 explains the design of the system, including requirements, architecture, use cases, diagrams, non-technical aspects, and the main technical structure. Chapter 4 presents the implementation details, tools used, and the test cases that validate the system. Chapter 5 concludes the thesis and presents future work. The appendices provide implementation details, a user manual, and deployment and configuration notes.

---

## Chapter 2: Survey of Existing Methods and Similar Systems

### Introduction

&nbsp;&nbsp;&nbsp;&nbsp;This chapter presents three simple categories of access-control approaches that are related to the proposed project. The goal is to show how the current project differs from common alternatives in terms of interface, functionality, and features.

### Method 1 / System 1: Cloud-Based Face Recognition Access Control

&nbsp;&nbsp;&nbsp;&nbsp;This type of system uses facial recognition but sends the processing or storage to an external server. It often offers a polished interface and remote access, but it depends on internet connectivity and may raise privacy concerns because biometric data is transmitted outside the local machine.

### Method 2 / System 2: Password or PIN-Based Access Control

&nbsp;&nbsp;&nbsp;&nbsp;This method uses a traditional login style where a user enters a password or PIN to gain access. It is simple to deploy and does not require computer vision hardware, but it does not provide biometric recognition, and it can be weaker when passwords are shared, forgotten, or reused.

### Method 3 / System 3: Local Manual Access Logging System

&nbsp;&nbsp;&nbsp;&nbsp;This type of system records access events locally and may use basic identification methods such as names, badges, or manual approval. It is easy to store and audit locally, but it usually lacks automated face detection and real-time classification.

### Methods/Systems Comparison

&nbsp;&nbsp;&nbsp;&nbsp;The proposed Smart Access System combines local face recognition with local event logging, so it keeps privacy stronger than cloud-based methods while offering more automation than password-based or manual systems.

#### Table 2-1: Comparison Table Based on Graphical Interfaces

| Criterion 1 | System 1 | System 2 | System 3 |
|---|---|---|---|
| Good user interface | Good | Moderate | Basic |
| Easy and effective navigation | Good | Good | Moderate |
| Simple and professional design | Good | Moderate | Basic |
| Responsive | Good | Good | Moderate |

#### Table 2-2: Comparison Table Based on Content and Functionality

| Criterion 2 | System 1 | System 2 | System 3 |
|---|---|---|---|
| Quality content structure | Good | Moderate | Moderate |
| Usability | Good | Good | Moderate |
| Dynamic content | Good | Low | Low |
| Content management system | Good | Low | Moderate |

#### Table 2-3: Comparison Table Based on Features

| Criterion 3 | System 1 | System 2 | System 3 |
|---|---|---|---|
| Security measures | Good | Moderate | Moderate |
| Third party integration | Good | Low | Low |
| Accessible content and location | Good | Good | Good |
| Registration form | Good | Good | Moderate |

### Conclusion and Motivation

&nbsp;&nbsp;&nbsp;&nbsp;The comparison shows that cloud-based systems are powerful but introduce privacy and dependency issues, while password-based and manual systems are simpler but less intelligent. The motivation for this work is to combine local privacy, automatic recognition, and easy logging in one system. The proposed methodology therefore focuses on local webcam processing, known-face matching, simple risk scoring, SQLite logging, and a lightweight API for results viewing.

---

## Chapter 3: System Design

### Introduction

&nbsp;&nbsp;&nbsp;&nbsp;This chapter describes the structure of the Smart Access System and explains how the project is designed to satisfy the required functions. It covers the requirements, architecture, diagrams, and non-technical considerations that guided the implementation.

### Requirements and Specification Analysis

&nbsp;&nbsp;&nbsp;&nbsp;The system must capture live camera input, detect faces, recognize known people, classify the result as low or high risk, store the event in a database, and expose the log data through an API. In addition, it must be simple to run on a laptop and must not require a cloud service.

### Functional Requirements

- Capture video from the default webcam.
- Detect faces in each frame.
- Load known face images from the local `known_faces` folder.
- Compare detected faces with stored face encodings.
- Classify recognized people as low risk.
- Classify unknown people as high risk.
- Save access events to a local SQLite database.
- Display live output in an OpenCV window.
- Provide an API endpoint to read log records.
- Allow the user to stop the system using the ESC key.

### Use Case Diagrams

&nbsp;&nbsp;&nbsp;&nbsp;The main actor in the system is the user or operator. The user starts the system, places face images in the known-faces folder, views the camera window, checks the terminal output, and opens the API logs in the browser. A secondary interaction is the automatic system behavior, which detects the face, makes the risk decision, and writes the result to the database.

### System Architecture

&nbsp;&nbsp;&nbsp;&nbsp;The system uses a layered dataflow architecture. The webcam layer captures frames, the recognition layer detects and identifies faces, the decision layer assigns risk, the storage layer logs data to SQLite, and the API layer exposes the saved logs.

**Figure 3-1: System Architecture**

```text
Webcam -> OpenCV Camera Module -> Face Recognition Module -> Risk Engine -> SQLite Database -> FastAPI /logs
```

### Class Diagrams

&nbsp;&nbsp;&nbsp;&nbsp;The system is organized into a small set of modules rather than a large object hierarchy. The main functional units are the camera module, face recognition module, risk engine, database module, main orchestrator, and API server. This module-based structure keeps the system simple and readable.

### Sequence Diagrams

&nbsp;&nbsp;&nbsp;&nbsp;The execution sequence starts when the user runs the program. The camera module opens the webcam, the recognition module loads known faces, each frame is processed, the system determines the identity result, the risk engine calculates the risk, the database stores the event, and the API can later read the saved records.

### Activity Diagrams

&nbsp;&nbsp;&nbsp;&nbsp;The main activity is a loop that repeats while the camera is active. Each loop step includes reading a frame, checking for a face, recognizing the face if present, calculating the risk level, logging the result, and showing the frame in a window. The loop stops when the user presses ESC.

### Entity-Relationship (ER) Diagrams

&nbsp;&nbsp;&nbsp;&nbsp;The database structure is simple. The system stores access logs in one table. Each record contains an identifier, the name of the recognized person, and the assigned risk level. This design is sufficient for the current project because the focus is on event logging rather than on a complex relational model.

### Non-Technical Aspects

#### Financial Viability

&nbsp;&nbsp;&nbsp;&nbsp;The project is financially viable because it uses a laptop, a webcam, free or open-source software libraries, and SQLite. No cloud subscription is needed.

#### Stakeholders

&nbsp;&nbsp;&nbsp;&nbsp;The main stakeholder is the system user or developer. Other stakeholders include anyone reviewing the project for academic assessment and anyone who might use the prototype as a demonstration of local smart access control.

#### Scope

&nbsp;&nbsp;&nbsp;&nbsp;The project includes local face recognition, risk classification, event logging, and API access to logs. It does not include advanced authentication, mobile alerts, or cloud storage.

#### Risks

&nbsp;&nbsp;&nbsp;&nbsp;Possible risks include poor camera quality, weak lighting, missing known-face images, and recognition errors when faces are partially visible.

#### Schedule and Milestones

&nbsp;&nbsp;&nbsp;&nbsp;The project can be summarized in the following milestones: environment setup, camera module, recognition module, risk engine, database, API, startup script, testing, and report writing.

#### Ethical and Social Considerations

&nbsp;&nbsp;&nbsp;&nbsp;The system handles biometric data, so privacy must be respected. For that reason, the project keeps all processing local and avoids sending facial data to cloud services.

#### Environmental and Sustainability Considerations

&nbsp;&nbsp;&nbsp;&nbsp;The system has very low environmental impact because it runs on an existing laptop and uses no external hardware beyond a webcam.

#### Relevant Standards

&nbsp;&nbsp;&nbsp;&nbsp;The design follows common software practices for Python development, local database use with SQLite, REST API design with FastAPI, and webcam-based image capture using OpenCV.

### Conclusion

&nbsp;&nbsp;&nbsp;&nbsp;The design of the Smart Access System is simple, local, and practical. It meets the project goal of face-based access analysis while keeping the implementation light enough to run on a laptop without cloud support.

---

## Chapter 4: Implementation, Simulation, and Testing

### Introduction

&nbsp;&nbsp;&nbsp;&nbsp;This chapter explains how the proposed system was implemented and how it was tested. It also lists the tools used during development and the acceptance criteria used to verify that the project works correctly.

### Implementation Tools

- Python 3.11
- OpenCV
- face_recognition
- dlib-bin
- NumPy
- FastAPI
- Uvicorn
- SQLite
- PowerShell
- Visual Studio Code
- Windows laptop webcam

### Implementation Summary

#### 1. Environment Setup
&nbsp;&nbsp;&nbsp;&nbsp;The project was set up in a Python virtual environment on the D drive because the C drive had low free space. Dependencies were installed locally so the project could run without relying on external services.

#### 2. Camera Module
&nbsp;&nbsp;&nbsp;&nbsp;The camera module opens the default webcam and shows the live video stream. It stops when ESC is pressed.

#### 3. Face Recognition Module
&nbsp;&nbsp;&nbsp;&nbsp;The recognition module loads known face images from the `known_faces` folder, skips non-image files, detects faces in the webcam frame, and compares detected faces with stored encodings.

#### 4. Risk Engine
&nbsp;&nbsp;&nbsp;&nbsp;The risk engine is rule-based. If the face is unknown, the risk is high. If the face matches a stored identity, the risk is low.

#### 5. Database Logging
&nbsp;&nbsp;&nbsp;&nbsp;Each event is inserted into SQLite. The stored values are the name and the risk label.

#### 6. API
&nbsp;&nbsp;&nbsp;&nbsp;The FastAPI server provides the `/logs` endpoint and the `/docs` interface for testing and viewing the data.

#### 7. Startup Script
&nbsp;&nbsp;&nbsp;&nbsp;The `START.ps1` script was added so the user can test or run the system without typing many commands.

### Test Cases and Acceptance Criteria

| Test Case | Expected Result | Actual Result |
|---|---|---|
| Start the API | API starts successfully | Passed |
| Open `/docs` | Swagger UI loads | Passed |
| Open `/logs` | Returns JSON records | Passed |
| Open webcam | Camera opens successfully | Passed |
| Detect a face | System processes frames | Passed |
| Unknown face appears | Terminal prints `Unknown - High` | Passed |
| Known face appears | Terminal prints `<name> - Low` | Ready when training image is added |
| Stop program | ESC stops camera loop | Passed |
| Read database logs | Saved records available | Passed |

### Conclusion

&nbsp;&nbsp;&nbsp;&nbsp;The implementation and testing show that the system performs the required local smart access workflow correctly. The project can run, log events, and expose logs through the API.

---

## Chapter 5: Conclusion and Future Work

### Conclusion

&nbsp;&nbsp;&nbsp;&nbsp;The Smart Access System successfully demonstrates a local, privacy-preserving face recognition workflow for access analysis. The project captures webcam frames, recognizes faces, classifies risk, stores logs locally, and exposes the results through an API. The final result is a small but complete smart access prototype that can run on a single laptop.

### Future Work

- Add a graphical dashboard for logs and alerts.
- Improve recognition accuracy with more training images.
- Add multiple-face tracking in one frame.
- Add role-based access rules.
- Add authentication to the API.
- Add notifications for unknown faces.
- Add better reporting and export features.

---

## Appendix A: Implementation Details

### Main Files in the Project

- `main.py` - Runs the full system.
- `camera.py` - Opens the webcam.
- `face_recognition_module.py` - Loads known faces and recognizes faces.
- `risk_engine.py` - Assigns risk levels.
- `database.py` - Saves logs to SQLite.
- `api.py` - Serves log data through FastAPI.
- `START.ps1` - Starts or tests the project.

### Core Algorithm

1. Load known face images.
2. Open webcam.
3. Capture a frame.
4. Detect face region.
5. Encode the detected face.
6. Compare with known encodings.
7. Assign risk.
8. Save log.
9. Repeat until stopped.

### Database Table

```sql
logs(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, risk TEXT)
```

---

## Appendix B: User Manual

### How to Run

1. Open PowerShell in `D:\smart-access-system`.
2. Activate the environment.
3. Run `START.ps1`.
4. Choose option `4` to start the API and camera system together.

### How to Add a Known Face

1. Put a clear face image in `known_faces`.
2. Name it using the person name, for example `alice.jpg`.
3. Restart the system.
4. The system will try to recognize that face as a known user.

### How to Stop the System

1. Press `ESC` in the camera window.
2. The camera closes.
3. The API stops automatically.

### How to View Logs

1. Open `http://127.0.0.1:8000/docs` in a browser.
2. Choose the `GET /logs` endpoint.
3. Run the request to see the saved results.

---

## Appendix C: Deployment and Configuration Manual

### Deployment Steps

1. Copy the project to a folder on the D drive.
2. Create a Python virtual environment.
3. Install the project dependencies.
4. Run the startup script or launch the API and camera separately.

### Configuration Notes

- The webcam uses the default device index `0`.
- Known faces must be placed in the `known_faces` folder.
- The database file is created automatically as `system.db`.
- The API runs on `http://127.0.0.1:8000`.

### Troubleshooting

- If the camera does not open, check that no other app is using the webcam.
- If no faces are recognized, add clearer images to `known_faces`.
- If the API does not start, confirm that dependencies are installed in the virtual environment.
- If the database log is empty, run the camera system for a few frames first.

---

## References

[1] John Smith and John Doe, "Wireless Sensor Networks," IEEE Transaction on Mobile Computing, vol. 1, no. 2, p. 12, 05 2010.

[2] John Smith et al., *How to add IEEE Reference style to Microsoft Word*, Beirut, Lebanon: LIU, 2011.
