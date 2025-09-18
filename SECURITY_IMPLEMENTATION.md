# Security Implementation Summary

This document summarizes the comprehensive security and cost control measures implemented for the YouTube Learning AI application.

## 🛡️ Security Features Implemented

### 1. Token Usage Restrictions
- **Daily Limits**: Configurable daily token consumption limits
- **Hourly Limits**: Prevents burst usage that could overwhelm the system
- **Per-Request Limits**: Prevents extremely expensive single requests
- **Text Length Limits**: Prevents abuse through oversized inputs
- **Real-time Tracking**: Persistent storage of usage statistics

### 2. Rate Limiting
- **Per-Minute Limits**: Configurable requests per minute
- **Per-Hour Limits**: Configurable requests per hour  
- **Per-Day Limits**: Configurable requests per day
- **Client Identification**: Based on API key or IP address
- **Automatic Cleanup**: Memory-efficient with automatic cleanup

### 3. API Key Authentication
- **Optional Authentication**: Can be enabled/disabled via environment variable
- **Master Key Support**: Environment-based master key for admin functions
- **Key Management**: Create, list, and revoke API keys
- **Permission System**: Role-based access control (read, admin)
- **Expiration Support**: API keys can have expiration dates
- **Per-Key Limits**: Individual token limits per API key

### 4. Monitoring & Alerting
- **Usage Monitoring**: Real-time tracking of token consumption
- **Alert System**: Configurable thresholds for warnings and critical alerts
- **Performance Monitoring**: Tracks slow requests and errors
- **Alert Storage**: Persistent storage of alerts with cleanup
- **Multiple Alert Levels**: Info, warning, error, critical

## 🚀 Deployment Configuration

### Railway Backend
- **Procfile**: Configured for Railway deployment
- **railway.json**: Railway-specific configuration
- **Environment Variables**: Comprehensive configuration template
- **Health Checks**: Built-in health check endpoint

### Vercel Frontend
- **vercel.json**: Vercel deployment configuration
- **Environment Variables**: API URL and key configuration
- **Static Build**: Optimized for Vercel's static build system

## 📊 Cost Control Features

### Token Limits (Configurable)
```bash
# Conservative (Low Budget)
DAILY_TOKEN_LIMIT=5000
HOURLY_TOKEN_LIMIT=500
REQUEST_TOKEN_LIMIT=2000

# Moderate (Medium Budget)  
DAILY_TOKEN_LIMIT=20000
HOURLY_TOKEN_LIMIT=2000
REQUEST_TOKEN_LIMIT=4000

# Generous (High Budget)
DAILY_TOKEN_LIMIT=100000
HOURLY_TOKEN_LIMIT=10000
REQUEST_TOKEN_LIMIT=8000
```

### Rate Limiting (Configurable)
```bash
# For Public APIs
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500
RATE_LIMIT_PER_DAY=5000

# For Private/Internal Use
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_PER_HOUR=2000
RATE_LIMIT_PER_DAY=20000
```

## 🔧 API Endpoints

### Public Endpoints
- `GET /health` - Health check
- `GET /usage` - Usage statistics
- `POST /subtitles/extract` - Extract subtitles
- `POST /summarize` - Summarize text
- `POST /rag/ingest` - Ingest text chunks
- `POST /rag/ask` - Ask questions

### Admin Endpoints (Require API Key)
- `POST /usage/reset` - Reset daily usage
- `GET /api-keys` - List API keys
- `POST /api-keys` - Create API key
- `DELETE /api-keys/{name}` - Revoke API key
- `GET /monitoring/alerts` - Get alerts
- `POST /monitoring/cleanup` - Clean up old alerts

## 🎯 Frontend Features

### Usage Statistics Display
- Real-time usage tracking
- Visual progress bars
- Daily/hourly usage breakdown
- Remaining token display
- Automatic refresh every 30 seconds

### API Key Support
- Automatic API key inclusion in requests
- Environment variable configuration
- Error handling for authentication failures

## 🔒 Security Best Practices

### For Development
```bash
REQUIRE_API_KEY=false
DAILY_TOKEN_LIMIT=10000
HOURLY_TOKEN_LIMIT=1000
```

### For Production
```bash
REQUIRE_API_KEY=true
MASTER_API_KEY=generate_secure_random_string
DAILY_TOKEN_LIMIT=50000
HOURLY_TOKEN_LIMIT=5000
```

## 📈 Monitoring & Alerts

### Alert Types
- **Token Usage Alerts**: When approaching daily/hourly limits
- **Rate Limiting Alerts**: When clients approach rate limits
- **Performance Alerts**: For slow requests (>5 seconds)
- **Error Alerts**: For API errors (4xx/5xx status codes)
- **High Usage Alerts**: For requests using >10k tokens

### Alert Levels
- **Info**: General information and high usage notifications
- **Warning**: Approaching limits or performance issues
- **Error**: API errors and failures
- **Critical**: Limit exceeded or system issues

## 💰 Cost Estimation

### Token Costs (OpenAI Pricing)
- **GPT-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Text-embedding-3-small**: ~$0.02 per 1M tokens

### Example Daily Costs
- **5,000 tokens/day**: ~$0.001-0.005 per day
- **20,000 tokens/day**: ~$0.004-0.02 per day
- **100,000 tokens/day**: ~$0.02-0.10 per day

## 🚀 Quick Start

### 1. Deploy Backend to Railway
1. Connect GitHub repository to Railway
2. Set environment variables from `env.example`
3. Deploy automatically

### 2. Deploy Frontend to Vercel
1. Connect GitHub repository to Vercel
2. Set `VITE_API_BASE` to your Railway URL
3. Optionally set `VITE_API_KEY` for authentication
4. Deploy automatically

### 3. Configure Security
1. Set `REQUIRE_API_KEY=true` for production
2. Generate secure `MASTER_API_KEY`
3. Adjust token limits based on budget
4. Monitor usage via `/usage` endpoint

## 🔍 Troubleshooting

### Common Issues
1. **"Rate limit exceeded"**: Increase rate limits or implement user-specific limiting
2. **"Token limit exceeded"**: Increase token limits or monitor usage
3. **"API key required"**: Set `REQUIRE_API_KEY=false` for development
4. **CORS errors**: Update `ALLOWED_ORIGINS` with frontend domain

### Monitoring Commands
```bash
# Check usage
curl https://your-railway-backend.railway.app/usage

# Create API key
curl -X POST "https://your-railway-backend.railway.app/api-keys" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "permissions": "read", "daily_limit": 5000}'

# Check alerts
curl https://your-railway-backend.railway.app/monitoring/alerts
```

## 📋 Production Checklist

- [ ] Set `REQUIRE_API_KEY=true`
- [ ] Generate secure `MASTER_API_KEY`
- [ ] Configure appropriate token limits
- [ ] Set up CORS for frontend domain
- [ ] Test all endpoints with API keys
- [ ] Monitor usage and costs
- [ ] Set up logging and monitoring
- [ ] Create backup API keys
- [ ] Document API key management process

## 🎉 Benefits

1. **Cost Control**: Prevents runaway costs through multiple limit layers
2. **Abuse Prevention**: Rate limiting and authentication prevent misuse
3. **Transparency**: Real-time usage tracking and monitoring
4. **Flexibility**: Configurable limits for different deployment scenarios
5. **Reliability**: Health checks and error monitoring
6. **Scalability**: Designed to work with Railway and Vercel's scaling

This implementation provides comprehensive protection against cost overruns and abuse while maintaining ease of use and deployment flexibility.
