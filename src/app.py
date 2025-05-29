import streamlit as st
import requests
import os
import time

API_URL = "http://localhost:8000/generate"  # Fixed port back to 8000
STATIC_DIR = os.path.abspath("static")

st.title("🎬 Manim Animation Generator")

# User input form
with st.form("animation_form"):
    prompt = st.text_area("📝 Prompt", "Draw a circle and make it grow")
    filename = st.text_input("💾 Output Filename", "circle_growth")
    quality = st.selectbox("🎥 Quality", ["l", "m", "h"])  # low, medium, high

    submitted = st.form_submit_button("Generate Animation")

if submitted:
    try:
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Start the request
        status_text.text("⏳ Sending request to server...")
        progress_bar.progress(10)
        
        # Make the request with a longer timeout
        response = requests.post(
            API_URL,
            json={
                "prompt": prompt,
                "filename": filename,
                "quality": quality
            },
            timeout=360  # 6 minutes timeout
        )
        
        progress_bar.progress(30)
        status_text.text("⏳ Processing animation...")

        if response.status_code == 200:
            data = response.json()
            progress_bar.progress(90)
            status_text.text("✅ Animation created!")
            
            video_path = data["video_path"]
            st.write(f"**Scene Class:** `{data['scene_class']}`")

            if os.path.exists(video_path):
                progress_bar.progress(100)
                st.video(video_path)
            else:
                st.error(f"❌ Video file not found at: {video_path}")
        else:
            error = response.json()
            error_msg = error.get('error', '') or error.get('detail', '')
            
            # Check for Manim-specific errors
            if 'AttributeError' in error_msg and 'point_from_function' in error_msg:
                st.error("❌ The generated animation code contains an error: " + 
                         "The Circle object doesn't have a 'point_from_function' method. " +
                         "Try a different prompt or simplify your request.")
                
                # Suggest a possible fix
                st.info("💡 Try a simpler prompt like: 'Create a circle that grows and changes color'")
            else:
                st.error(f"❌ Error: {error_msg}")
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out after 6 minutes. The animation might be too complex or the server might be busy.")
        st.info("💡 Try a simpler animation or try again later.")
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to the API server. Make sure it's running at http://localhost:8000")
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
    finally:
        # Clean up progress indicators
        progress_bar.empty()
        status_text.empty()