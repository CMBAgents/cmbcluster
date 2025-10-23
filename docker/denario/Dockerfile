# Custom Denario image for CMBCluster with dynamic project directory support
FROM pablovd/denario:latest

# Run as user 1000 (matches GKE security requirements)
USER 1000

# Expose Streamlit port
EXPOSE 8501

# Command to run the app with --deploy flag for dynamic project directory
# The --deploy flag makes Denario use get_project_dir() which creates directories dynamically
CMD ["streamlit", "run", "/usr/local/lib/python3.12/site-packages/denario_app/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--", "--deploy"]
