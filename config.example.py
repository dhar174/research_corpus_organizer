# Example Configuration File
# Copy this to config.py and fill in your values

# Google Drive Settings
DRIVE_FOLDER_PATH = "/content/drive/MyDrive/Research_PDFs"
OUTPUT_FOLDER = "/content/drive/MyDrive/Research_Brain_Output"

# OpenAI API Settings
OPENAI_API_KEY = ""  # Add your OpenAI API key here

# Model Configuration
MODEL_NAME = "gpt-4-turbo-preview"  # Will update to GPT-5.1 when available
EMBEDDING_MODEL = "text-embedding-3-large"

# Processing Settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_TOKENS_PER_CHUNK = 500

# Taxonomy Configuration
TIER_1_CATEGORIES = [
    "Computer Science",
    "Physics", 
    "Mathematics",
    "Biology",
    "Chemistry",
    "Engineering",
    "Other"
]

# FAISS Settings
EMBEDDING_DIMENSION = 3072  # For text-embedding-3-large
