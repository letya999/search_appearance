import gradio as gr
import os
from typing import List
from mvp.storage.db import PhotoDatabase
from mvp.annotator.batch_process import process_folder
from mvp.annotator.client import VLMClient
from mvp.annotator.batch_process import process_file
from mvp.search.aggregator import ProfileAggregator
from mvp.search.ranker import Ranker
from mvp.schema.models import PhotoProfile
import uuid
import shutil

# Initialize Logic
DB_PATH = "data/db.json"
os.makedirs("data", exist_ok=True)
db = PhotoDatabase(db_path=DB_PATH)
aggregator = ProfileAggregator()
ranker = Ranker()
# VLM Client might be needed for fresh uploads
try:
    vlm_client = VLMClient()
except:
    vlm_client = None

def get_db_images():
    db.load() # Reload
    profiles = db.get_all_profiles()
    # Return list of (path, label)
    return [(p.image_path, f"ID: {p.id[:8]}...") for p in profiles]

def index_folder(folder_path, progress=gr.Progress()):
    if not folder_path or not os.path.exists(folder_path):
        return "Invalid folder path"
    
    # We use process_folder but we want to point it to our DB file
    # process_folder appends to a list in the file.
    # Our DB handles loading lists.
    # We might need to "merge" if DB already has dict structure.
    # best is to process to a temp file, then load and add to DB.
    
    temp_out = "data/temp_batch.json"
    try:
        process_folder(folder_path, temp_out)
        
        # Merge
        temp_db = PhotoDatabase(temp_out) # Reads the list we just made
        for p in temp_db.get_all_profiles():
            db.add_profile(p)
            
        return f"Indexed {len(temp_db.get_all_profiles())} profiles."
    except Exception as e:
        return f"Error: {e}"

def analyze_query_image(image_path: str) -> PhotoProfile:
    # Process single image for query
    if not vlm_client:
        raise Exception("VLM Client unavailable")
    
    # process_file returns dict
    p_dict = process_file(vlm_client, image_path)
    return PhotoProfile(**p_dict)

def visual_search(positive_files, negative_files, gender_filter, face_weight, hair_weight, body_weight):
    # 1. Analyze Uploaded Queries
    pos_profiles = []
    neg_profiles = []
    
    # Process Positives
    if positive_files:
        for f in positive_files:
            try:
                prof = analyze_query_image(f.name)
                pos_profiles.append(prof)
            except Exception as e:
                print(f"Error analyzing positive: {e}")

    # Process Negatives
    if negative_files:
        for f in negative_files:
            try:
                prof = analyze_query_image(f.name)
                neg_profiles.append(prof)
            except Exception as e:
                print(f"Error analyzing negative: {e}")

    if not pos_profiles:
        return [] # No positives

    # 2. Build Target
    target = aggregator.build_target_profile(pos_profiles, neg_profiles)
    
    # 3. Construct Weights
    # We construct a dictionary to override specific fields based on multipliers
    weights = {}
    
    # Helper to boost category
    def boost_category(cat_prefix, multiplier):
        # We don't have a list of all keys easily available unless we iterate models
        # For MVP, we'll manually boost key fields
        if cat_prefix == "face":
            keys = ["face.face_shape", "face.eye_color", "face.eye_shape", "face.nose", "face.lips", "face.jawline"]
        elif cat_prefix == "hair":
            keys = ["hair.color", "hair.length", "hair.texture"]
        elif cat_prefix == "basic": # Body usually implies basic attributes
             keys = ["basic.height", "basic.body_type"]
        else:
            keys = []
            
        for k in keys:
            # We assume base weight ~1.0-1.5, so we just multiply it?
            # Ranker.DEFAULT_WEIGHTS keys might slightly differ, but Ranker merges.
            # Ideally we read Ranker.DEFAULT_WEIGHTS and scale.
            base = ranker.DEFAULT_WEIGHTS.get(k, 1.0)
            weights[k] = base * multiplier

    boost_category("face", face_weight)
    boost_category("hair", hair_weight)
    boost_category("basic", body_weight)

    # 4. Search
    db.load()
    candidates = db.get_all_profiles()
    
    # Filter
    if gender_filter and gender_filter != "All":
        filtered = []
        for c in candidates:
            # Check basic.gender exists
            if c.basic and c.basic.gender and c.basic.gender.value:
                # Value is Enum, so .value gives string, e.g. "male"
                # Wait, c.basic.gender is AttributeScore. value is Gender Enum.
                # Gender Enum value is string.
                g_val = c.basic.gender.value.value if hasattr(c.basic.gender.value, 'value') else c.basic.gender.value
                if g_val.lower() == gender_filter.lower():
                    filtered.append(c)
        candidates = filtered
        
    results = []
    for cand in candidates:
        score = ranker.score_candidate(target, cand, weights=weights)
        results.append((cand, score))
        
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Return Top 20
    output = []
    for p, s in results[:20]:
        output.append((p.image_path, f"Score: {s:.2f}"))
        
    return output

# UI Layout
with gr.Blocks(title="Visual Dating Search MVP") as demo:
    gr.Markdown("# 🔍 Visual Dating Search (MVP)")
    
    with gr.Tab("Knowledge Base"):
        gr.Markdown("### Index Photos")
        folder_input = gr.Textbox(label="Images Folder Path", placeholder="C:/images/...")
        index_btn = gr.Button("Start Indexing (VLM)")
        status_output = gr.Textbox(label="Status")
        
        gr.Markdown("### Database Preview")
        refresh_btn = gr.Button("Refresh Gallery")
        db_gallery = gr.Gallery(label="Indexed Profiles", columns=6, height=400)
        
        index_btn.click(index_folder, inputs=folder_input, outputs=status_output)
        refresh_btn.click(get_db_images, outputs=db_gallery)
        
    with gr.Tab("Visual Search"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 1. Upload Query Images")
                pos_input = gr.File(label="Positive Examples (What you like)", file_count="multiple", type="filepath")
                neg_input = gr.File(label="Negative Examples (What you don't)", file_count="multiple", type="filepath")
                
                gr.Markdown("### 2. Filters & Weights")
                gender_input = gr.Radio(["All", "Male", "Female"], label="Gender Filter", value="All")
                
                with gr.Accordion("Importance Weights", open=False):
                    face_slider = gr.Slider(0.1, 3.0, value=1.0, label="Face Importance")
                    hair_slider = gr.Slider(0.1, 3.0, value=1.0, label="Hair Importance")
                    body_slider = gr.Slider(0.1, 3.0, value=1.0, label="Body Importance")
                
                search_btn = gr.Button("🔍 Search Match", variant="primary")
            
            with gr.Column(scale=2):
                gr.Markdown("### 3. Results")
                results_gallery = gr.Gallery(label="Top Matches", columns=4)
                
        search_btn.click(
            visual_search, 
            inputs=[pos_input, neg_input, gender_input, face_slider, hair_slider, body_slider], 
            outputs=results_gallery
        )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
