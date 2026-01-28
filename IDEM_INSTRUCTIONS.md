# How to Run the Visual Search Demo

## 1. Backend Setup
First, we need to run the FastAPI server which handles the logic and database.

```powershell
# Install dependencies
pip install uvicorn python-multipart

# Run the server (from the root project directory)
python -m mvp.api.main
```
*The server will start at `http://127.0.0.1:8000`*

## 2. Frontend Setup
In a **new terminal**, set up and run the React UI.

```powershell
cd frontend

# Install dependencies
npm install

# Run the UI
npm run dev
```
*The UI will usually start at `http://localhost:5173`*

## 3. Using the App
1. Open `http://localhost:5173` in your browser.
2. Drag & Drop 1-5 photos into the **Target Vibe** box (Positive examples).
3. (Optional) Drag photos into **Exclude Traits** (Negative examples).
4. Click **Find Matches**.
5. The system will analyze your photos using the VLM (approx. 5-10s) and find the closest matches from your indexed dataset.
