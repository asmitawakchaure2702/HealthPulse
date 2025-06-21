import pickle
import os

DOCS_PATH = os.path.join("faiss_index", "index.pkl")

print(f"Attempting to load pickle file from: {DOCS_PATH}")

if not os.path.exists(DOCS_PATH):
    print(f"Error: Pickle file not found at {DOCS_PATH}")
else:
    try:
        with open(DOCS_PATH, 'rb') as f:
            data = pickle.load(f)
        
        print(f"Successfully loaded pickle file.")
        print(f"Type of loaded data: {type(data)}")
        
        if isinstance(data, tuple):
            print(f"Data is a tuple with {len(data)} elements.")
            for i, item in enumerate(data):
                print(f"  Element {i}: Type = {type(item)}")
                if isinstance(item, list):
                    print(f"    This element is a list with {len(item)} items.")
                    if len(item) > 0:
                        print(f"    Type of first item in this list: {type(item[0])}")
                        print(f"    Content of first item (first 100 chars): {str(item[0])[:100]}")
                elif isinstance(item, dict):
                     print(f"    This element is a dict with keys: {list(item.keys())}")
                # Add more specific checks if needed based on expected content

        elif isinstance(data, list): # Should not happen based on previous output, but good to keep
            print(f"Data is a list. Number of items: {len(data)}")
            if len(data) > 0:
                print(f"Type of first item: {type(data[0])}")
                print(f"First item's content (first 100 chars): {str(data[0])[:100]}")
        elif isinstance(data, dict):
            print(f"Data is a dictionary. Keys: {list(data.keys())}")
        else:
            print(f"Data is not a tuple, list, or dictionary. Investigate its structure.")

    except Exception as e:
        print(f"Error loading or inspecting pickle file: {str(e)}")
