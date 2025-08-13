import json
import os
from backend.main import app

def generate_schema():
    """Generates the OpenAPI schema and saves it to a file."""
    schema = app.openapi()

    # Create the output directory if it doesn't exist
    output_dir = "schema"
    os.makedirs(output_dir, exist_ok=True)

    # Save the schema to a file
    output_path = os.path.join(output_dir, "openapi.json")
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"✅ OpenAPI schema generated at {output_path}")

if __name__ == "__main__":
    generate_schema()
