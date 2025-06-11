import argparse
import os
import sys
import pathlib
import subprocess
import glob
import webbrowser # For opening the HTML report in a web browser	
import html # For escaping HTML content
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from multiprocessing import cpu_count
import re


# --- Configuration ---
# Set the path to the blender executable,
# by default will use 'blender' in the PATH.
# If you have blender installed in a different location,
# you can set this variable to the path of the blender executable.
BLENDER_EXECUTABLE = "blender"
# --- End Configuration ---


def import_scripts_from_blend_file(filepath: str, extracted_scripts_path: pathlib.Path, blender_executable: str = BLENDER_EXECUTABLE):
    # This function should import the scripts from the blend file
    # will extract them from the blend file, store them in temporal directory and return the path
    # Will run a blender instance with the default scene and run the 'extract_scripts.py' script with the target filepath as argument.
    # The script will look-up and append all scripts from the target blend file in the filepath argument.
    # The extracted scripts will be stored in a temporal directory and the path to the directory will be returned.
    # The blender instance will be terminated after the script is finished.

    # Path to the extract_scripts.py (assuming it's in the same directory as main.py)
    extractor_script_path = pathlib.Path(__file__).parent / "extract_scripts.py"
    if not extractor_script_path.is_file():
        print(f"Error: extract_scripts.py not found at {extractor_script_path}")
        # If directory is empty, delete it.
        if not os.listdir(extracted_scripts_path):
            extracted_scripts_path.rmdir()
        return None


    # Run the blender instance with the 'extract_scripts.py' script.
    # Disable auto script execution to prevent running potentially harmful code.
    print(f"Running Blender to extract scripts from: {filepath}")
    process = subprocess.run(
        [
            blender_executable,
            "--background",
            "--factory-startup",
            "--disable-autoexec",
            "--python", str(extractor_script_path),
            "--",
            filepath,
            str(extracted_scripts_path),
        ],
        capture_output=True, text=True
    )

    if process.returncode != 0:
        print(f"Error during script extraction with Blender:")
        print(f"Stdout: {process.stdout}")
        print(f"Stderr: {process.stderr}")
        if not os.listdir(extracted_scripts_path): # Cleanup if empty
            extracted_scripts_path.rmdir()
        return None
    else:
        print("Blender script extraction completed.")
        if process.stdout: print(f"Blender stdout:\n{process.stdout}")
        if process.stderr: print(f"Blender stderr:\n{process.stderr}")


