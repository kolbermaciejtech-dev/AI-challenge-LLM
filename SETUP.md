# Slack Analytics Bot - Setup Guide

This guide will walk you through setting up the Slack Analytics Bot from scratch.

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone <repository-url>
cd AI-challenge-LLM
pip install -r requirements.txt
```

### 2. Test Core Functionality (No API Keys Required)

```bash
# Run the mock test suite
python test_bot_mock.py

# Try the interactive demo
python demo.py
```

### 3. Configure for Production

Copy the environment template:
```bash
cp .env.example .env
```

Edit `.env` with your credentials (see sections below).

## 📱 Slack App Setup

### Step 1: Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. App Name: `Analytics Bot`
4. Select your workspace
5. Click **"Create App"**

### Step 2: Configure Bot Permissions

1. Go to **"OAuth & Permissions"** in the sidebar
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add these scopes:
   - `app_mentions:read`
   - `channels:history`
   - `chat:write`
   - `im:history`
   - `im:read`
   - `im:write`

### Step 3: Enable Events

1. Go to **"Event Subscriptions"** in the sidebar
2. Toggle **"Enable Events"** to **ON**
3. **Request URL**: `https://your-domain.com/slack/events`
   - You'll need to deploy the app first (see deployment section)
4. **Subscribe to bot events**:
   - `app_mention`
   - `message.channels`
   - `message.im`

### Step 4: Install to Workspace

1. Go to **"Install App"** in the sidebar
2. Click **"Install to Workspace"**
3. Authorize the app
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
5. Go to **"Basic Information"** → **"App Credentials"**
6. Copy the **"Signing Secret"**

### Step 5: Update Environment Variables

Add to your `.env` file:
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

## 🤖 OpenAI API Setup

### Step 1: Get API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Go to **API Keys** section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### Step 2: Add to Environment

```env
OPENAI_API_KEY=sk-your-api-key-here
```

### Step 3: Set Up Billing (Important!)

- OpenAI requires a paid account for API access
- Add payment method in your OpenAI account
- Set usage limits to control costs

## 🔍 LangSmith Setup (Optional)

LangSmith provides observability for LLM operations.

### Step 1: Create Account

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Sign up for an account
3. Create a new project

### Step 2: Get API Key

1. Go to **Settings** → **API Keys**
2. Create a new API key
3. Copy the key

### Step 3: Configure Environment

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=slack-analytics-bot
```

## 🚀 Deployment Options

### Option 1: Local Development with ngrok

For testing and development:

1. **Install ngrok**: [ngrok.com](https://ngrok.com)
2. **Run the bot**:
   ```bash
   python main.py
   ```
3. **Expose to internet**:
   ```bash
   ngrok http 12000
   ```
4. **Update Slack Event URL** with the ngrok URL:
   ```
   https://your-ngrok-id.ngrok.io/slack/events
   ```

### Option 2: Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t slack-analytics-bot .
   ```

2. **Run with docker-compose**:
   ```bash
   docker-compose up -d
   ```

### Option 3: Cloud Deployment

#### Heroku
```bash
# Install Heroku CLI
heroku create your-app-name
heroku config:set SLACK_BOT_TOKEN=your-token
heroku config:set SLACK_SIGNING_SECRET=your-secret
heroku config:set OPENAI_API_KEY=your-key
git push heroku main
```

#### Railway
```bash
# Install Railway CLI
railway login
railway init
railway add
railway deploy
```

#### DigitalOcean App Platform
1. Connect your GitHub repository
2. Set environment variables in the dashboard
3. Deploy automatically

## ✅ Verification Steps

### 1. Test Core Functionality
```bash
python test_bot_mock.py
```
Should show all tests passing.

### 2. Test API Connections
```bash
python test_bot.py
```
Should connect to OpenAI and LangSmith (if configured).

### 3. Test Slack Integration

1. **Invite bot to channel**:
   ```
   /invite @Analytics Bot
   ```

2. **Test basic query**:
   ```
   @Analytics Bot how many apps do we have?
   ```

3. **Test complex query**:
   ```
   @Analytics Bot which country generates the most revenue?
   ```

4. **Test CSV export**:
   ```
   @Analytics Bot show top apps by installs
   export this as csv
   ```

5. **Test SQL request**:
   ```
   @Analytics Bot total revenue by platform
   show me the sql
   ```

## 🔧 Troubleshooting

### Common Issues

#### "Invalid Auth" Error
- Check your `SLACK_BOT_TOKEN` is correct
- Ensure the bot is installed in your workspace
- Verify the token starts with `xoxb-`

#### "Request URL Failed" Error
- Ensure your app is running and accessible
- Check the ngrok tunnel is active
- Verify the URL in Slack matches your endpoint

#### "OpenAI Quota Exceeded"
- Add payment method to OpenAI account
- Check your usage limits
- Consider using the mock service for testing

#### "Database Not Found"
- The database is created automatically on first run
- Check file permissions in the app directory
- Verify SQLite is available

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

### Health Check

Check if the app is running:
```bash
curl http://localhost:12000/health
```

## 📊 Usage Examples

### Simple Questions
- "How many apps do we have?"
- "What's the total revenue?"
- "Which platform is more popular?"

### Complex Analysis
- "Which country generates the most revenue?"
- "List all iOS apps sorted by popularity"
- "Show apps with biggest UA spend change"
- "Compare iOS vs Android performance"

### Special Commands
- "export this as csv" (after any query)
- "show me the sql" (after any query)
- "help" (show available commands)

## 🔒 Security Notes

- Never commit API keys to version control
- Use environment variables for all secrets
- Implement rate limiting in production
- Monitor API usage and costs
- Regularly rotate API keys

## 📈 Monitoring

### Key Metrics to Track
- Query response times
- OpenAI API usage and costs
- Error rates
- User engagement
- Database performance

### Recommended Tools
- LangSmith for LLM observability
- Application monitoring (New Relic, DataDog)
- Log aggregation (ELK stack, Splunk)
- Uptime monitoring (Pingdom, UptimeRobot)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review application logs
3. Test with the mock service first
4. Verify all environment variables are set
5. Check API quotas and billing

For additional help, refer to:
- [Slack API Documentation](https://api.slack.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [LangChain Documentation](https://python.langchain.com/)