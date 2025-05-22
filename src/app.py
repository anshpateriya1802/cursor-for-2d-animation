import streamlit as st
import requests

API_URL = "http://localhost:8000/generate"

st.title("🎬 Manim Animation Generator")

# User input form
with st.form("animation_form"):
    prompt = st.text_area("📝 Prompt", "Draw a circle and make it grow")
    filename = st.text_input("💾 Output Filename", "circle_growth")
    quality = st.selectbox("🎥 Quality", ["l", "m", "h"])  # low, medium, high

    submitted = st.form_submit_button("Generate Animation")

if submitted:
    with st.spinner("⏳ Generating animation..."):
        response = requests.post(API_URL, json={
            "prompt": prompt,
            "filename": filename,
            "quality": quality
        })

        if response.status_code == 200:
            data = response.json()
            st.success(data["message"])

            video_path = data["video_path"]
            st.write(f"**Scene Class:** `{data['scene_class']}`")

            # Load video file and display
            try:
                with open(video_path, "rb") as f:
                    video_bytes = f.read()
                st.video(video_bytes)
            except FileNotFoundError:
                st.error("❌ Video file not found.")
        else:
            error = response.json()
            st.error(f"❌ Error: {error.get('error') or error.get('detail')}")