import sys
import threading
import os
import json
import subprocess
import time
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QMessageBox, QFileDialog
)


class LogHandler(QObject):
    log_signal = pyqtSignal(str, bool)


def process_input(input_path, is_file, summary_type, language, log_handler):
    try:
        start_time = time.time()  # Start the timer
        log_handler.log_signal.emit("Starting computation...\n", False)

        # Loading settings
        with open("settings.json", "r") as f:
            settings = json.load(f)

        # Path to whisper
        whisper_path = settings.get("whisper_path", "")
        model_path = os.path.join(whisper_path, "models/ggml-large-v3.bin")
        smtp_server = settings.get("smtp_server", "")
        port = settings.get("port", "")
        password = settings.get("password", "")

        # Collecting email in CC
        base_email = settings.get("email", "")
        additional_emails = main_window.input_email.text().strip()
        recipient_emails = [base_email]
        if additional_emails:
            recipient_emails.extend([email.strip() for email in additional_emails.split(",")])

        # Default metadata if not available
        video_title = "Unknown Title"
        channel_name = "Unknown Channel"
        subject = ""
        body = ""
        transcript = ""
        wav_path = None

        if is_file:
            log_handler.log_signal.emit(f"Processing local file: {input_path}\n", False)
            wav_path = input_path
            if not input_path.lower().endswith(".wav"):
                wav_path = convert_to_wav(input_path, log_handler)
                if not wav_path:
                    log_handler.log_signal.emit("Error: Failed to convert file to WAV.\n", True)
                    return

            transcript_command = f'{os.path.join(whisper_path, "main")} -f "{wav_path}" -m "{model_path}" -l {language.lower()}'
            transcript_result = subprocess.run(transcript_command, shell=True, capture_output=True, text=True)
            if transcript_result.returncode != 0:
                log_handler.log_signal.emit(f"Error during transcription: {transcript_result.stderr}\n", True)
                return

            transcript = transcript_result.stdout.strip()
            video_title = os.path.basename(input_path)
            subject = f"Transcript of your video {video_title}"

        else:
            log_handler.log_signal.emit("Processing YouTube video...\n", False)

            metadata_command = f'yt-dlp -J "{input_path}"'
            metadata_result = subprocess.run(metadata_command, shell=True, capture_output=True, text=True)
            if metadata_result.returncode != 0:
                log_handler.log_signal.emit(f"Error extracting metadata: {metadata_result.stderr}\n", True)
                return

            metadata_json = json.loads(metadata_result.stdout.strip())
            video_title = metadata_json.get("title", "Unknown Title")
            channel_name = metadata_json.get("uploader", "Unknown Channel")
            log_handler.log_signal.emit(f"Metadata retrieved: {video_title} ({channel_name})\n", False)

            transcript_command = f'yt2doc --video "{input_path}"'
            transcript_result = subprocess.run(transcript_command, shell=True, capture_output=True, text=True)
            if transcript_result.returncode != 0:
                log_handler.log_signal.emit(f"Error during transcription: {transcript_result.stderr}\n", True)
                return

            transcript = transcript_result.stdout.strip()
            subject = f"Summary of your video {video_title} - {channel_name}"

        log_handler.log_signal.emit(f"Transcript successfully retrieved ({len(transcript)} characters).\n", False)

        if summary_type == "Full Transcript":
            output_file = os.path.join(os.path.expanduser("~"), "transcript.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(transcript)

            body = "Please find the full transcript attached.\n"
            if not is_file:
                body += f"The video is available here: {input_path}\n"

            email_result = send_email(
                to_emails=recipient_emails,
                smtp_server=smtp_server,
                port=port,
                password=password,
                subject=subject,
                body=body,
                attachment_path=output_file,
            )
            log_handler.log_signal.emit(email_result, False)
            os.remove(output_file)

        else:  # Create summaries with aichat
            log_handler.log_signal.emit("Generating summary...\n", False)
            summary_command = f'echo "{transcript}" | aichat summarize --language {language.lower()} --length {"short" if summary_type == "Brief Summary" else "1500"}'
            summary_result = subprocess.run(summary_command, shell=True, capture_output=True, text=True)
            if summary_result.returncode != 0:
                log_handler.log_signal.emit(f"Error generating summary: {summary_result.stderr}\n", True)
                return

            summary = summary_result.stdout.strip()
            body = f"Hello,\n\nHere is the summary of your video:\n\n{summary}\n"
            if not is_file:
                body += f"\nThe video is available here: {input_path}"

            email_result = send_email(
                to_emails=recipient_emails,
                smtp_server=smtp_server,
                port=port,
                password=password,
                subject=subject,
                body=body,
            )
            log_handler.log_signal.emit(email_result, False)

        # Delete WAV
        if wav_path and wav_path != input_path:
            try:
                os.remove(wav_path)
                log_handler.log_signal.emit(f"Temporary WAV file deleted: {wav_path}\n", False)
            except Exception as e:
                log_handler.log_signal.emit(f"Error deleting WAV file: {str(e)}\n", True)

        # Calculate total time
        end_time = time.time()
        elapsed_time = end_time - start_time
        log_handler.log_signal.emit(f"Total processing time: {elapsed_time:.2f} seconds\n", False)

        log_handler.log_signal.emit("-" * 50, False)

    except Exception as e:
        log_handler.log_signal.emit(f"Error: {str(e)}\n", True)


def convert_to_wav(input_path, log_handler):
    try:
        log_handler.log_signal.emit(f"Converting file {input_path} to WAV...\n", False)
        output_path = os.path.splitext(input_path)[0] + ".wav"
        # ffmpeg command to convert video to WAV audio track
        ffmpeg_command = f'ffmpeg -i "{input_path}" -ar 16000 -ac 1 -c:a pcm_s16le "{output_path}"'
        subprocess.run(ffmpeg_command, shell=True, check=True)
        log_handler.log_signal.emit(f"File successfully converted to WAV: {output_path}\n", False)
        return output_path
    except Exception as e:
        log_handler.log_signal.emit(f"Unexpected error during conversion: {str(e)}\n", True)
        return None

def send_email(to_emails, smtp_server, port, password, subject, body, attachment_path=None):
    from smtplib import SMTP
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders

    try:
        msg = MIMEMultipart()
        msg["From"] = to_emails[0]
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if attachment_path:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            msg.attach(part)

        with SMTP(smtp_server, int(port)) as server:
            server.starttls()
            server.login(to_emails[0], password)
            server.sendmail(to_emails[0], to_emails, msg.as_string())

        return "E-mail sent !"
    except Exception as e:
        return f"Error while sending email : {str(e)}"


class ConfigWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setGeometry(300, 300, 400, 300)

        self.layout = QVBoxLayout()
        self.label_whisper_path = QLabel("Whisper Path :")
        self.input_whisper_path = QLineEdit()

        self.label_smtp_server = QLabel("SMTP Server:")
        self.input_smtp_server = QLineEdit()

        self.label_port = QLabel("Port :")
        self.input_port = QLineEdit()

        self.label_email = QLabel("Email :")
        self.input_email = QLineEdit()

        self.label_password = QLabel("Password :")
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)

        self.button_save = QPushButton("Save")
        self.button_save.clicked.connect(self.save_config)

        self.layout.addWidget(self.label_whisper_path)
        self.layout.addWidget(self.input_whisper_path)
        self.layout.addWidget(self.label_smtp_server)
        self.layout.addWidget(self.input_smtp_server)
        self.layout.addWidget(self.label_port)
        self.layout.addWidget(self.input_port)
        self.layout.addWidget(self.label_email)
        self.layout.addWidget(self.input_email)
        self.layout.addWidget(self.label_password)
        self.layout.addWidget(self.input_password)
        self.layout.addWidget(self.button_save)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.load_config()

    def load_config(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
            self.input_whisper_path.setText(settings.get("whisper_path", ""))
            self.input_smtp_server.setText(settings.get("smtp_server", ""))
            self.input_port.setText(settings.get("port", ""))
            self.input_email.setText(settings.get("email", ""))
            self.input_password.setText(settings.get("password", ""))
        except FileNotFoundError:
            QMessageBox.warning(self, "Errorr", "Cannot find settings.json.")
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Error", "Error reading settings.json.")

    def save_config(self):
        try:
            settings = {
                "whisper_path": self.input_whisper_path.text(),
                "smtp_server": self.input_smtp_server.text(),
                "port": self.input_port.text(),
                "email": self.input_email.text(),
                "password": self.input_password.text(),
            }
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
            QMessageBox.information(self, "Success", "Settings have been saved.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Errorr", f"Error while saving settings : {str(e)}")


class YouTubeSummarizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTubeSummarizer")
        self.setGeometry(200, 200, 400, 600)

        self.layout = QVBoxLayout()
        self.label_input = QLabel("YouTube URL or local file :")
        self.input_path = QLineEdit()
        self.button_file = QPushButton("Upload a file")
        self.button_file.clicked.connect(self.upload_file)

        self.label_summary = QLabel("Type of summary :")
        self.dropdown_summary = QComboBox()
        self.dropdown_summary.addItems(["Short", "Detailled (A4 sheet)", "Complete verbatim"])

        self.label_language = QLabel("Language of the transcript :")
        self.dropdown_language = QComboBox()
        self.dropdown_language.addItems(["FR", "EN"])

        self.label_email = QLabel("other email addresses (comma separeted) :")
        self.input_email = QLineEdit()

        self.button_config = QPushButton("Configure")
        self.button_config.clicked.connect(self.open_config_window)

        self.button_run = QPushButton("GO")
        self.button_run.clicked.connect(self.run_process)

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)

        self.layout.addWidget(self.label_input)
        self.layout.addWidget(self.input_path)
        self.layout.addWidget(self.button_file)
        self.layout.addWidget(self.label_summary)
        self.layout.addWidget(self.dropdown_summary)
        self.layout.addWidget(self.label_language)
        self.layout.addWidget(self.dropdown_language)
        self.layout.addWidget(self.label_email)
        self.layout.addWidget(self.input_email)
        self.layout.addWidget(self.button_run)
        self.layout.addWidget(self.logs)
        self.layout.addWidget(self.button_config)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.log_handler = LogHandler()
        self.log_handler.log_signal.connect(self.log_message)

    def log_message(self, message, is_error=False):
        if is_error:
            self.logs.setTextColor(QColor("red"))
        else:
            self.logs.setTextColor(QColor("black"))
        self.logs.append(message)
        self.logs.moveCursor(QTextCursor.End)

    def upload_file(self):
        file_types = "Audio/Video Files (*.mp3 *.wav *.aac *.ogg *.flac *.mov *.mkv *.mp4 *.mpeg *.avi *.flv *.wmv)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélect a file", "", file_types)
        if file_path:
            self.input_path.setText(file_path)

    def open_config_window(self):
        self.config_window = ConfigWindow(self)
        self.config_window.show()

    def run_process(self):
        input_path = self.input_path.text().strip()
        is_file = not input_path.startswith("http")
        summary_type = self.dropdown_summary.currentText()
        language = self.dropdown_language.currentText()

        if not input_path:
            QMessageBox.critical(self, "Error", "Please enter an URL or upload a file.")
            return

        threading.Thread(
            target=process_input,
            args=(input_path, is_file, summary_type, language, self.log_handler),
        ).start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = YouTubeSummarizerApp()
    main_window.show()
    sys.exit(app.exec_())

