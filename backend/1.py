import os

def get_absolute_path(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)

ABSOLUTE_PATH = get_absolute_path('backend/1.py')

print(f"Hello from {ABSOLUTE_PATH}")