def analyze_scripts(scripts_path: pathlib.Path, lmstudio_api_base: str = None, lmstudio_model: str = None):
    print("Starting scripts analysis!", scripts_path)

    python_files = glob.glob(os.path.join(str(scripts_path), "*.py"))

    if not python_files:
        print(f"No Python files found in {scripts_path}")
        return []

    use_lmstudio = lmstudio_api_base is not None

    if use_lmstudio:
        print(f"Using LMStudio API at {lmstudio_api_base}")
        from openai import OpenAI
        client = OpenAI(
            base_url=lmstudio_api_base,
            api_key="lm-studio"  # LMStudio ignores the key, but it must be set
        )
        model_name = lmstudio_model  # You may want to make this configurable
    else:
        print("Downloading model...")
        model_name = "unsloth/Qwen3-4B-GGUF"
        model_file = "Qwen3-4B-Q4_K_M.gguf"
        model_path = pathlib.Path("models") / model_file
        if not model_path.exists():
            print("Downloading model...")
            model_path = hf_hub_download(model_name, filename=model_file, local_dir="models")
        else:
            print("Model already exists, skipping download.")
        print("Model downloaded.")
        print("Loading model...")
        llm = Llama(
            model_path=str(model_path),
            n_ctx=4000,
            n_threads=cpu_count(),
            n_gpu_layers=20
        )
        print("Model loaded.")

    all_analysis_results = []
    system_prompt = (
        "You are a Python security expert. Analyze and deep-research the following Blender Python script for any suspicious or potentially malicious code embedded on it. "
        "You must follow the following format: <Score>score value goes here</Score> <Analysis>all analysis information here</Analysis>\n"
        "Do NOT output multiple <Score></Score> or <Analysis></Analysis> tags, even if you find multiple issues—summarize everything in a single pair of tags.\n\n"
        "The guidelines for the <Score> section are below: \n"
        "- A single integer value between 0 and 10, where 10 is most secure and 0 is most suspicious.\n"
        "- The more suspicious or risky patterns it has, the lower the score should be. Be serious with the score as it should determine if the script is safe or not to execute.\n\n"
        "The guidelines for the <Analysis> section are below: \n"
        "- A summary of any suspicious or malicious patterns, or a statement if none are found. Avoid recommendations.\n"
        "- You should use html tags for formatting, for example: <h4> for headings, <pre> for code blocks, <span class='code-inline'> for inline code blocks, <ul> for lists, <li> for list items, <div> for sections. Avoid markdown like format.\n"
        "- Focus only on what is truly suspicious or risky like obfuscated code, http communications, subprocess, os.system, codified strings, and other suspicious patterns or libraries.\n\n"
        "Do NOT include recommendations or extra sections. Be brief and to the point. Respect the formatting guidelines.\n\n "
    )

    for python_file_path_str in python_files:
        python_file_path = pathlib.Path(python_file_path_str)
        script_name = python_file_path.name
        print(f"\nAnalyzing script: {script_name}...")
        try:
            with open(python_file_path, "r", encoding='utf-8') as file:
                script_content = file.read()
        except Exception as e:
            print(f"Error reading script {script_name}: {e}")
            all_analysis_results.append({
                "script_name": script_name,
                "script_content": f"Error reading file: {e}",
                "ai_analysis_html": "<h3>Error</h3><p>Could not read script content.</p>"
            })
            continue

        try:
            if use_lmstudio:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": script_content}
                    ],
                    max_tokens=-1,
                    temperature=0.7,
                )
                ai_raw_response = response.choices[0].message.content
            else:
                full_prompt = f"System: {system_prompt}\nUser: {script_content}\nAssistant:"
                ai_raw_response = llm(full_prompt, max_tokens=100)
            
            # Debugging: Print the raw AI response
            print(f"AI Response for {script_name}:\n{ai_raw_response}")

            # Use regex to extract <Score> and <Analysis> tags
            score_match = re.search(r"<Score>(.*?)</Score>", ai_raw_response, re.DOTALL | re.IGNORECASE)
            analysis_match = re.search(r"<Analysis>(.*?)</Analysis>", ai_raw_response, re.DOTALL | re.IGNORECASE)
            if not analysis_match:
                analysis_match = re.search(r"<Analysis>(.*?)", ai_raw_response, re.DOTALL | re.IGNORECASE)

            report_html = "<div>"
            if score_match:
                report_html += "<h3>Security Score:</h3><pre>" + html.escape(score_match.group(1).strip()) + "</pre>"
            if analysis_match:
                report_html += "<h3>Analysis:</h3>\n" + analysis_match.group(1) + "\n"
            if not score_match and not analysis_match:
                report_html += "<h3>AI Analysis Not Fully Parsed</h3><pre>" + html.escape(ai_raw_response) + "</pre>"
            report_html += "</div>"

            print(f"AI Response for {script_name} processed.")
            all_analysis_results.append({
                "script_name": script_name,
                "script_content_escaped": html.escape(script_content),
                "ai_analysis_html": report_html
            })
        except Exception as e:
            print(f"Error during AI analysis for {script_name}: {e}")
            all_analysis_results.append({
                "script_name": script_name,
                "script_content_escaped": html.escape(script_content),
                "ai_analysis_html": f"<h3>Error during AI analysis</h3><p>{html.escape(str(e))}</p>"
            })
            
    return all_analysis_results

