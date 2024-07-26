from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
from langchain_aws import ChatBedrock


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

        # Generate a response using the context (assuming you have a separate function to generate responses)
        response = generate_response(prompt, context)

        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit-feedback/")
async def submit_feedback(request: FeedbackRequest):
    try:
        with open("feedback.txt", "a") as f:
            f.write(f"Response: {request.response_content}\n")
            f.write(f"Rating: {request.rating} stars\n\n")
        return {"message": "Feedback saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_response(prompt, context):
    # Implement your language model call here using context and prompt
    try:
        messages = [
            {"role": "system", "content": "You are a highly knowledgeable AI chatbot designed to provide technical support for a tech company specializing in consumer electronics. Utilizing a Retrieval-Augmented Generation (RAG) approach, you are to act as a troubleshooter based on the information provided. You have access to a comprehensive knowledge base that includes product manuals, FAQ documents, user forums, and help articles. Your primary goal is to assist users in troubleshooting common issues, provide step-by-step guides, and offer information on warranty and repair services. Use only the information available in the provided context to generate responses. If the necessary information is not available, clearly state “Information not available.” If more information is needed to provide an accurate response, ask specific follow-up questions to gather the required details from the user."},
            {"role": "user", "content": f""" Provide detailed instructions based on the specific model, referencing the available product manual and troubleshooting steps. Additionally, suggest contacting customer service or provide warranty information only if such details are explicitly provided in the context.
             
            Information: {context}
            
            question: {prompt} 

            Don't say 'Based on the information provided'
            If answer is available start with 'Happy to help....'  if not say 'Apologies! I don't have information at the moment regarding the question'"""}
        ]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    