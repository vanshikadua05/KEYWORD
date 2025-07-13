#to extract texts from the uploaded file in pdf,docx, xlsx, csv format.(convert text into plain text for further processing)
import os
import logging
import tempfile  
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import csv


logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_data):
    """Extract text from a PDF file."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name
        
        pdf_reader = PdfReader(tmp_path)
        text = ""
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
       
        os.unlink(tmp_path)
        
        if not text.strip():
            logger.warning("PDF file contains no extractable text (might be scanned or protected)")
            return "No text could be extracted from this PDF. It might be scanned or protected."
        
        return text.strip()
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def extract_text_from_docx(file_data):
    """Extract text from a Word document."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name
        
        doc = Document(tmp_path)
        text = "\n\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text])
        
      
        os.unlink(tmp_path)
        
        if not text.strip():
            logger.warning("Word document contains no text")
            return "No text could be extracted from this Word document."
        
        return text.strip()
    
    except Exception as e:
        logger.error(f"Error extracting text from Word document: {str(e)}")
        raise Exception(f"Failed to extract text from Word document: {str(e)}")

def extract_text_from_txt(file_data):
    """Extract text from a plain text file."""
    try:
        text = file_data.decode('utf-8', errors='replace')
        return text.strip()
    
    except Exception as e:
        logger.error(f"Error reading text file: {str(e)}")
        raise Exception(f"Failed to read text file: {str(e)}")

def extract_text_from_csv(file_data):
    """Extract text from a CSV file."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name
        
        text = ""
        with open(tmp_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            for row in reader:
                text += " ".join(row) + "\n"
        
        os.unlink(tmp_path)
        
        if not text.strip():
            logger.warning("CSV file contains no text")
            return "No text could be extracted from this CSV file."
        
        return text.strip()
    
    except Exception as e:
        logger.error(f"Error extracting text from CSV file: {str(e)}")
        raise Exception(f"Failed to extract text from CSV file: {str(e)}")

def extract_text_from_excel(file_data):
    """Extract text from an Excel file."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name
        
        excel_file = pd.ExcelFile(tmp_path)
        text = ""
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            sheet_text = f"\n--- Sheet: {sheet_name} ---\n"
            sheet_text += df.to_string(index=False) + "\n\n"
            
            text += sheet_text
    
        os.unlink(tmp_path)
        
        if not text.strip():
            logger.warning("Excel file contains no text data")
            return "No text could be extracted from this Excel file."
        
        return text.strip()
    
    except Exception as e:
        logger.error(f"Error extracting text from Excel file: {str(e)}")
        raise Exception(f"Failed to extract text from Excel file: {str(e)}")

def extract_text_from_file(file_data, filename):
    
    try:
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension == '.pdf':
            return extract_text_from_pdf(file_data)
        elif file_extension == '.docx':
            return extract_text_from_docx(file_data)
        elif file_extension == '.txt':
            return extract_text_from_txt(file_data)
        elif file_extension == '.csv':
            return extract_text_from_csv(file_data)
        elif file_extension in ['.xlsx', '.xls']:
             return extract_text_from_excel(file_data)

        else:
            error_msg = f"Unsupported file type: {file_extension}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        raise Exception(f"Failed to process file: {str(e)}")