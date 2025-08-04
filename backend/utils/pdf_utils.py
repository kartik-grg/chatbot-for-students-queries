import os
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
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

def get_text_chunks(text):
    """Split text into chunks for processing"""
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    """Create FAISS vector store from text chunks"""
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=Config.GOOGLE_API_KEY,
        task_type="retrieval_query" 
    )
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
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
    text = get_pdf_text(pdf_files)
    chunks = get_text_chunks(text)
    vectorstore = get_vector_store(chunks)
    print("Embeddings created successfully!")
    return vectorstore

def append_to_pdf(question, answer):
    """Append question and answer to extra.pdf"""
    pdf_path = os.path.join(os.getcwd(), "resources", "extra.pdf")
    
    # Create resources directory if it doesn't exist
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    try:
        # Try to read existing PDF
        if os.path.exists(pdf_path):
            try:
                existing_pdf = PdfReader(pdf_path)
                # If successfully read, create temp file
                c = canvas.Canvas(pdf_path + ".tmp", pagesize=letter)
                # Copy existing content by creating blank pages
                for _ in range(len(existing_pdf.pages)):
                    c.showPage()
            except:
                # If reading fails, start fresh
                print("Creating new PDF file due to corruption or empty file")
                c = canvas.Canvas(pdf_path, pagesize=letter)
        else:
            # If file doesn't exist, create new
            c = canvas.Canvas(pdf_path, pagesize=letter)
        
        # Add new content
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 750, f"Question:")
        c.setFont("Helvetica", 12)
        c.drawString(50, 730, question)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 690, f"Answer:")
        c.setFont("Helvetica", 12)
        c.drawString(50, 670, answer)
        
        c.showPage()
        c.save()
        
        # If temp file exists and main operation succeeded, replace original
        if os.path.exists(pdf_path + ".tmp"):
            os.replace(pdf_path + ".tmp", pdf_path)
            
        return True
        
    except Exception as e:
        print(f"Error in append_to_pdf: {str(e)}")
        # If anything fails, try to create a new PDF with just this Q&A
        try:
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 750, f"Question:")
            c.setFont("Helvetica", 12)
            c.drawString(50, 730, question)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 690, f"Answer:")
            c.setFont("Helvetica", 12)
            c.drawString(50, 670, answer)
            c.showPage()
            c.save()
            return True
        except Exception as e2:
            print(f"Critical error creating new PDF: {str(e2)}")
            return False

def update_vectorstore(vectorstore, question, answer):
    """Update the vectorstore with new Q&A"""
    # Create text chunk from new Q&A
    new_text = f"Question: {question}\nAnswer: {answer}"
    chunks = get_text_chunks(new_text)
    
    # Add new chunks to existing vectorstore
    vectorstore.add_texts(chunks)
    print("Vectorstore updated with new Q&A")
