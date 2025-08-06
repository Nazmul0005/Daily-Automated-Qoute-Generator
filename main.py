from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import json
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Daily Quote Generator", version="1.0.0")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class QuoteResponse(BaseModel):
    quote: str
    author: str
    category: str
    generated_at: str

class QuoteRequest(BaseModel):
    category: Optional[str] = "inspirational"
    style: Optional[str] = "motivational"

@app.get("/")
async def root():
    return {"message": "Daily Quote Generator API", "endpoints": ["/generate-quote", "/health"]}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/generate-quote", response_model=QuoteResponse)
async def generate_quote(request: QuoteRequest = QuoteRequest()):
    try:
        # Create a prompt for OpenAI
        prompt = f"""Generate a {request.style} {request.category} quote.
        
        Please respond in this exact JSON format:
        {{
            "quote": "The actual quote text here",
            "author": "Author Name (can be 'Anonymous' if original)",
            "category": "{request.category}"
        }}
        
        Make it inspiring and meaningful."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a wise quote generator. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.8
        )

        # Parse the response
        quote_data = json.loads(response.choices[0].message.content.strip())
        
        # Add timestamp
        quote_data["generated_at"] = datetime.now().isoformat()
        
        return QuoteResponse(**quote_data)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse AI response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quote: {str(e)}")

@app.get("/quote-of-the-day")
async def get_daily_quote():
    """Generate today's special quote"""
    try:
        prompt = """Generate a unique inspirational quote for today.
        
        Please respond in this exact JSON format:
        {
            "quote": "The actual quote text here",
            "author": "Author Name (can be 'Anonymous' if original)",
            "category": "daily-inspiration"
        }
        
        Make it particularly meaningful and uplifting for someone starting their day."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a wise quote generator creating daily inspiration. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.9
        )

        quote_data = json.loads(response.choices[0].message.content.strip())
        quote_data["generated_at"] = datetime.now().isoformat()
        quote_data["date"] = datetime.now().strftime("%Y-%m-%d")
        
        return quote_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating daily quote: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)