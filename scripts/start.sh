#!/bin/bash

# Install dependencies
pip install -r requirements.txt
 
# Run Streamlit app with Render-compatible settings
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.fileWatcherType=none 