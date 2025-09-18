# Deployment Guide for Railway and Vercel

This guide explains how to deploy the YouTube Learning AI application with proper token restrictions and API key authentication.

## Railway Backend Deployment

### 1. Environment Variables

Set these environment variables in your Railway project:

#### Required Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# YouTube API (if using YouTube features)
YOUTUBE_API_KEY=your_youtube_api_key_here
```

#### Token Limits (Customize based on your budget)
```bash
# Daily token limit - adjust based on your budget
DAILY_TOKEN_LIMIT=10000

# Hourly token limit - prevents burst usage
HOURLY_TOKEN_LIMIT=1000

# Per-request token limit - prevents expensive single requests
REQUEST_TOKEN_LIMIT=4000

# Text length limits
MAX_TEXT_LENGTH=50000
MAX_QUESTION_LENGTH=1000
```

#### Rate Limiting
```bash
# Requests per time period
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
```

#### API Key Authentication
```bash
# Set to true to require API keys for all requests
REQUIRE_API_KEY=false

# Master API key for admin functions (generate a secure random string)
MASTER_API_KEY=your_secure_master_key_here
```

#### CORS Configuration
```bash
# Allow your frontend domain
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

### 2. Railway Deployment Steps

1. **Connect your GitHub repository to Railway**
2. **Set environment variables** in Railway dashboard
3. **Deploy** - Railway will automatically detect the Python app and use the `Procfile`

### 3. Railway-Specific Considerations

- **Persistent Storage**: Railway provides ephemeral storage. Token usage data will reset on deployment.
- **Memory**: The in-memory rate limiter will reset on deployment.
- **Scaling**: Each instance has its own rate limiting and token tracking.

## Vercel Frontend Deployment

### 1. Environment Variables

Set these in your Vercel project:

```bash
# Backend API URL
VITE_API_URL=https://your-railway-backend.railway.app

# Optional: API key for frontend requests
VITE_API_KEY=your_api_key_here
```

### 2. Vercel Configuration

Create `vercel.json` in your frontend directory:

```json
{
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

## Security Best Practices

### 1. API Key Management

#### For Development
```bash
REQUIRE_API_KEY=false
```

#### For Production
```bash
REQUIRE_API_KEY=true
MASTER_API_KEY=generate_secure_random_string
```

### 2. Token Limits

#### Conservative (Low Budget)
```bash
DAILY_TOKEN_LIMIT=5000
HOURLY_TOKEN_LIMIT=500
REQUEST_TOKEN_LIMIT=2000
```

#### Moderate (Medium Budget)
```bash
DAILY_TOKEN_LIMIT=20000
HOURLY_TOKEN_LIMIT=2000
REQUEST_TOKEN_LIMIT=4000
```

#### Generous (High Budget)
```bash
DAILY_TOKEN_LIMIT=100000
HOURLY_TOKEN_LIMIT=10000
REQUEST_TOKEN_LIMIT=8000
```

### 3. Rate Limiting

#### For Public APIs
```bash
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500
RATE_LIMIT_PER_DAY=5000
```

#### For Private/Internal Use
```bash
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_PER_HOUR=2000
RATE_LIMIT_PER_DAY=20000
```

## Monitoring and Management

### 1. Check Usage Statistics

```bash
curl https://your-railway-backend.railway.app/usage
```

### 2. Create API Keys

```bash
curl -X POST "https://your-railway-backend.railway.app/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-app",
    "permissions": "read",
    "daily_limit": 5000,
    "hourly_limit": 500,
    "expires_days": 30
  }'
```

### 3. List API Keys

```bash
curl https://your-railway-backend.railway.app/api-keys
```

### 4. Reset Daily Usage (Admin)

```bash
curl -X POST https://your-railway-backend.railway.app/usage/reset
```

## Cost Estimation

### Token Costs (OpenAI Pricing)
- **GPT-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Text-embedding-3-small**: ~$0.02 per 1M tokens

### Example Daily Costs
- **5,000 tokens/day**: ~$0.001-0.005 per day
- **20,000 tokens/day**: ~$0.004-0.02 per day
- **100,000 tokens/day**: ~$0.02-0.10 per day

## Troubleshooting

### Common Issues

1. **"Rate limit exceeded" errors**
   - Check your rate limiting settings
   - Consider increasing limits or implementing user-specific rate limiting

2. **"Token limit exceeded" errors**
   - Check your daily/hourly token limits
   - Monitor usage via `/usage` endpoint

3. **"API key required" errors**
   - Set `REQUIRE_API_KEY=false` for development
   - Provide valid API key in requests

4. **CORS errors**
   - Update `ALLOWED_ORIGINS` with your frontend domain
   - Ensure no trailing slashes in URLs

### Monitoring

- Check Railway logs for errors
- Monitor token usage via `/usage` endpoint
- Set up alerts for high usage periods
- Regularly review API key usage

## Production Checklist

- [ ] Set `REQUIRE_API_KEY=true`
- [ ] Generate secure `MASTER_API_KEY`
- [ ] Configure appropriate token limits
- [ ] Set up CORS for your frontend domain
- [ ] Test all endpoints with API keys
- [ ] Monitor usage and costs
- [ ] Set up logging and monitoring
- [ ] Create backup API keys
- [ ] Document API key management process
