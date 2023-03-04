import os
import shutil
from flask import current_app

'''
    Extracts a 7z file
    return the path to the extracted folder
'''
def extract_dataset(file_path):
    # remove destination folder if exists
    destination_folder = file_path.replace(".7z", "").replace("downloads/", "extract/")
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    
    extract_output = os.path.join(current_app.config["BASE_DIR"], "files/extract/")
    
    cmd = f"/usr/bin/7z x -o'{extract_output}' {file_path} -p'{current_app.config['ZIP_PASSWORD']}'"
    os.system(cmd)
    return destination_folder