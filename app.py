import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from flask import Flask, request, jsonify
from langchain_community.docstore.in_memory import InMemoryDocstore
from flask_cors import CORS
import logging
import sys

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
CORS(app)

# Load Sentence Transformer model, FAISS index, and documents
MODEL_NAME = 'all-MiniLM-L6-v2' # A common, good-quality model
FAISS_INDEX_PATH = os.path.join("faiss_index", "index.faiss")
DOCS_PATH = os.path.join("faiss_index", "index.pkl")

model = None
index = None
documents = None
error_message_global = None # To store any loading errors

try:
    logger.info(f"Loading sentence transformer model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    logger.info("Model loaded successfully.")

    if not os.path.exists(FAISS_INDEX_PATH):
        error_message_global = f"FAISS index not found at {FAISS_INDEX_PATH}"
        logger.error(error_message_global)
    else:
        logger.info(f"Loading FAISS index from {FAISS_INDEX_PATH}...")
        index = faiss.read_index(FAISS_INDEX_PATH)
        logger.info("FAISS index loaded successfully.")

    if not os.path.exists(DOCS_PATH):
        error_message_global = f"Documents pickle file not found at {DOCS_PATH}"
        logger.error(error_message_global)
        documents = None
    elif index is not None:
        logger.info(f"Loading documents tuple from {DOCS_PATH}...")
        try:
            with open(DOCS_PATH, 'rb') as f:
                loaded_tuple = pickle.load(f)
            logger.info("Documents tuple loaded successfully.")

            if not isinstance(loaded_tuple, tuple) or len(loaded_tuple) != 2:
                error_message_global = "Pickle file did not contain the expected tuple (docstore, id_map)."
                logger.error(error_message_global)
                documents = None
            else:
                docstore, index_to_docstore_id = loaded_tuple
                
                if not isinstance(docstore, InMemoryDocstore) or not hasattr(docstore, '_dict') or not isinstance(index_to_docstore_id, dict):
                    error_message_global = "Loaded tuple does not contain a valid InMemoryDocstore and id_map."
                    logger.error(error_message_global)
                    documents = None
                else:
                    temp_documents = []
                    logger.info(f"Reconstructing documents list from InMemoryDocstore (FAISS index size: {index.ntotal})...")
                    all_docs_reconstructed = True
                    for i in range(index.ntotal): # Iterate based on FAISS index size
                        doc_store_key = index_to_docstore_id.get(str(i)) # Langchain FAISS uses string keys for index_to_docstore_id
                        if doc_store_key is None: # Try integer key if string key fails (common variation)
                             doc_store_key = index_to_docstore_id.get(i)

                        if doc_store_key is not None:
                            langchain_document = docstore._dict.get(doc_store_key)
                            if langchain_document and hasattr(langchain_document, 'page_content'):
                                temp_documents.append(langchain_document.page_content)
                            else:
                                logger.error(f"Could not retrieve or find page_content for doc_store_key {doc_store_key} (FAISS index {i})")
                                temp_documents.append(f"Error: Missing document for FAISS index {i}")
                                all_docs_reconstructed = False
                        else:
                            logger.error(f"FAISS index {i} not found in index_to_docstore_id map.")
                            temp_documents.append(f"Error: Missing mapping for FAISS index {i}")
                            all_docs_reconstructed = False
                    
                    documents = temp_documents
                    
                    if not all_docs_reconstructed:
                        reconstruction_error = "Errors occurred during document list reconstruction. Some documents may be missing or replaced with error messages."
                        logger.warning(reconstruction_error)
                        if error_message_global: error_message_global += f"; {reconstruction_error}"
                        else: error_message_global = reconstruction_error
                    
                    logger.info(f"Successfully reconstructed {len(documents)} documents.")

                    if index.ntotal != len(documents):
                        mismatch_error = (
                            f"CRITICAL MISMATCH: FAISS index size ({index.ntotal}) "
                            f"vs reconstructed documents ({len(documents)})."
                        )
                        logger.error(mismatch_error)
                        if error_message_global: error_message_global += f"; {mismatch_error}"
                        else: error_message_global = mismatch_error
                        # This is a more critical error, potentially invalidate documents if lengths don't match
                        # For now, we proceed but the app might behave unexpectedly
        except Exception as e_pickle:
            pickle_error = f"Error processing pickle file from {DOCS_PATH}: {str(e_pickle)}"
            logger.error(pickle_error)
            error_message_global = pickle_error
            documents = None

except Exception as e:
    error_message_global = f"Error loading model/index/documents: {str(e)}"
    logger.error(error_message_global)
    # Invalidate all to prevent partial use
    model = None
    index = None
    documents = None


@app.route('/api/chat', methods=['POST'])
def chat():
    global model, index, documents, error_message_global # Allow access to global vars
    try:
        data = request.get_json()
        logger.info(f"Received message: {data}")
        
        if not data or 'message' not in data:
            logger.error("No message provided in request")
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['message']
        logger.info(f"Processing message: {user_message}")

        if error_message_global:
            logger.error(f"Returning server error due to loading failure: {error_message_global}")
            return jsonify({'error': f'Internal server error: Failed to load resources. {error_message_global}'}), 500
        
        if not model or not index or not documents:
            logger.error("Model, FAISS index, or documents not loaded properly.")
            return jsonify({'error': 'Internal server error: Resources not available.'}), 500

        # Encode the user's message
        query_embedding = model.encode([user_message])[0] # Pass as list, take first result

        # Search the FAISS index
        k = 3 # Number of results to retrieve
        distances, indices = index.search(np.array([query_embedding]), k)

        # Retrieve and format the results
        results = []
        if indices.size > 0:
            for i in range(len(indices[0])):
                doc_index = indices[0][i]
                if 0 <= doc_index < len(documents):
                    results.append({
                        'text': documents[doc_index],
                        'distance': float(distances[0][i])
                    })
                else:
                    logger.warning(f"Invalid document index {doc_index} from FAISS search.")
        
        if not results:
            response_text = "I couldn't find specific information for your query in the medical book. Please try rephrasing or ask a different question."
            logger.info("No relevant documents found in FAISS index.")
        else:
            # Extract symptom name from user message
            symptom = user_message.lower().strip()
            # Remove common words that might be part of the query
            symptom = symptom.replace('what causes', '').replace('why do i have', '').replace('i have', '').replace('what is', '').strip()
            
            # Initialize response sections
            why_it_happens = ""
            common_reasons = []
            precautions = []
            treatments = []
            
            # Process and categorize information from results
            for res in results:
                text = res['text'].lower()
                sentences = text.split('.')
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                        
                    # Categorize based on content and keywords
                    if ('cause' in sentence or 'due to' in sentence or 'result' in sentence or 'response to' in sentence) and not why_it_happens:
                        why_it_happens = sentence.capitalize()
                    
                    elif ('common' in sentence or 'often' in sentence or 'usually' in sentence or 'typical' in sentence or 'frequently' in sentence):
                        if len(common_reasons) < 3 and not any(reason.lower() in sentence.lower() for reason in common_reasons):
                            common_reasons.append(sentence.capitalize())
                    
                    elif ('avoid' in sentence or 'prevent' in sentence or 'should' in sentence or 'recommended' in sentence or 'important to' in sentence):
                        if len(precautions) < 2 and not any(precaution.lower() in sentence.lower() for precaution in precautions):
                            precautions.append(sentence.capitalize())
                    
                    elif ('treat' in sentence or 'medicine' in sentence or 'remedy' in sentence or 'relief' in sentence or 'help' in sentence):
                        if len(treatments) < 2 and not any(treatment.lower() in sentence.lower() for treatment in treatments):
                            treatments.append(sentence.capitalize())
            
            # Format the response
            response_text = f"Symptom: {symptom.title()}\n\n"
            
            # Why it Happens section
            if why_it_happens:
                response_text += f"Why it Happens: {why_it_happens}\n\n"
            else:
                response_text += "Why it Happens: This is a medical condition that requires professional evaluation for proper diagnosis\n\n"
            
            # Common Reasons section
            response_text += "Common Reasons:\n"
            if common_reasons:
                for reason in common_reasons:
                    response_text += f"• {reason}\n"
            else:
                response_text += "• Viral or bacterial infections\n"
                response_text += "• Environmental factors\n"
                response_text += "• Underlying medical conditions\n"
            
            # Precautions section
            response_text += "\nPrecautions:\n"
            if precautions:
                for precaution in precautions:
                    response_text += f"• {precaution}\n"
            else:
                response_text += "• Monitor your symptoms and maintain a record\n"
                response_text += "• Follow general health guidelines\n"
            
            # Treatment section
            response_text += "\nCure / Treatment:\n"
            if treatments:
                for treatment in treatments:
                    response_text += f"• {treatment}\n"
            else:
                response_text += "• Seek professional medical advice for proper diagnosis and treatment\n"
                response_text += "• Consult a doctor if symptoms persist or worsen\n"
            
            # Add disclaimer
            response_text += "\nNote: This information is for educational purposes only. Always consult a healthcare provider for medical advice."
            
            logger.info(f"Structured response created for symptom: {symptom}")
        
        # Sanitize the response text to handle any potential markdown or special characters
        sanitized_response = response_text.replace('<', '&lt;').replace('>', '&gt;')
        return jsonify({'response': sanitized_response})

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'Internal server error during chat processing.'}), 500

if __name__ == '__main__':
    # Ensure resources are loaded before starting app, or handle gracefully
    if model and index and documents:
        logger.info("Starting Flask app - resources loaded successfully.")
    else:
        logger.error(f"CRITICAL: Flask app starting with errors in resource loading: {error_message_global if error_message_global else 'Unknown error'}. API will likely fail.")
    app.run(host='0.0.0.0', port=5000, debug=True)
