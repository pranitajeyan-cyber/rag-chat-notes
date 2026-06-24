"""
Build RAG Chat as a Windows .exe using PyInstaller.

Usage:
    python scripts/build_exe.py

The .exe will be in the dist/rag-chat-notes/ folder.
Run rag-chat-notes.exe to start the app — your browser will open automatically.
"""

import os
import sys
import subprocess

REQUIRED_PACKAGES = ["pyinstaller", "pip"]

def check_dependencies():
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def build():
    check_dependencies()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=rag-chat-notes",
        "--add-data=docs;docs",
        "--add-data=.env.example;.",
        "--hidden-import=langchain_huggingface",
        "--hidden-import=chromadb",
        "--hidden-import=google.generativeai",
        "--collect-all=sentence_transformers",
        "--collect-all=chromadb",
        "--windowed",
        "app.py",
    ]

    print("Building .exe... (this takes 2-5 minutes)")
    subprocess.check_call(cmd)

    print("\n✅ Done! Your .exe is at: dist/rag-chat-notes/rag-chat-notes.exe")
    print("📦 Size: ~300-400 MB (bundles Python + all libraries)")
    print("\nTo run: double-click rag-chat-notes.exe")
    print("Your browser will open at http://localhost:8501")

if __name__ == "__main__":
    build()
