# Blend File Analyzer

BlendFileAnalyzer is a security and code analysis tool for Blender `.blend` files. It extracts embedded Python scripts from `.blend` files and analyzes them for suspicious or potentially malicious code using local or remote AI models.

## Features

- **Drag-and-drop GUI**: Easily analyze `.blend` files with a user-friendly interface.
- **Script Extraction**: Uses Blender in headless mode to extract all embedded Python scripts from a `.blend` file in a safe way.
- **AI-Powered Security Analysis**: Analyzes extracted scripts for suspicious patterns using a local LLM (Llama.cpp) or LMStudio API.
- **HTML Reports**: Generates detailed HTML reports with security scores and analysis for each script.
- **Cross-platform**: Works on Windows and Linux/macOS.

## Requirements

- [Blender](https://www.blender.org/) (must be installed and accessible in your PATH or specified manually)
- Python 3.11+
- [virtualenv](https://virtualenv.pypa.io/)
- [LMStudio](https://lmstudio.ai/) for LLM analysis

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd BlendFileAnalyzer
```

### 2. Set up the Python environment

On Windows

```bash
setup_env.bat
```

On Linux/macOS

```bash
source setup_env.sh
```

This will create a virtual environment and install all required dependencies, including llama-cpp-python , huggingface_hub , openai , and tkinterdnd2.

### 3. Download Blender and LMStudio

- Ensure Blender is installed and accessible in your system PATH, or use the GUI to select the Blender executable.
- For remote LLM analysis, install and run LMStudio, and provide its API URL and model name in the GUI.

## Usage

### Launch the GUI

On Windows

```bash
run_gui.bat
```

On Linux/macOS

```bash
./run_ui.sh
```

### Analyze a .blend file

1. Open the GUI.
2. (Optional) Select your Blender executable and configure LMStudio API/model if desired.
3. Drag and drop a .blend file onto the window.
4. Wait for the analysis to complete. An HTML report will be generated in the project directory.

## Command-line Usage

You can also run the analysis directly:

```bash
python main.py --filepath <path-to-blend-file> [--blender-exec <path-to-blender>] [--lmstudio-api <url>] [--lmstudio-model <model>]
```

## Output

- Extracted scripts are saved in the extracted_scripts/ directory.
- HTML reports are generated as report__<blendfilename>.html.

## Project Structure

- main.py - Main entry point for script extraction and analysis.
- extract_scripts.py - Script run by Blender to extract embedded scripts.
- gui_analyzer.py - Tkinter-based drag-and-drop GUI.
- setup_env.bat / setup_env.sh - Environment setup scripts.
- run_ui.bat / run_ui.sh - Scripts to launch the GUI.
- .gitignore - Ignores virtual environment, models, and temporary files.

## License

GPLv3 License

-----

Disclaimer:

This tool is intended for security research and educational purposes. Always review the analysis results and use caution when running scripts extracted from unknown .blend files.
