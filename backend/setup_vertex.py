"""Helper script to setup Vertex AI credentials."""
import os
import sys
import json
from pathlib import Path

def setup_vertex():
    print("\n" + "="*80)
    print("VERTEX AI SETUP")
    print("="*80 + "\n")
    
    print("To use Vertex AI (Option B), we need:")
    print("1. A Google Cloud Service Account Key (JSON file)")
    print("2. The Project ID and Location")
    
    print("\nDo you have your Service Account JSON key file ready?")
    print("If not, go to: https://console.cloud.google.com/iam-admin/serviceaccounts")
    print("Create a key -> Download JSON.")
    
    json_path = input("\nPaste the full path to your .json key file: ").strip()
    
    # Remove quotes if user added them
    if (json_path.startswith('"') and json_path.endswith('"')) or \
       (json_path.startswith("'") and json_path.endswith("'")):
        json_path = json_path[1:-1]
        
    path_obj = Path(json_path)
    
    if not path_obj.exists():
        print(f"\nERROR: File not found at: {json_path}")
        return
        
    try:
        with open(path_obj, "r") as f:
            data = json.load(f)
            project_id = data.get("project_id")
            
        if not project_id:
            print("\nERROR: Could not find 'project_id' in the JSON file.")
            return
            
        print(f"\nFound Project ID: {project_id}")
        
    except Exception as e:
        print(f"\nERROR reading JSON: {e}")
        return

    location = input("Enter Google Cloud Region (default: us-central1): ").strip() or "us-central1"
    
    # Update .env file
    env_path = Path(".env")
    env_lines = []
    if env_path.exists():
        env_lines = env_path.read_text().splitlines()
        
    # Remove existing vertex keys
    env_lines = [l for l in env_lines if not l.startswith("VERTEX_PROJECT_ID=") and \
                 not l.startswith("VERTEX_LOCATION=") and \
                 not l.startswith("GOOGLE_APPLICATION_CREDENTIALS=")]
                 
    env_lines.append(f"VERTEX_PROJECT_ID={project_id}")
    env_lines.append(f"VERTEX_LOCATION={location}")
    env_lines.append(f"GOOGLE_APPLICATION_CREDENTIALS={json_path}")
    
    env_path.write_text("\n".join(env_lines))
    
    print("\n" + "="*80)
    print("SUCCESS! .env updated.")
    print(f"GOOGLE_APPLICATION_CREDENTIALS set to: {json_path}")
    print(f"VERTEX_PROJECT_ID set to: {project_id}")
    print("="*80)
    print("\nRestarting backend is required.")

if __name__ == "__main__":
    setup_vertex()


