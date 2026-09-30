# Court Board Assistant

A local Linux/Ubuntu-compatible court workflow automation system.

## Overview
This system processes a daily `.ods` file downloaded from an existing court system and generates a structured final court board. 

The application strictly adheres to the following pipeline:
`SOURCE ODS` → `IMPORT` → `VALIDATE` → `NORMALIZE` → `STAGE FILTERING` → `STAGE-WISE DATASET` → `FINAL BOARD CLASSIFICATION` → `READY/UNREADY HANDLING` → `BOARD RENDERING` → `ODS + PDF`

## Core Principles
- Original source files are treated as read-only.
- All classifications are exact and based on the "Next Purpose" metadata.
- Unmapped cases are never silently discarded or incorrectly guessed.
- Microsoft Excel dependencies are avoided; full `.ods`/LibreOffice compatibility is guaranteed.

## Development Setup

1. **Prerequisites**
   - Python 3.10 or higher.
   - LibreOffice (for `.ods` rendering/export workflows).

2. **Virtual Environment Setup**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Linux/MacOS
   # OR .venv\Scripts\activate on Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -e .[dev]
   ```

4. **Running Tests**
   ```bash
   pytest
   ```
