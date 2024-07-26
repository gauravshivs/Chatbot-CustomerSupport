from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
from langchain_aws import ChatBedrock
from src.prompts import CLAUDE_SYSTEM_MESSAGE, CLAUDE_USER_MESSAGE

# FastAPI app initialization
app = FastAPI()

# Database connection configuration
DATABASE_CONFIG = {
    "dbname": "document_search",
    "user": "gaurav.shivhare",
    "host": "localhost",
    "port": "5432"
}

# AWS Bedrock Configuration
model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# Initialize the ChatBedrock model
llm = ChatBedrock(
    model_id=model_id,
    model_kwargs=dict(temperature=0),
)

def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG)

def create_feedback_table():
    # Ensure the feedback table exists
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    response_content TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

# Create feedback table if it does not exist
create_feedback_table()

# Initialize SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Pydantic models for request and response
class PromptRequest(BaseModel):
    prompt: str

class FeedbackRequest(BaseModel):
    response_content: str
    rating: int

@app.post("/get-response/")
async def get_response(request: PromptRequest):
    try:
        prompt = request.prompt
        prompt_embedding = model.encode(prompt).tolist()

        # Fetch similar texts from the PostgreSQL database using the pgvector extension
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT document FROM document_vectors
                    ORDER BY embedding <-> %s
                    LIMIT 20;
                """, (Json(prompt_embedding),))
                rows = cur.fetchall()

        # Assuming that we concatenate the top documents as context
        context = " ".join([row[0] for row in rows])

        # Generate a response using the context
        response = generate_response(prompt, context)

        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit-feedback/")
async def submit_feedback(request: FeedbackRequest):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO feedback (response_content, rating)
                    VALUES (%s, %s)
                """, (request.response_content, request.rating))
            conn.commit()
        return {"message": "Feedback saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_response(prompt, context):
    try:
        messages = [
            {"role": "system", "content": CLAUDE_SYSTEM_MESSAGE},
            {"role": "user", "content": CLAUDE_USER_MESSAGE.format(context=context, prompt=prompt)}
        ]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))