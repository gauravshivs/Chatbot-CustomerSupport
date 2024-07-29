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
    model_kwargs=dict(temperature=0.2),
)

def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG)

def create_feedback_table():
    """
    Creates a 'feedback' table in the database if it does not already exist.

    This function establishes a connection to the database and ensures that a table named 'feedback' is present. 
    The 'feedback' table is designed to store user feedback on chatbot responses, including the response content, 
    the rating given by the user, and a timestamp indicating when the feedback was submitted.

    The table schema includes:
    - `id`: A unique identifier for each feedback entry (auto-incremented).
    - `response_content`: The content of the chatbot response being rated.
    - `rating`: The rating given by the user, an integer between 1 and 5 inclusive.
    - `created_at`: A timestamp indicating when the feedback was created, with a default value of the current time.

    Parameters:
    None

    Returns:
    None
    """
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
    history: str
    prompt: str

class FeedbackRequest(BaseModel):
    response_content: str
    rating: int

@app.post("/get-response/")
async def get_response(request: PromptRequest):
    """
    Handles POST requests to generate a response based on user input and conversation history.

    This endpoint accepts a `PromptRequest` containing the conversation history and the current prompt from the user. 
    It performs the following steps:
    1. Extracts the history and prompt from the request.
    2. Encodes the prompt into an embedding using a machine learning model.
    3. Queries a PostgreSQL database for the most similar documents to the prompt using the `pgvector` extension.
    4. Concatenates the retrieved documents to form a context.
    5. Generates a response using the context, history, and prompt.

    Parameters:
    - request (PromptRequest): The incoming request containing the conversation history and user prompt.

    Returns:
    - dict: A dictionary containing the generated response.

    Raises:
    - HTTPException: If an error occurs during processing, returns a 500 status code with the error details.

    Dependencies:
    - The `PromptRequest` data model should define `history` and `prompt` fields.
    - The `model.encode` function should be implemented to convert the prompt into a suitable embedding.
    - The PostgreSQL database must have a table `document_vectors` with document texts and their corresponding embeddings.
    - The `pgvector` extension is used for efficient vector similarity searches.
    - The `generate_response` function should be implemented to create a response based on the provided context, history, and prompt.

    Example:
    When a POST request is made to this endpoint with a prompt and history, the server retrieves similar documents, 
    generates a context, and returns an appropriate response for the given prompt.

    Note:
    - Ensure the PostgreSQL database connection and schema are correctly set up and that the necessary extensions and libraries are installed.
    - Proper error handling should be in place to handle issues such as database connectivity errors, empty responses, or invalid embeddings.
    """
    try:
        history = request.history
        prompt = request.prompt
        prompt_embedding = model.encode(prompt).tolist()

        # Fetch similar texts from the PostgreSQL database using the pgvector extension
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT document FROM document_vectors
                    ORDER BY embedding <=> %s
                    LIMIT 20;
                """, (Json(prompt_embedding),))
                rows = cur.fetchall()

        # Assuming that we concatenate the top documents as context
        context = " ".join([row[0] for row in rows])

        # Generate a response using the context
        response = generate_response(history, prompt, context)

        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit-feedback/")
async def submit_feedback(request: FeedbackRequest):
    """
    Handles POST requests to submit feedback for a chatbot response.

    This endpoint accepts a `FeedbackRequest` containing the response content and the user's rating. It performs the following steps:
    1. Extracts the `response_content` and `rating` from the request.
    2. Inserts this feedback into the `feedback` table in the PostgreSQL database.
    3. Commits the transaction to save the feedback.

    Parameters:
    - request (FeedbackRequest): The incoming request containing `response_content` (text of the response being rated) and `rating` (an integer representing the user's rating).

    Returns:
    - dict: A dictionary with a message indicating that the feedback has been saved.

    Raises:
    - HTTPException: If an error occurs during the database operation, an HTTP 500 status code is returned with the error details.

    Dependencies:
    - The `FeedbackRequest` data model should define `response_content` and `rating` fields.
    - The `get_db_connection` function should provide a valid database connection.
    - The PostgreSQL database must have a `feedback` table with the appropriate schema.

    Example:
    When a POST request is made to this endpoint with feedback data, the server stores the feedback in the database and returns a confirmation message.

    Note:
    - Ensure that the database schema for the `feedback` table includes columns for `response_content` (TEXT) and `rating` (INTEGER).
    - Proper error handling should be in place to manage issues such as database connectivity errors or invalid input data.
    """
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

def generate_response(history, prompt, context):
    """

    This function prepares a list of messages, including system instructions and the user's input, formatted with the
    provided context and history. It then invokes a language model to generate an appropriate response.

    Parameters:
    - history (str): A string representing the past conversation history, used to provide context to the language model.
    - prompt (str): The current prompt or question from the user that requires a response.
    - context (str): Additional context information, such as similar documents or related content, to assist in generating a more accurate response.

    Returns:
    - str: The generated response content from the language model.

    Raises:
    - HTTPException: If an error occurs during the response generation process, an HTTP 500 status code is returned with the error details.

    Dependencies:
    - `CLAUDE_SYSTEM_MESSAGE`: A predefined system message or instruction that sets the behavior or context for the language model.
    - `CLAUDE_USER_MESSAGE`: A template message for the user input, formatted with the context, prompt, and history.
    - `llm.invoke`: The method used to interact with the language model, sending the prepared messages and receiving a response.

    Example:
    The function is typically used in an application where user inputs need to be responded to dynamically. The context and history help in generating a coherent and contextually relevant reply.

    Note:
    - Ensure that `CLAUDE_SYSTEM_MESSAGE` and `CLAUDE_USER_MESSAGE` are correctly defined and accessible in the scope where this function is used.
    - The function assumes that `llm.invoke(messages)` returns an object with a `content` attribute containing the response text.
    """
    try:
        messages = [
            {"role": "system", "content": CLAUDE_SYSTEM_MESSAGE},
            {"role": "user", "content": CLAUDE_USER_MESSAGE.format(context=context, prompt=prompt, history=history)}
        ]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))