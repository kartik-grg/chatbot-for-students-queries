import os
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from config.config import Config

def get_pdf_text(pdf_docs):
    """Extract text from PDF documents"""
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            # Skip if PDF has no pages
            if len(pdf_reader.pages) == 0:
                print(f"Skipping empty PDF: {pdf}")
                continue
            for page in pdf_reader.pages:
                text += page.extract_text()
        except Exception as e:
            print(f"Error reading PDF {pdf}: {str(e)}")
            continue
    return text

def get_text_chunks(text, source=None):
    """Split text into chunks for processing with metadata"""
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    # Add metadata if source is provided
    if source:
        return chunks, [{"source": source} for _ in chunks]
    return chunks

def get_vector_store(text_chunks):
    """Create Pinecone vector store from text chunks"""
    # Initialize Pinecone with v3 API
    pc = Pinecone(api_key=Config.PINECONE_API_KEY)
    
    # Check if index exists, if not create it
    index_name = Config.PINECONE_INDEX_NAME
    dimension = 768  # Dimension for Google Embeddings model
    
    # Check if the index already exists
    indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in indexes:
        print(f"Creating Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine"
        )
    
    # Create embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=Config.GOOGLE_API_KEY,
        task_type="retrieval_query" 
    )
    
    # Create and return the vector store
    vectorstore = PineconeVectorStore.from_texts(
        texts=text_chunks,
        embedding=embeddings,
        index_name=index_name
    )
    
    return vectorstore

def create_embeddings():
    """Create embeddings from PDF files in resources directory"""
    resources_dir = os.path.join(os.getcwd(), "resources")
    pdf_files = []
    
    # Check if resources directory exists
    if not os.path.exists(resources_dir):
        print("Resources directory not found, creating default vectorstore")
        default_text = "This is a student query chatbot for academic assistance."
        chunks = get_text_chunks(default_text)
        return get_vector_store(chunks)
    
    # Collect valid PDF files
    for filename in os.listdir(resources_dir):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(resources_dir, filename)
            try:
                # Try to open the PDF to check if it's valid
                with open(filepath, 'rb') as f:
                    pdf = PdfReader(f)
                    if len(pdf.pages) > 0:
                        pdf_files.append(filepath)
                    else:
                        print(f"Skipping empty PDF: {filename}")
            except Exception as e:
                print(f"Error checking PDF {filename}: {str(e)}")
                continue
    
    if not pdf_files:
        print("No valid PDF files found, creating default vectorstore")
        default_text = "This is a student query chatbot for academic assistance."
        chunks = get_text_chunks(default_text)
        return get_vector_store(chunks)
    
    print(f"Found {len(pdf_files)} valid PDF files")
    
    all_chunks = []
    all_metadatas = []
    
    for filepath in pdf_files:
        filename = os.path.basename(filepath)
        print(f"Processing {filename}...")
        text = get_pdf_text([filepath])
        chunks, metadatas = get_text_chunks(text, source=filename)
        all_chunks.extend(chunks)
        all_metadatas.extend(metadatas)
    
    # Initialize Pinecone with v3 API
    pc = Pinecone(api_key=Config.PINECONE_API_KEY)
    
    # Check if index exists, if not create it
    index_name = Config.PINECONE_INDEX_NAME
    dimension = 768  # Dimension for Google Embeddings model
    
    # Check if the index already exists
    indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in indexes:
        print(f"Creating Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine"
        )
    
    # Create embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=Config.GOOGLE_API_KEY,
        task_type="retrieval_query" 
    )
    
    # Create and return the vector store with namespace
    vectorstore = PineconeVectorStore.from_texts(
        texts=all_chunks,
        embedding=embeddings,
        metadatas=all_metadatas,
        index_name=index_name,
        namespace="course_materials"  # Organize by namespace
    )
    
    print("Embeddings created successfully!")
    return vectorstore

