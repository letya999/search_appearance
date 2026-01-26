# Visual Dating Search (MVP)

A visual search engine for dating profiles that allows users to find "lookalikes" or search by specific physical attributes using fuzzy logic and Vision Language Models (VLM).

## 🚀 Features

- **Visual Search**: Upload "Positive" (what you like) and "Negative" (what you don't) examples.
- **VLM Annotation**: Automatically extracts 20+ physical attributes from photos using AI (Qwen2.5-VL / Llava / GPT-4o).
- **Fuzzy Matching**: Uses semantic distance matrices to find profiles that are "close enough" (e.g., Light Brown hair is closer to Blonde than Black).
- **Attribute Filters**: Filter by Gender, and adjust importance weights for Face, Hair, and Body.

## 🛠️ Installation

### 1. Local Setup

**Prerequisites:**
- Python 3.12+
- `uv` or `pip`

**Steps:**
1. Clone the repository:
   ```bash
   git clone <repo_url>
   cd search_appearance
   ```

2. Install dependencies:
   ```bash
   pip install .
   # OR with uv
   uv sync
   ```

3. Set up Environment Variables:
   Create a `.env` file (optional if passing keys directly, but recommended for VLM):
   ```
   OPENAI_API_KEY=your_key_here
   OPENAI_BASE_URL=https://openrouter.ai/api/v1  # If using OpenRouter
   ```

4. Run the demo:
   ```bash
   python run_demo.py
   ```
   Open http://localhost:7860 in your browser.

### 2. Docker Setup

1. Build the image:
   ```bash
   docker build -t visual-dating-search .
   ```

2. Run the container:
   ```bash
   docker run -p 7860:7860 -e OPENAI_API_KEY=your_key visual-dating-search
   ```

## 📖 Usage

### Data Indexing (Knowledge Base)
1. Go to the "Knowledge Base" tab.
2. Enter the absolute path to a local folder containing images (e.g., `C:/datasets/faces`).
3. Click "Start Indexing". The system will use the configured VLM to analyze each image and save the attributes to `data/db.json`.

### Visual Search
1. Go to the "Visual Search" tab.
2. Upload 1-5 photos of people you find attractive in the "Positive Examples" box.
3. (Optional) Upload photos of people you definitively do not like in "Negative Examples".
4. Adjust filters (Gender) and importance sliders (Face vs Body vs Hair).
5. Click "Search Match". Matches are ranked by similarity score.

## 📂 Project Structure

- `mvp/schema`: Pydantic models and Enums for attributes.
- `mvp/core`: Distance matrices and similarity logic (Fuzzy Logic).
- `mvp/annotator`: VLM Client and prompt engineering.
- `mvp/search`: Aggregation of user preferences and ranking logic.
- `mvp/storage`: JSON-based database handler.
- `mvp/ui`: Gradio interface.
