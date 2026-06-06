# AI-Powered Emergency Vehicle Priority System

A resume-focused proof-of-concept that uses computer vision and machine learning to analyze uploaded traffic videos, detect vehicles and ambulances, estimate congestion, and recommend emergency vehicle priority actions.

This project simulates traffic priority decisions. It does not control real traffic lights, IoT hardware, GPS systems, or emergency infrastructure.

## Current Status

Phase 2 - Computer Vision Foundation

Completed:

- Streamlit-first architecture selected
- CPU-only development target
- YOLOv8n selected as the baseline detector
- CSV selected for initial historical storage
- Video upload mode selected as the first input workflow
- FastAPI deferred
- OpenCV video loading foundation added
- Frame extraction and basic frame annotation added
- Annotated output video saving added

## Technology Stack

- Python
- Streamlit
- OpenCV
- YOLOv8n through Ultralytics
- Scikit-Learn
- Pandas
- NumPy
- Plotly / Matplotlib
- CSV-based storage
- Pytest

## Project Structure

```text
AI-Emergency-Vehicle-Priority-System/
  backend/
    .gitkeep
  data/
    raw/
      .gitkeep
    processed/
      .gitkeep
    logs/
      .gitkeep
    models/
      .gitkeep
  docs/
    .gitkeep
  frontend/
    .gitkeep
  ml/
    .gitkeep
    cv_pipeline.py
  tests/
    .gitkeep
  .gitignore
  PRD.md
  PROJECT_SETUP.md
  README.md
  requirements.txt
```

## Folder Responsibilities

- `frontend/`: Streamlit dashboard and user-facing app files.
- `ml/`: Computer vision, vehicle counting, congestion prediction, and priority engine modules.
- `data/raw/`: Uploaded or sample input videos.
- `data/processed/`: Processed frames, derived datasets, or intermediate outputs.
- `data/logs/`: CSV detection logs, congestion history, and dashboard history.
- `data/models/`: Downloaded YOLO weights or trained model artifacts.
- `backend/`: Reserved for optional helper services or API work if approved later.
- `docs/`: Architecture notes, screenshots, diagrams, and dataset documentation.
- `tests/`: Unit tests for density classification, counting, prediction, and recommendation logic.

## Setup Instructions

### 1. Create a virtual environment

```powershell
python -m venv .venv
```

### 2. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again.

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify the environment

```powershell
python --version
pip list
```

### 5. Run the Phase 2 OpenCV pipeline

Place a sample traffic video in `data/raw/`, then run:

```powershell
python ml/cv_pipeline.py --input data/raw/sample_traffic.mp4 --output data/processed/annotated_output.mp4
```

To export processed frames as JPG files:

```powershell
python ml/cv_pipeline.py --input data/raw/sample_traffic.mp4 --output data/processed/annotated_output.mp4 --frames-dir data/processed/frames
```

For a quick test on only the first 100 frames:

```powershell
python ml/cv_pipeline.py --input data/raw/sample_traffic.mp4 --output data/processed/annotated_output.mp4 --max-frames 100
```

To display processed frames in an OpenCV window:

```powershell
python ml/cv_pipeline.py --input data/raw/sample_traffic.mp4 --display
```

Press `q` to close the display window early.

### 6. Expected Streamlit command after Phase 7

The Streamlit app will be added in a later phase. Once created, the expected command will be:

```powershell
streamlit run frontend/app.py
```

## Development Phases

1. Project Setup
2. Computer Vision Foundation
3. Vehicle Detection
4. Ambulance Detection
5. Vehicle Counting
6. Congestion Classification
7. Dashboard
8. Machine Learning
9. Priority Engine
10. Analytics
11. Production Readiness

## Phase 2 Testing Steps

1. Install dependencies with `pip install -r requirements.txt`.
2. Add a short video file to `data/raw/`.
3. Run `python ml/cv_pipeline.py --input data/raw/sample_traffic.mp4 --output data/processed/annotated_output.mp4 --max-frames 100`.
4. Confirm the terminal output shows FPS, frame count, dimensions, and processed frame count.
5. Confirm `data/processed/annotated_output.mp4` is created.
6. Run again with `--frames-dir data/processed/frames` and confirm JPG frames are created.
7. Optionally run with `--display` and confirm processed frames appear with frame number, FPS, and timestamp overlays.

## Phase 3 Preview

Phase 3 will add YOLOv8n vehicle detection:

- Load YOLOv8n weights
- Detect cars, buses, trucks, and motorcycles
- Draw detection bounding boxes
- Save detection logs