def append_to_pdf(question, answer):
    """Append question and answer to extra.pdf efficiently"""
    pdf_path = os.path.join(os.getcwd(), "resources", "extra.pdf")
    
    # Create resources directory if it doesn't exist
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    # Maximum Q&As per page and text wrapping settings
    MAX_QA_PER_PAGE = 5
    LINE_HEIGHT = 15
    PAGE_HEIGHT = 792  # Letter size height in points
    MARGIN_TOP = 50
    MARGIN_BOTTOM = 50
    MARGIN_LEFT = 50
    TEXT_WIDTH = 500
    
    def wrap_text(text, max_width=70):
        """Wrap text to fit within specified width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_width:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        return lines
    
    try:
        # Read existing Q&As from PDF if it exists
        existing_qas = []
        if os.path.exists(pdf_path):
            try:
                existing_pdf = PdfReader(pdf_path)
                full_text = ""
                for page in existing_pdf.pages:
                    full_text += page.extract_text() + "\n"
                
                # Improved parsing logic
                if full_text.strip():
                    # Split by Q&A markers and clean up
                    import re
                    
                    # Find all Q&A sections using regex
                    qa_pattern = r'Q&A #\d+\s*Question:\s*(.*?)\s*Answer:\s*(.*?)(?=Q&A #\d+|$)'
                    matches = re.findall(qa_pattern, full_text, re.DOTALL | re.IGNORECASE)
                    
                    for match in matches:
                        question_text = match[0].strip()
                        answer_text = match[1].strip()
                        
                        # Clean up the extracted text
                        question_text = re.sub(r'\s+', ' ', question_text)
                        answer_text = re.sub(r'\s+', ' ', answer_text)
                        
                        # Remove any remaining Q&A markers from the text
                        question_text = re.sub(r'Q&A #\d+', '', question_text).strip()
                        answer_text = re.sub(r'Q&A #\d+', '', answer_text).strip()
                        
                        if question_text and answer_text:
                            existing_qas.append((question_text, answer_text))
                    
                    # If regex parsing fails, try manual parsing as fallback
                    if not existing_qas and "Question:" in full_text:
                        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                        
                        i = 0
                        while i < len(lines):
                            line = lines[i]
                            
                            # Look for Question: marker
                            if "Question:" in line:
                                # Extract question
                                question_text = line.replace("Question:", "").strip()
                                question_text = re.sub(r'Q&A #\d+', '', question_text).strip()
                                
                                # Continue reading question lines until we hit Answer:
                                i += 1
                                while i < len(lines) and "Answer:" not in lines[i]:
                                    if lines[i] and not lines[i].startswith("Q&A #"):
                                        question_text += " " + lines[i]
                                    i += 1
                                
                                # Extract answer
                                answer_text = ""
                                if i < len(lines) and "Answer:" in lines[i]:
                                    answer_text = lines[i].replace("Answer:", "").strip()
                                    answer_text = re.sub(r'Q&A #\d+', '', answer_text).strip()
                                    
                                    # Continue reading answer lines until next Q&A or end
                                    i += 1
                                    while i < len(lines) and not lines[i].startswith("Q&A #") and "Question:" not in lines[i]:
                                        if lines[i]:
                                            answer_text += " " + lines[i]
                                        i += 1
                                    i -= 1  # Step back one since we'll increment at end of loop
                                
                                # Clean up and add if both question and answer exist
                                question_text = re.sub(r'\s+', ' ', question_text).strip()
                                answer_text = re.sub(r'\s+', ' ', answer_text).strip()
                                
                                if question_text and answer_text:
                                    # Check for duplicates
                                    if not any(q == question_text for q, a in existing_qas):
                                        existing_qas.append((question_text, answer_text))
                            
                            i += 1
                            
            except Exception as e:
                print(f"Could not read existing PDF, starting fresh: {str(e)}")
                existing_qas = []
        
        # Check if the new Q&A already exists to avoid duplicates
        new_qa_exists = any(q.strip().lower() == question.strip().lower() for q, a in existing_qas)
        if not new_qa_exists:
            existing_qas.append((question, answer))
        else:
            print("Q&A already exists, skipping duplicate.")
        
        # Limit total Q&As to prevent PDF from becoming too large
        MAX_TOTAL_QAS = 50
        if len(existing_qas) > MAX_TOTAL_QAS:
            # Keep only the most recent Q&As
            existing_qas = existing_qas[-MAX_TOTAL_QAS:]
        
        # Create new PDF with all Q&As
        temp_path = pdf_path + ".tmp"
        c = canvas.Canvas(temp_path, pagesize=letter)
        
        current_y = PAGE_HEIGHT - MARGIN_TOP
        qa_count_on_page = 0
        
        for i, (q, a) in enumerate(existing_qas):
            # Check if we need a new page
            if qa_count_on_page >= MAX_QA_PER_PAGE:
                c.showPage()
                current_y = PAGE_HEIGHT - MARGIN_TOP
                qa_count_on_page = 0
            
            # Wrap question and answer text
            q_lines = wrap_text(q)
            a_lines = wrap_text(a)
            
            # Calculate space needed for this Q&A
            space_needed = (len(q_lines) + len(a_lines) + 4) * LINE_HEIGHT  # +4 for labels and spacing
            
            # Check if we have enough space on current page
            if current_y - space_needed < MARGIN_BOTTOM:
                c.showPage()
                current_y = PAGE_HEIGHT - MARGIN_TOP
                qa_count_on_page = 0
            
            # Draw Q&A number
            c.setFont("Helvetica-Bold", 12)
            c.drawString(MARGIN_LEFT, current_y, f"Q&A #{i + 1}")
            current_y -= LINE_HEIGHT + 5
            
            # Draw Question
            c.setFont("Helvetica-Bold", 11)
            c.drawString(MARGIN_LEFT, current_y, "Question:")
            current_y -= LINE_HEIGHT
            
            c.setFont("Helvetica", 10)
            for line in q_lines:
                c.drawString(MARGIN_LEFT + 10, current_y, line)
                current_y -= LINE_HEIGHT
            
            current_y -= 5  # Extra spacing
            
            # Draw Answer
            c.setFont("Helvetica-Bold", 11)
            c.drawString(MARGIN_LEFT, current_y, "Answer:")
            current_y -= LINE_HEIGHT
            
            c.setFont("Helvetica", 10)
            for line in a_lines:
                c.drawString(MARGIN_LEFT + 10, current_y, line)
                current_y -= LINE_HEIGHT
            
            current_y -= 20  # Space between Q&As
            qa_count_on_page += 1
        
        c.save()
        
        # Replace original file with new one
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        os.rename(temp_path, pdf_path)
        
        print(f"Successfully appended Q&A to PDF. Total Q&As: {len(existing_qas)}")
        return True
        
    except Exception as e:
        print(f"Error in append_to_pdf: {str(e)}")
        # Clean up temp file if it exists
        temp_path = pdf_path + ".tmp"
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False

# Update the update_vectorstore function
def update_vectorstore(vectorstore, question, answer):
    """Update the Pinecone vector store with new Q&A"""
    # Create text chunk from new Q&A
    new_text = f"Question: {question}\nAnswer: {answer}"
    chunks = get_text_chunks(new_text)
    
    # Add metadata to chunks
    metadatas = [{"source": "admin_response", "question": question[:100]} for _ in chunks]
    
    # Add new chunks to Pinecone vectorstore
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=Config.GOOGLE_API_KEY,
        task_type="retrieval_query" 
    )
    
    # Use the index name and namespace to add to the existing index
    index_name = Config.PINECONE_INDEX_NAME
    PineconeVectorStore.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=metadatas,
        index_name=index_name,
        namespace="admin_responses"  # Separate namespace for admin responses
    )
    print("Pinecone vectorstore updated with new Q&A")
