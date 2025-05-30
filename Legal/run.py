import os
import sys
import streamlit.web.cli as stcli

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)  # Insert at beginning to ensure it's found first

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", os.path.join(project_root, "ui_frontend", "interface.py")]
    sys.exit(stcli.main()) 
