import os
import sys
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

def test_cloudinary():
    # Load environment variables
    load_dotenv()
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    
    print("Cloudinary configuration:")
    print(f"Cloud name: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
    print(f"API key: {os.getenv('CLOUDINARY_API_KEY')[:5]}...")
    print(f"PDF folder: {os.getenv('CLOUDINARY_PDF_FOLDER')}")
    
    # Test listing folders
    try:
        folders = cloudinary.api.root_folders()
        print(f"Root folders: {folders}")
    except Exception as e:
        print(f"Error listing folders: {e}")
    
    # Test uploading a sample PDF
    try:
        test_pdf_path = "te.pdf"  # Create a small test PDF in your backend directory
        
        # Create a simple test PDF if it doesn't exist
        if not os.path.exists(test_pdf_path):
            from reportlab.pdfgen import canvas
            
            c = canvas.Canvas(test_pdf_path)
            c.drawString(100, 750, "Test PDF for Cloudinary")
            c.save()
            print("Created test PDF")
        
        folder = os.getenv('CLOUDINARY_PDF_FOLDER')
        result = cloudinary.uploader.upload(
            test_pdf_path,
            resource_type="raw",
            public_id="test_pdf",
            folder=folder,
            overwrite=True
        )
        print(f"Upload result: {result}")
    except Exception as e:
        print(f"Error uploading test PDF: {e}")
    
    # Test listing resources
    try:
        folder = os.getenv('CLOUDINARY_PDF_FOLDER')
        resources = cloudinary.api.resources(
            resource_type="raw",
            type="upload",
            prefix=folder,
            max_results=500
        )
        print(f"Resources in {folder}: {resources}")
    except Exception as e:
        print(f"Error listing resources: {e}")

if __name__ == "__main__":
    test_cloudinary()