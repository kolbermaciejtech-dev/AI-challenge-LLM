import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env vars
from slack_bot import api

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 12000))
    host = os.getenv("APP_HOST", "0.0.0.0")
    
    print(f"🚀 Starting Slack Analytics Bot on {host}:{port}")
    print(f"📊 Database initialized with sample app portfolio data")
    print(f"🤖 LLM service ready with GPT-3.5-turbo")
    
    uvicorn.run(
        "slack_bot:api",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )