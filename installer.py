import os
import subprocess
import sys

def install(package):
    """Install a Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package}: {e}")

def main():
    # Liste des dépendances nécessaires
    dependencies = [
        "PyQt5",
        "yt-dlp",
        "ffmpeg-python"
    ]

    print("Installation des dépendances nécessaires...")
    for dependency in dependencies:
        print(f"Vérification et installation de {dependency}...")
        install(dependency)

    # Vérification et installation de ffmpeg si nécessaire
    print("\nVérification de l'installation de FFmpeg...")
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("FFmpeg est déjà installé.")
    except FileNotFoundError:
        print("FFmpeg n'est pas installé. Téléchargez et installez-le depuis : https://ffmpeg.org/download.html")
        if sys.platform.startswith("win"):
            print("Pour Windows, ajoutez FFmpeg au PATH après l'installation.")

    print("\nToutes les dépendances sont installées.")

if __name__ == "__main__":
    main()

