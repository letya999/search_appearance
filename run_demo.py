import os
import sys

# Ensure module path is set
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting Visual Dating Search Demo...")
    print("Please ensure you have set the VLM_API_KEY environment variable if you plan to index new photos.")
    print("Note: The demo uses 'mvp/ui/app.py'.")
    
    # Import and launch
    from mvp.ui.app import demo
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
