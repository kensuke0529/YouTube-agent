# Token Usage Restrictions

This document explains how token usage is restricted and managed in the YouTube Learning AI application to control costs and prevent abuse.

## Overview

The application implements comprehensive token usage restrictions to:
- **Control costs** by limiting daily/hourly token consumption
- **Prevent abuse** by setting per-request limits
- **Provide transparency** with real-time usage tracking
- **Ensure reliability** by preventing system overload

## Token Limits

### Daily Limits
- **Default**: 10,000 tokens per day
- **Configurable**: Set via `DAILY_TOKEN_LIMIT` environment variable
- **Reset**: Automatically resets at midnight
- **Purpose**: Prevents excessive daily spending

### Hourly Limits
- **Default**: 1,000 tokens per hour
- **Configurable**: Set via `HOURLY_TOKEN_LIMIT` environment variable
- **Purpose**: Prevents burst usage that could overwhelm the system

### Per-Request Limits
- **Default**: 4,000 tokens per request
- **Configurable**: Set via `REQUEST_TOKEN_LIMIT` environment variable
- **Purpose**: Prevents extremely large requests that could be expensive

### Text Length Limits
- **General text**: 50,000 characters maximum
- **Questions**: 1,000 characters maximum
- **Configurable**: Set via `MAX_TEXT_LENGTH` and `MAX_QUESTION_LENGTH`

## How It Works

### 1. Request Validation
Before making any API call to OpenAI:
1. **Text length check**: Ensures input doesn't exceed character limits
2. **Token estimation**: Roughly estimates token usage (1 token ≈ 4 characters)
3. **Limit checking**: Verifies request won't exceed daily/hourly/request limits
4. **Error response**: Returns HTTP 429 (Too Many Requests) if limits exceeded

### 2. Usage Tracking
After successful API calls:
1. **Actual usage recording**: Records real token usage from OpenAI responses
2. **Persistent storage**: Saves usage data to `data/token_usage.json`
3. **Real-time updates**: Updates usage statistics immediately

### 3. Frontend Display
The UI shows:
- **Current usage**: Daily token consumption with progress bar
- **Remaining tokens**: How many tokens are left for the day
- **Breakdown**: Prompt vs completion vs embedding tokens
- **Visual indicators**: Color-coded progress bar (green/orange/red)

## Configuration

### Environment Variables

```bash
# Token Limits
DAILY_TOKEN_LIMIT=10000       # Daily token limit
HOURLY_TOKEN_LIMIT=1000       # Hourly token limit  
REQUEST_TOKEN_LIMIT=4000      # Per-request limit

# Text Length Limits
MAX_TEXT_LENGTH=50000         # Maximum text length
MAX_QUESTION_LENGTH=1000      # Maximum question length

# Storage
TOKEN_STORAGE_FILE=data/token_usage.json  # Usage data file
```

### Recommended Settings

#### For Development
```bash
DAILY_TOKEN_LIMIT=10000       # Current default for development
HOURLY_TOKEN_LIMIT=1000       # Current default for development
REQUEST_TOKEN_LIMIT=2000      # Smaller request limit for testing
```

#### For Production
```bash
DAILY_TOKEN_LIMIT=50000       # Higher daily limit for production
HOURLY_TOKEN_LIMIT=5000       # Higher hourly limit for production
REQUEST_TOKEN_LIMIT=4000      # Standard request limit
```

## API Endpoints

### Get Usage Statistics
```http
GET /usage
```

Response:
```json
{
  "total_tokens": 1500,
  "prompt_tokens": 800,
  "completion_tokens": 600,
  "embedding_tokens": 100,
  "daily_limit": 10000,
  "hourly_limit": 1000,
  "request_limit": 4000,
  "daily_remaining": 8500,
  "last_reset": "2024-01-15T00:00:00"
}
```

### Reset Daily Usage (Admin)
```http
POST /usage/reset
```

Response:
```json
{
  "message": "Daily usage reset successfully"
}
```

## Error Handling

### HTTP Status Codes
- **400 Bad Request**: Text too long or invalid input
- **429 Too Many Requests**: Token limits exceeded
- **500 Internal Server Error**: API or processing errors

### Error Messages
- `"Text too long. Maximum allowed: 50000 characters"`
- `"Daily token limit exceeded (10000). Current usage: 9500"`
- `"Hourly token limit exceeded (1000). Current hourly usage: 950"`
- `"Request token limit exceeded (4000). Estimated tokens: 5000"`

## Cost Estimation

### Token Costs (OpenAI Pricing)
- **GPT-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Text-embedding-3-small**: ~$0.02 per 1M tokens

### Example Costs
- **10,000 tokens/day**: ~$0.002-0.01 per day depending on input/output ratio
- **Typical video summary**: ~2,000-5,000 tokens (~$0.001-0.003)
- **Typical Q&A**: ~500-1,500 tokens (~$0.0005-0.001)

## Best Practices

### For Users
1. **Use quick summaries** for initial overviews
2. **Ask specific questions** rather than broad ones
3. **Check usage stats** before making large requests
4. **Break up large videos** into smaller chunks if needed

### For Administrators
1. **Monitor usage patterns** via the `/usage` endpoint
2. **Adjust limits** based on actual usage and budget
3. **Set up alerts** for high usage periods
4. **Regular cleanup** of old usage data if needed

## Troubleshooting

### Common Issues

#### "Token limit exceeded" errors
- **Cause**: Daily/hourly/request limits reached
- **Solution**: Wait for reset or increase limits
- **Prevention**: Monitor usage and adjust limits proactively

#### "Text too long" errors
- **Cause**: Input exceeds character limits
- **Solution**: Break text into smaller chunks
- **Prevention**: Implement text chunking in frontend

#### High costs despite limits
- **Cause**: Limits set too high or inefficient prompts
- **Solution**: Lower limits and optimize prompts
- **Prevention**: Regular cost monitoring and optimization

### Monitoring
- Check `/usage` endpoint regularly
- Monitor `data/token_usage.json` file
- Set up logging for token usage events
- Track cost trends over time

## Future Enhancements

- **User-specific limits**: Different limits per user/session
- **Rate limiting**: More sophisticated rate limiting
- **Cost alerts**: Email/SMS notifications for high usage
- **Usage analytics**: Detailed usage reports and trends
- **Dynamic limits**: Adjust limits based on usage patterns
