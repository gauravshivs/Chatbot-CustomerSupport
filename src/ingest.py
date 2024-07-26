import os
import PyPDF2
from sentence_transformers import SentenceTransformer
import psycopg2
import argparse

# Function to extract text from a PDF file using PyPDF2
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

# Function to extract text from a TXT file
def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

# Function to split text by paragraphs
def split_text_by_paragraphs(text):
    # Split the text by double new lines (paragraphs)
    paragraphs = text.split('\n\n')
    # Strip leading/trailing whitespace from each paragraph
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs

# Function to connect to the PostgreSQL database and insert data
def insert_into_db(documents, embeddings):
    conn = psycopg2.connect(
        dbname="document_search", 
        user="gaurav.shivhare", 
        password="your_password",  # replace with actual password
        host="localhost", 
        port="5432"
    )
    cursor = conn.cursor()

    # Create vector extension if it doesn't exist
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()

    # Create table with vector(384) type if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS document_vectors (
        id SERIAL PRIMARY KEY,
        document TEXT,
        embedding vector(384)
    );
    ''')
    conn.commit()

    # Insert data into the table
    for doc, vec in zip(documents, embeddings):
        # Convert numpy array to list before insertion
        cursor.execute(
            "INSERT INTO document_vectors (document, embedding) VALUES (%s, %s)",
            (doc, vec.tolist())  # vec.tolist() converts numpy array to list
        )
    conn.commit()

    cursor.close()
    conn.close()

def main(file_paths):
    # Separate files by extension
    pdf_files = [f for f in file_paths if f.lower().endswith('.pdf')]
    txt_files = [f for f in file_paths if f.lower().endswith('.txt')]

    # Extract text from PDF and TXT files
    texts = []
    for pdf_path in pdf_files:
        texts.append(extract_text_from_pdf(pdf_path))

    for txt_path in txt_files:
        texts.append(extract_text_from_txt(txt_path))

    # Split the texts by paragraphs
    split_texts = []
    for text in texts:
        split_texts.extend(split_text_by_paragraphs(text))

    # Load the SentenceTransformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Generate embeddings for the split texts
    embeddings = model.encode(split_texts)

    # Insert split texts and their embeddings into the database
    insert_into_db(split_texts, embeddings)

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process PDF and TXT files and store embeddings in PostgreSQL.")
    parser.add_argument('file_paths', metavar='F', type=str, nargs='+', help='Paths to PDF and TXT files')
    args = parser.parse_args()

    main(args.file_paths)