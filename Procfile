web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
streamlit: streamlit run src/app.py --server.port $((PORT + 1)) 