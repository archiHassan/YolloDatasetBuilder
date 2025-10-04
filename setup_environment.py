#!/usr/bin/env python3
"""
Environment setup script for YOLO Dataset Builder Phase 2.
This script helps set up the complete environment needed for Phase 2 functionality.
"""

import subprocess
import sys
import os
from pathlib import Path
import importlib.util

def run_command(command, description=""):
    """Run a command and return success status."""
    print(f"{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ SUCCESS")
        if result.stdout:
            print("Output:", result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print("✗ FAILED")
        print("Error:", e.stderr.strip())
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} is not compatible. Need Python 3.8+")
        return False

def check_package_installed(package_name):
    """Check if a package is already installed."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_core_dependencies():
    """Install core dependencies."""
    print("\n" + "="*60)
    print("INSTALLING CORE DEPENDENCIES")
    print("="*60)
    
    # Core requirements
    core_packages = [
        "torch>=2.0.0",
        "torchvision>=0.15.0", 
        "numpy>=1.24.0",
        "pillow>=9.0.0",
        "opencv-python>=4.8.0",
        "pyyaml>=6.0",
        "click>=8.0.0",
        "tqdm>=4.65.0",
        "pandas>=2.0.0"
    ]
    
    for package in core_packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            print(f"Warning: Failed to install {package}")
    
    return True

def install_ml_dependencies():
    """Install ML and computer vision dependencies."""
    print("\n" + "="*60)
    print("INSTALLING ML/CV DEPENDENCIES")
    print("="*60)
    
    ml_packages = [
        "ultralytics>=8.0.0",
        "transformers>=4.35.0",
        "timm>=0.9.0",
        "accelerate>=0.24.0",
        "scikit-learn>=1.3.0",
        "imagehash>=4.3.1",
        "pycocotools",
        "networkx>=3.0"
    ]
    
    for package in ml_packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            print(f"Warning: Failed to install {package}")
    
    return True

def install_nlp_dependencies():
    """Install NLP dependencies."""
    print("\n" + "="*60)
    print("INSTALLING NLP DEPENDENCIES")
    print("="*60)
    
    nlp_packages = [
        "spacy>=3.7.0",
        "nltk>=3.8.1", 
        "fuzzywuzzy>=0.18.0",
        "python-levenshtein>=0.23.0"
    ]
    
    for package in nlp_packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            print(f"Warning: Failed to install {package}")
    
    # Download spaCy model
    print("\nDownloading spaCy English model...")
    run_command("python -m spacy download en_core_web_sm", "Downloading spaCy English model")
    
    return True

def install_vision_language_models():
    """Install vision-language model dependencies."""
    print("\n" + "="*60)
    print("INSTALLING VISION-LANGUAGE MODEL DEPENDENCIES")
    print("="*60)
    
    vl_packages = [
        "open-clip-torch>=2.24.0",
        "lavis>=1.0.2"
    ]
    
    for package in vl_packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            print(f"Warning: Failed to install {package}")
    
    return True

def install_optional_dependencies():
    """Install optional dependencies."""
    print("\n" + "="*60)
    print("INSTALLING OPTIONAL DEPENDENCIES")
    print("="*60)
    
    optional_packages = [
        "supervision>=0.16.0",
        "plotly>=5.17.0",
        "seaborn>=0.13.0"
    ]
    
    for package in optional_packages:
        print(f"Installing optional package: {package}")
        run_command(f"pip install {package}", f"Installing {package}")
    
    # Optional: Try to install Grounding DINO (might fail, that's ok)
    print("\nTrying to install Grounding DINO (optional, may fail)...")
    run_command("pip install groundingdino-py>=0.1.0", "Installing Grounding DINO")
    
    return True

def download_nltk_data():
    """Download required NLTK data."""
    print("\n" + "="*60)
    print("DOWNLOADING NLTK DATA")
    print("="*60)
    
    nltk_downloads = [
        "punkt",
        "wordnet", 
        "omw-1.4",
        "stopwords"
    ]
    
    try:
        import nltk
        for item in nltk_downloads:
            print(f"Downloading NLTK {item}...")
            try:
                nltk.download(item, quiet=True)
                print(f"✓ Downloaded {item}")
            except Exception as e:
                print(f"✗ Failed to download {item}: {e}")
    except ImportError:
        print("NLTK not installed, skipping NLTK data download")
    
    return True

def verify_installation():
    """Verify that key packages are installed correctly."""
    print("\n" + "="*60)
    print("VERIFYING INSTALLATION")
    print("="*60)
    
    key_packages = [
        ("torch", "PyTorch"),
        ("torchvision", "TorchVision"), 
        ("cv2", "OpenCV"),
        ("ultralytics", "YOLOv8"),
        ("transformers", "HuggingFace Transformers"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("yaml", "PyYAML"),
        ("click", "Click"),
        ("tqdm", "TQDM"),
        ("sklearn", "Scikit-learn"),
        ("nltk", "NLTK"),
        ("spacy", "spaCy"),
        ("fuzzywuzzy", "FuzzyWuzzy"),
        ("networkx", "NetworkX")
    ]
    
    success_count = 0
    total_count = len(key_packages)
    
    for package, name in key_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {name} - OK")
            success_count += 1
        except ImportError:
            print(f"✗ {name} - FAILED")
    
    print(f"\nVerification Results: {success_count}/{total_count} packages available")
    
    if success_count >= total_count * 0.8:  # 80% success rate
        print("✓ Installation verification PASSED")
        return True
    else:
        print("✗ Installation verification FAILED")
        return False

def create_test_script():
    """Create a test script to validate the installation."""
    test_script = '''#!/usr/bin/env python3
"""
Quick test script to validate Phase 2 environment setup.
"""

def test_imports():
    """Test importing key libraries."""
    try:
        # Core ML libraries
        import torch
        import torchvision
        import ultralytics
        import cv2
        import numpy as np
        import pandas as pd
        
        # Transformers and vision-language models
        import transformers
        
        # NLP libraries
        import nltk
        import spacy
        import sklearn
        import fuzzywuzzy
        import networkx
        
        # Configuration and utilities
        import yaml
        import click
        import tqdm
        
        print("✓ All core imports successful!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_models():
    """Test loading basic models."""
    try:
        # Test YOLO
        from ultralytics import YOLO
        print("✓ YOLO import successful")
        
        # Test transformers
        from transformers import pipeline
        print("✓ Transformers import successful")
        
        # Test spaCy
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✓ spaCy English model loaded successfully")
        except OSError:
            print("⚠ spaCy English model not found (run: python -m spacy download en_core_web_sm)")
        
        return True
        
    except Exception as e:
        print(f"✗ Model loading error: {e}")
        return False

def main():
    print("Phase 2 Environment Test")
    print("=" * 40)
    
    import_success = test_imports()
    model_success = test_models()
    
    if import_success and model_success:
        print("\\n✓ Environment setup is ready for Phase 2!")
        return True
    else:
        print("\\n✗ Environment setup has issues. Check installation.")
        return False

if __name__ == "__main__":
    main()
'''
    
    with open("test_environment.py", "w") as f:
        f.write(test_script)
    
    print("✓ Created test_environment.py script")

def main():
    """Main setup function."""
    print("YOLO Dataset Builder - Phase 2 Environment Setup")
    print("=" * 60)
    print("This script will install all dependencies needed for Phase 2 functionality.")
    print("Including: BLIP, NLP processing, Active Learning, and Enhanced Ensemble")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        print("Please upgrade to Python 3.8 or higher and try again.")
        sys.exit(1)
    
    # Install dependencies in order
    steps = [
        ("Core Dependencies", install_core_dependencies),
        ("ML/CV Dependencies", install_ml_dependencies), 
        ("NLP Dependencies", install_nlp_dependencies),
        ("Vision-Language Models", install_vision_language_models),
        ("Optional Dependencies", install_optional_dependencies),
        ("NLTK Data", download_nltk_data)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🚀 Starting: {step_name}")
        try:
            step_func()
            print(f"✓ Completed: {step_name}")
        except Exception as e:
            print(f"✗ Error in {step_name}: {e}")
            print("Continuing with next step...")
    
    # Verify installation
    print("\n🔍 Verifying installation...")
    if verify_installation():
        print("\n🎉 Environment setup completed successfully!")
    else:
        print("\n⚠️ Environment setup completed with some issues.")
    
    # Create test script
    create_test_script()
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print("Next steps:")
    print("1. Run: python test_environment.py")
    print("2. If tests pass, try: python test_phase2_syntax.py")
    print("3. Then test the pipeline: python -m src.yolo_dataset_builder.main --help")
    print("=" * 60)

if __name__ == "__main__":
    main()