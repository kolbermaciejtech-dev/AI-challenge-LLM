# Slack Analytics Bot - AI Engineer Challenge

A sophisticated Slack chatbot for data analytics and business intelligence that answers questions about mobile app portfolio performance using natural language processing and SQL generation.

## 🚀 Features

- **Natural Language to SQL**: Converts user questions into SQL queries using GPT-3.5-turbo
- **Smart Response Formatting**: Automatically determines when to show simple answers vs detailed tables
- **CSV Export**: Users can export query results as downloadable CSV files
- **SQL Query Retrieval**: Users can request the SQL statements used for their queries
- **Query Caching**: Optimizes token usage by caching recent queries
- **Off-topic Detection**: Politely declines non-analytics questions
- **Conversation Context**: Maintains session context for follow-up requests
- **LangSmith Integration**: Full observability and tracing of LLM operations

## 📊 Database Schema

The bot works with a comprehensive app portfolio database containing:

- **App Name**: Mobile app names (TikTok, Instagram, WhatsApp, etc.)
- **Platform**: iOS or Android
- **Date**: Daily metrics timestamps
- **Country**: Geographic performance data (US, UK, Germany, etc.)
- **Installs**: App download counts
- **In-App Revenue**: Revenue from in-app purchases
- **Ads Revenue**: Advertisement revenue
- **UA Cost**: User acquisition costs

## 🛠 Technology Stack

- **Backend**: FastAPI + Python 3.12
- **Slack Integration**: Slack SDK for Python + Slack Bolt
- **LLM**: OpenAI GPT-3.5-turbo via LangChain 0.3.x
- **Database**: SQLite (easily scalable to PostgreSQL)
- **Observability**: LangSmith for LLM tracing
- **Data Processing**: Pandas for CSV exports and data manipulation

## 📋 Prerequisites

- Python 3.12+
- Slack workspace with admin access
- OpenAI API key
- LangSmith account (optional, for observability)

## 🔧 Installation & Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd AI-challenge-LLM
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-api-key-here

# LangSmith Configuration (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=slack-analytics-bot
```

### 3. Slack App Setup

1. **Create a Slack App**:
   - Go to [api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Name: "Analytics Bot", select your workspace

2. **Configure Bot Permissions**:
   - Go to "OAuth & Permissions"
   - Add these Bot Token Scopes:
     - `app_mentions:read`
     - `channels:history`
     - `chat:write`
     - `im:history`
     - `im:read`
     - `im:write`

3. **Enable Events**:
   - Go to "Event Subscriptions"
   - Enable Events: ON
   - Request URL: `https://your-domain.com/slack/events`
   - Subscribe to Bot Events:
     - `app_mention`
     - `message.channels`
     - `message.im`

4. **Install to Workspace**:
   - Go to "Install App"
   - Click "Install to Workspace"
   - Copy the "Bot User OAuth Token" to your `.env` file

### 4. Run the Application

```bash
python main.py
```

The bot will start on `http://0.0.0.0:12000` with:
- Slack event endpoint: `/slack/events`
- Health check: `/health`
- CSV download: `/download/{file_id}`

### 5. Expose to Internet (for Slack Events)

For development, use ngrok or similar:

```bash
ngrok http 12000
```

Update your Slack app's Request URL with the ngrok URL.

## 💬 Usage Examples

### Simple Questions
```
User: how many apps do we have?
Bot: We have 15 apps in our portfolio.

User: export this as csv
Bot: ✅ Data exported successfully!
```

### Complex Analysis
```
User: which country generates the most revenue?
Bot: Based on the data, the US generates the highest total revenue with $2.3M, 
     followed by Germany ($1.8M) and UK ($1.5M). This analysis includes both 
     in-app and ads revenue across all apps and platforms.

[Displays formatted table with country revenue breakdown]
```

### SQL Requests
```
User: show me the sql
Bot: Here's the SQL query I used:

```sql
SELECT country, 
       SUM(in_app_revenue + ads_revenue) as total_revenue
FROM app_metrics 
GROUP BY country 
ORDER BY total_revenue DESC
```

### Off-topic Handling
```
User: what's the weather today?
Bot: I'm focused on helping with app portfolio analytics. Please ask questions 
     about our mobile apps, their performance, revenue, or user metrics.
```

## 🏗 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Slack User    │───▶│   FastAPI App    │───▶│  LLM Service    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Session Manager  │    │ OpenAI GPT-3.5  │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ SQLite Database  │    │   LangSmith     │
                       └──────────────────┘    └─────────────────┘
```

## 🔍 Key Components

### 1. LLM Service (`llm_service.py`)
- Natural language to SQL conversion
- Query relevance detection
- Response formatting logic
- Query caching for cost optimization

### 2. Database Manager (`database.py`)
- SQLite database with sample data generation
- Schema management
- Query execution with error handling

### 3. Slack Bot (`slack_bot.py`)
- Slack event handling
- Session management
- CSV export functionality
- Message formatting for Slack

### 4. Session Management
- Maintains conversation context
- Stores recent queries and results
- Enables follow-up commands (CSV export, SQL requests)

## 🚦 Testing

### Manual Testing Commands

```bash
# Test database initialization
python -c "from database import db_manager; print(len(db_manager.get_sample_data(10)))"

# Test LLM service
python -c "from llm_service import llm_service; print(llm_service.is_relevant_query('how many apps?'))"

# Test SQL generation
python -c "from llm_service import llm_service; print(llm_service.generate_sql_query('total revenue'))"
```

### Health Check
```bash
curl http://localhost:12000/health
```

## 📈 Production Roadmap

### Phase 1: Security & Scalability
- [ ] User authentication and role-based access control
- [ ] Rate limiting and usage quotas
- [ ] PostgreSQL migration for production scale
- [ ] Redis for session management and caching
- [ ] Input validation and SQL injection prevention

### Phase 2: Enhanced Analytics
- [ ] Advanced visualization generation
- [ ] Scheduled reports and alerts
- [ ] Custom dashboard creation
- [ ] Data export to BI tools (Tableau, PowerBI)
- [ ] Real-time data streaming integration

### Phase 3: AI Improvements
- [ ] Fine-tuned models for domain-specific queries
- [ ] Multi-turn conversation improvements
- [ ] Predictive analytics capabilities
- [ ] Natural language report generation
- [ ] Automated insight discovery

### Phase 4: Enterprise Features
- [ ] Multi-tenant architecture
- [ ] Audit logging and compliance
- [ ] Advanced user management
- [ ] Custom data source connectors
- [ ] API for external integrations

## 🔒 Security Considerations

- **SQL Injection Prevention**: Query sanitization and parameterization
- **Access Control**: User-level permissions (planned)
- **Data Privacy**: Secure handling of sensitive business metrics
- **API Security**: Rate limiting and authentication
- **Audit Trail**: Complete logging of all queries and actions

## 🚀 CI/CD Pipeline (Planned)

```yaml
# .github/workflows/deploy.yml
- Code quality checks (black, flake8, mypy)
- Unit and integration tests
- Security scanning
- Docker containerization
- Automated deployment to staging/production
- Database migration management
```

## 📊 Monitoring & Observability

- **LangSmith**: LLM query tracing and performance monitoring
- **Application Metrics**: Response times, error rates, usage patterns
- **Database Monitoring**: Query performance and optimization
- **Cost Tracking**: OpenAI API usage and optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

This project is part of the AI Engineer Challenge for Rounds.

## 🆘 Support

For questions or issues:
- Check the troubleshooting section in this README
- Review application logs
- Contact the development team

---

**Built with ❤️ for the Rounds AI Engineer Challenge**