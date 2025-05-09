
def import_scripts_from_blend_file(filepath: str, extracted_scripts_path: str):
    # This function should import the scripts from the blend file
    import bpy
    import os

    # Append all scripts from the blend file.
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        data_to.texts = data_from.texts

    # now operate directly on the loaded data
    for text in data_to.texts:
        if text is None:
            continue

        # Disable auto-execution for the script.
        text.use_module = False

        # Get the text content of the text data block
        text_content = text.as_string()

        # Create a new Python file with the same name as the text data block
        script_filename = text.name + ".py"
        script_filepath = os.path.join(extracted_scripts_path, script_filename)

        # Write the text content to the Python file
        with open(script_filepath, "w") as file:
            file.write(text_content)

    # Close the blend file
    # bpy.ops.wm.save_mainfile(filepath=filepath)
    bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    # Get the arguments passed to the script
    import sys
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]  # get all args after "--"
    filepath = argv[0]
    extracted_scripts_path = argv[1]

    import_scripts_from_blend_file(filepath, extracted_scripts_path)
