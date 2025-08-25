import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

def make_cloudinary_pdfs_public():
    """Make all Cloudinary PDFs public"""
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
    folder = os.getenv('CLOUDINARY_PDF_FOLDER', 'student_chatbot/pdfs')
    
    # List all PDFs
    try:
        resources = cloudinary.api.resources(
            resource_type="raw",
            type="upload",
            prefix=folder,
            max_results=500
        )
        
        pdfs = resources.get('resources', [])
        print(f"Found {len(pdfs)} PDFs in {folder}")
        
        # Make each PDF public
        for pdf in pdfs:
            public_id = pdf['public_id']
            print(f"Making {public_id} public...")
            
            # Download the file
            url = pdf['url']
            
            # Re-upload with public access
            result = cloudinary.uploader.explicit(
                public_id,
                resource_type="raw",
                type="upload",
                access_mode="public"
            )
            
            print(f"Updated {public_id}: {result.get('access_mode', 'unknown')}")
            
        print("All PDFs have been made public.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    make_cloudinary_pdfs_public()
