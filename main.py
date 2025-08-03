import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env vars
from app.core.config import settings

# Try to import Slack bot, fallback to REST API only if tokens are missing
try:
    from app.api.v1.slack_bot import api
    slack_enabled = True
except Exception as e:
    print(f"⚠️  Slack integration disabled: {e}")
    print("📡 Starting with REST API only...")
    from app.api.v1.endpoints import api
    slack_enabled = False

if __name__ == "__main__":
    print(f"🚀 Starting Slack Analytics Bot on {settings.app_host}:{settings.app_port}")
    print(f"📊 Database initialized with sample app portfolio data")
    print(f"🤖 LLM service ready with GPT-3.5-turbo")
    
    if slack_enabled:
        print("💬 Slack integration enabled")
        module_path = "app.api.v1.slack_bot:api"
    else:
        print("🌐 REST API only mode")
        module_path = "app.api.v1.endpoints:api"
    
    uvicorn.run(
        module_path,
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level="info"
    )