def generate_html_report(analysis_results, blend_filename, report_filepath: str):
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Script Analysis Report: {html.escape(blend_filename)}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f4f4f9; color: #333; }}
        .header {{
            width: 100%;
            background-color: #222a35;
            color: #fff;
            padding: 12px 0 10px 30px;
            font-size: .9em;
            font-weight: 600;
            letter-spacing: 1px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
            position: fixed;
            height: 1rem;
            z-index: 2;
        }}
        .code-inline {{
            font-family: 'Courier New', Courier, monospace;
            background-color: #282c34;
            color: #abb2bf;
            padding: 2px 4px;
            border-radius: 4px;
            font-size: 0.9em;
            white-space: nowrap;
        }}
        .content-wrapper {{
            display: flex;
            flex: 1 1 auto;
            height: 100%;
            padding-top: 4rem;
        }}
        .sidebar {{
            width: 240px;
            background-color: #333a40;
            color: #e0e0e0;
            padding: 32px 20px;
            overflow-y: auto;
            border-right: 1px solid #444;
            position: fixed;
            height: calc(100vh - 2rem);
            top: 2rem;
            z-index: 1;
        }}
        .sidebar h3 {{ margin-top: 0; font-size: 1.2em; border-bottom: 1px solid #555; padding-bottom: 10px; }}
        .sidebar ul {{ list-style-type: none; padding: 0; }}
        .sidebar li a {{ color: #b0c4de; text-decoration: none; display: block; padding: 10px 15px; border-radius: 4px; margin-bottom: 5px; transition: background-color 0.3s, color 0.3s; font-size: 1em; }}
        .sidebar li a:hover, .sidebar li a.active {{ background-color: #4a525a; color: #ffffff; }}
        .main-content {{
            width: 100%; flex-grow: 1; padding: 1rem 2rem; overflow-y: auto; background-color: #ffffff;
            margin-left: 300px;
        }}
        .script-analysis-container {{ display: none; }} /* Hidden by default */
        .script-analysis-container.active {{ display: block; }}
        .script-analysis-container h3 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        .code-view-container {{ display: flex; gap: 20px; margin-top: 15px; }}
        .code-box {{ flex: 1; background-color: #282c34; color: #abb2bf; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', Courier, monospace; font-size: 0.9em; line-height: 1.5; }}
        .code-box h4 {{ margin-top: 0; color: #61afef; border-bottom: 1px solid #454c55; padding-bottom: 8px; }}
        .ai-analysis-box {{ flex: 1; background-color: #fdfdfd; border: 1px solid #e0e0e0; padding: 15px; border-radius: 5px; }}
        .ai-analysis-box h3, .ai-analysis-box h4 {{ color: #333; }}
        .ai-analysis-box pre {{ white-space: pre-wrap; word-wrap: break-word; background-color: #f9f9f9; padding: 10px; border-radius: 4px; border: 1px solid #eee; }}
        #placeholder {{ text-align: center; color: #777; margin-top: 50px; font-size: 1.2em; }}
    </style>
</head>
<body>
    <div class="header">{html.escape(blend_filename)}</div>
    <div class="content-wrapper">
        <aside class="sidebar">
            <h3>Analyzed Scripts:</h3>
            <ul id="script-list">
    """
    for i, result in enumerate(analysis_results):
        script_id = f"script-{i}"
        html_content += f'<li><a href="#" onclick="showAnalysis(\'{script_id}\'); return false;">{html.escape(result["script_name"])}</a></li>'
    html_content += """
            </ul>
        </aside>
        <main class="main-content">
            <div id="placeholder">Select a script from the sidebar to view its analysis.</div>
    """

    for i, result in enumerate(analysis_results):
        script_id = f"script-{i}"
        html_content += f"""
            <div id="{script_id}" class="script-analysis-container">
                <div class="code-view-container">
                    <div class="code-box">
                        <h4>Script: {html.escape(result["script_name"])}</h4>
                        <pre>{result["script_content_escaped"]}</pre>
                    </div>
                    <div class="ai-analysis-box">
                        {result["ai_analysis_html"]}
                    </div>
                </div>
            </div>
        """

    html_content += """
        </main>
    </div>
    <script>
        function showAnalysis(id) {
            var containers = document.getElementsByClassName('script-analysis-container');
            for (var i = 0; i < containers.length; i++) {
                containers[i].classList.remove('active');
            }
            var el = document.getElementById(id);
            if (el) {
                el.classList.add('active');
                document.getElementById('placeholder').style.display = 'none';
            }
        }
    </script>
</body>
</html>
    """
    try:
        with open(report_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Report generated at: {report_filepath}")
        webbrowser.open(f"file://{report_filepath}")
    except Exception as e:
        print(f"Error generating HTML page: {e}")

def generate_no_scripts_html(blend_filename, report_filepath: str):
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>No Scripts Found: {html.escape(blend_filename)}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f4f9; color: #333; text-align: center; }}
        .container {{ background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); display: inline-block; }}
        h1 {{ color: #2c3e50; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>No Scripts Found</h1>
        <p>No Python scripts were found embedded within the Blender file: <strong>{html.escape(blend_filename)}</strong>.</p>
        <p>Therefore, no security analysis could be performed on its internal scripts.</p>
    </div>
</body>
</html>
    """
    try:
        with open(report_filepath, "w", encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML 'no scripts' page generated: {report_filepath}")
        webbrowser.open(f"file://{report_filepath}")
    except Exception as e:
        print(f"Error generating or opening 'no scripts' HTML page: {e}")


def main(blend_filepath: str, blender_executable: str, lmstudio_api: str, lmstudio_model: str): # Renamed main to main_logic and accept filepath
    # Create a temporal directory to store the extracted scripts.
    scripts_dir_path = pathlib.Path(__file__).parent / "extracted_scripts" / pathlib.Path(blend_filepath).stem
    scripts_dir_path.mkdir(exist_ok=True, parents=True)

    # Import the scripts from the blend file.
    import_scripts_from_blend_file(blend_filepath, scripts_dir_path, blender_executable)

    # Report html filepath.
    report_filepath = str(pathlib.Path(scripts_dir_path).parent / f"report__{pathlib.Path(blend_filepath).stem}.html")
    
    blend_filename = os.path.basename(filepath)

    # If directory is empty, delete it.
    if not os.listdir(scripts_dir_path):
        print("No scripts found in the blend file or extraction failed.")
        generate_no_scripts_html(blend_filename, report_filepath)
        # Clean up empty extracted_scripts_path if it exists
        if scripts_dir_path and scripts_dir_path.exists():
            # Check if the directory itself exists before trying to remove it,
            # as it might have been removed if extraction failed early.
            if scripts_dir_path.exists():
                scripts_dir_path.rmdir()
        return

    # Analyze the scripts.
    analysis_results = analyze_scripts(scripts_dir_path, lmstudio_api, lmstudio_model)

    if not analysis_results:
        print("Script analysis did not produce any results (possibly due to model loading error or no .py files).")
        # Even if scripts were extracted but analysis failed or found no .py files, show a specific message.
        generate_no_scripts_html(blend_filename, report_filepath) # Or a more specific error HTML
    else:
        generate_html_report(analysis_results, blend_filename, report_filepath)

    # Optional: Clean up the extracted_scripts_path directory after analysis
    # import shutil
    # try:
    #     shutil.rmtree(scripts_dir_path)
    #     print(f"Cleaned up extracted scripts directory: {scripts_dir_path}")
    # except Exception as e:
    #     print(f"Error cleaning up directory {scripts_dir_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a .blend file and interact with an AI model.")
    parser.add_argument("--filepath", type=str, required=True, help="Path to the .blend file to analyze.")
    parser.add_argument("--blender-exec", type=str, default=BLENDER_EXECUTABLE, help="Path to the Blender executable to use.")
    parser.add_argument("--lmstudio-api", type=str, default=None, help="LMStudio API base URL (e.g. http://localhost:1234/v1)")
    parser.add_argument("--lmstudio-model", type=str, default="TheModelNameYouUseInLMStudio", help="LMStudio model name (if using LMStudio API)")
    args = parser.parse_args()

    filepath: str = args.filepath
    blender_executable: str = args.blender_exec
    lmstudio_api_base: str = args.lmstudio_api
    lmstudio_model: str = args.lmstudio_model

    # Validate the filepath
    if not os.path.isfile(filepath):
        print(f"Error: The file '{filepath}' does not exist.")
        sys.exit(1)

    if not filepath.lower().endswith(".blend"):
        print(f"Error: The file '{filepath}' is not a .blend file.")
        sys.exit(1)

    main(filepath, blender_executable, lmstudio_api_base, lmstudio_model)
