# Search Appearance

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)
![Gradio](https://img.shields.io/badge/Gradio-4.0%2B-orange)

**Search Appearance** is an advanced visual search engine designed to find "lookalikes" or search by specific physical attributes. It leverages the power of Vision Language Models (VLMs) like GPT-4o, Claude 3.5, or Gemini to extract over 20+ distinct physical attributes from images and uses fuzzy logic matching to find the best results.

Unlike traditional reverse image search (which looks for pixel similarity), this project understands *semantic* features—hair color, face shape, body type, and vibe—allowing for much more nuanced and human-like search results.

## 🚀 Features

-   **Visual Lookalike Search**: Upload photos of people you find attractive ("Positive") and those you don't ("Negative") to build a personalized preference profile.
-   **AI-Powered Annotation**: Automatically tags images with attributes (Gender, Ethnicity, Hair Color/Style, Body Type, Vibe, etc.) using state-of-the-art VLMs.
-   **Fuzzy Matching Engine**: Uses semantic distance matrices. For example, "Dark Brown" hair is considered closer to "Black" than "Blonde".
-   **Privacy-First Design**: Includes built-in checks for blacklisted embeddings and duplicate prevention.
-   **Hybrid Application**:
    -   **Backend**: FastAPI for robust API handling.
    -   **Frontend**: Gradio (for demos) and React/Vite (planned).

## 🛠️ Installation

### Prerequisites
-   Python 3.12 or higher
-   [uv](https://github.com/astral-sh/uv) (recommended) or `pip`
-   Docker (optional, for containerized deployment)

### Local Development

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/search-appearance.git
    cd search-appearance
    ```

2.  **Install dependencies**
    Using `uv` (faster):
    ```bash
    uv sync
    ```
    Or using `pip`:
    ```bash
    pip install .
    ```

3.  **Configuration**
    Copy the example environment file and fill in your API keys:
    ```bash
    cp .env.example .env
    ```
    
    Edit `.env` to add at least one VLM provider (OpenAI, Anthropic, Google, or OpenRouter):
    ```ini
    OPENAI_API_KEY=sk-proj-your-key
    ```

4.  **Run the Application**
    
    Start the API server:
    ```bash
    # Run data indexing or other scripts as needed first
    python -m mvp.api.main
    ```
    
    *Or use the provided convenience script (if available):*
    ```bash
    python run_demo.py
    ```

### Docker Deployment

1.  **Build the container**
    ```bash
    docker build -t search-appearance .
    ```

2.  **Run the container**
    ```bash
    docker run -p 8000:8000 --env-file .env search-appearance
    ```

## 📖 Usage Guide

### 1. Indexing Data (Knowledge Base)
To make images searchable, they must first be analyzed.
1.  Navigate to the `/api/collections` (or use the UI).
2.  Point the system to a local directory of images.
3.  The VLM will process each image, extracting structured JSON attributes (Face, Hair, Body, Vibe).
4.  Embeddings (CLIP) and Face Vectors are computed for fast retrieval.

### 2. Search
1.  Upload 1-5 "Positive" anchor images.
2.  (Optional) Upload "Negative" images to refine the search.
3.  The system aggregates these inputs into a "Target Profile".
4.  It ranks the entire database against this target using a weighted scoring system.

## 📂 Project Structure

```text
search_appearance/
├── data/               # Local data storage (ignored by git)
├── mvp/                # Main application source
│   ├── annotator/      # VLM Client & Prompts
│   ├── api/            # FastAPI routes & wrappers
│   ├── core/           # Logic for embeddings & matching
│   ├── schema/         # Pydantic models & Enums
│   ├── search/         # Ranking algorithms
│   └── storage/        # Database & File handling
├── tests/              # Pytest suite
└── scripts/            # Utility scripts (analysis, cleanup)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the project
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
