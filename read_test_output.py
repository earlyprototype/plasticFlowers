
import os

def read_file(path):
    print(f"--- Reading {path} ---")
    if not os.path.exists(path):
        print("File not found.")
        return
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            print(f.read())
    except Exception as e:
        print(f"Error reading utf-8: {e}")
        try:
            with open(path, 'r', encoding='utf-16', errors='replace') as f:
                 print(f.read())
        except Exception as e2:
             print(f"Error reading utf-16: {e2}")

read_file('pytest_output.txt')
