# YouTubeAndVideoSummarizer
A small Python App to summarize YouTube and local Video.

## Description
This application allows you to generate transcripts and summaries for YouTube videos or local audio/video files. It includes:
- A graphical user interface (GUI) built with PyQt5.
- Integration with `yt-dlp` for metadata retrieval from YouTube.
- Support for transcription using FFmpeg and external tools.

## Requirements

### System Requirements
- Python 3.8 or later
- pip
- Operating System: Should work on Windows, macOS, or Linux if Python 3.x and following packages are installed
- A valid email address to send the results

### Python Dependencies
The following Python packages are required:
- `PyQt5`
- `yt-dlp`
- `ffmpeg-python`

### Additional Tools
- **FFmpeg**: Required for audio/video processing. Install it from [FFmpeg Downloads](https://ffmpeg.org/download.html) and ensure it is accessible in your system PATH.

## Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/MrYoann/YouTubeAndVideoSummarizer.git
cd YouTubeSummarizer
```


### Step 2: Install FFmpeg
Follow the instructions for your operating system:
- **Windows**: Download FFmpeg from [FFmpeg Downloads](https://ffmpeg.org/download.html) and add it to your PATH.
- **Linux/macOS**: Use a package manager (e.g., `sudo apt install ffmpeg` on Ubuntu or homebrew on MacOS).


### Step 3: Install PyQT5
Follow the instruction to install PyQT5 with pip by using the following command : pip install PyQt5
https://pypi.org/project/PyQt5/

### Step 4: Install Whisper
Follow the instruction to install Whisper : https://github.com/openai/whisper
The easiest way is again to use pip install with the following command : pip install -U openai-whisper


## Usage

### Running the Application
1. Ensure all dependencies are installed.
2. Run the main script:
   ```bash
   python youtubesummarizer.py 
   ```
3. Use the configuration button to set email parameters and Whisper PATH
4. The program will then allow you to upload a local video or copy-paste a Youtube URL, select the size and language of the summary and add recipient addresses.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
