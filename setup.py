import os
import sys
import subprocess
import platform

def install_python_packages():
    print("Installing required Python packages...")
    packages = ["PyQt5", "yt-dlp", "requests"]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def install_ffmpeg():
    print("Checking for ffmpeg installation...")
    try:
        subprocess.check_call(["ffmpeg", "-version"])
        print("ffmpeg is already installed.")
    except FileNotFoundError:
        print("ffmpeg is not installed.")
        os_name = platform.system()
        if os_name == "Windows":
            print("Please download ffmpeg from https://ffmpeg.org/download.html and add it to your system PATH.")
        elif os_name == "Darwin":  # macOS
            print("Installing ffmpeg via Homebrew...")
            subprocess.check_call(["brew", "install", "ffmpeg"])
        elif os_name == "Linux":
            print("Installing ffmpeg via apt...")
            subprocess.check_call(["sudo", "apt", "install", "-y", "ffmpeg"])
        else:
            print(f"Unsupported OS: {os_name}. Please install ffmpeg manually.")

def install_whisper_cpp():
    print("Installing whisper.cpp...")
    if not os.path.exists("whisper.cpp"):
        subprocess.check_call(["git", "clone", "https://github.com/ggerganov/whisper.cpp.git"])
    os.chdir("whisper.cpp")
    print("Building whisper.cpp...")
    if platform.system() == "Windows":
        subprocess.check_call(["build.bat"])
    else:
        subprocess.check_call(["bash", "models/download-ggml-model.sh", "large"])
        subprocess.check_call(["make"])
    os.chdir("..")

def download_whisper_model():
    print("Downloading Whisper model...")
    model_dir = os.path.join("whisper.cpp", "models")
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    os.chdir("whisper.cpp/models")
    subprocess.check_call(["bash", "download-ggml-model.sh", "large"])
    os.chdir("../..")

def install_aichat():
    print("Installing aichat...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aichat"])
    except subprocess.CalledProcessError:
        print("Failed to install aichat via pip. Cloning from GitHub...")
        if not os.path.exists("aichat"):
            subprocess.check_call(["git", "clone", "https://github.com/yourusername/aichat.git"])
        os.chdir("aichat")
        subprocess.check_call([sys.executable, "setup.py", "install"])
        os.chdir("..")

def main():
    install_python_packages()
    install_ffmpeg()
    install_whisper_cpp()
    download_whisper_model()
    install_aichat()
    print("All dependencies have been installed successfully.")

if __name__ == "__main__":
    main()
