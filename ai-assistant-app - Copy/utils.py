import io
import base64
import PyPDF2
from docx import Document
from PIL import Image, ImageEnhance, ImageFilter
import google.generativeai as genai

def compress_pdf(pdf_file):
    """
    Compress a PDF file to reduce its size
    This is a simplified version - real implementation would use more sophisticated methods
    """
    reader = PyPDF2.PdfReader(pdf_file)
    writer = PyPDF2.PdfWriter()
    
    # Copy pages from reader to writer
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        writer.add_page(page)
    
    # Create output PDF
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer

def compress_docx(docx_file):
    """
    Basic compression for Word documents
    This is a simplified version - real implementation would use more sophisticated methods
    """
    doc = Document(docx_file)
    
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer

def enhance_image(image, enhancement_level=1.5, sharpen_level=1.5):
    """
    Enhance image quality by adjusting contrast, brightness, and sharpness
    """
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(enhancement_level)
    
    # Enhance brightness
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(min(enhancement_level, 1.3))  # Don't brighten too much
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(sharpen_level)
    
    # Apply a subtle unsharp mask for additional clarity
    image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    return image

def summarize_text(text, api_key, max_tokens=2048):
    """
    Summarize text using Gemini API
    """
    # Configure Gemini API
    genai.configure(api_key=api_key)
    
    # Create a generative model - use newest Gemini 1.5 model
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Truncate the text if needed
    if len(text) > max_tokens * 5:  # Approximate character count
        text = text[:max_tokens * 5] + "..."
    
    # Generate summary with prompt
    prompt = f"Please provide a concise summary of the following text:\n\n{text}\n\nSummary:"
    response = model.generate_content(prompt)
    
    return response.text

def format_chat_message(message):
    """
    Format messages for better display in the chat interface
    """
    return message.replace('\n', '<br>')

def create_download_link(content, filename, text):
    """
    Create a download link for files
    """
    b64 = base64.b64encode(content).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{text}</a>'
    return href