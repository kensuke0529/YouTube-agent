# Railway Pre-Deploy Command Fix

## 🚨 Issue: Pre-Deploy Command Still Running

Even though we removed the pre-deploy command from the configuration, Railway is still trying to run one. This means it's set in your Railway project settings.

## 🔧 Fix Required: Update Railway Dashboard

### Step 1: Go to Railway Dashboard
1. Open your Railway project: `youtube-extracter`
2. Click on **Settings** tab
3. Scroll down to **Deploy** section

### Step 2: Remove Pre-Deploy Command
1. Find **Pre Deploy Command** field
2. **Clear the field completely** (remove any text)
3. Click **Save**

### Step 3: Verify Configuration
Your deploy settings should look like this:
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health`
- **Pre Deploy Command**: (empty/blank)
- **Build Command**: (empty/blank - auto-detect)

## 📋 Alternative: Use Procfile Only

If Railway settings are still causing issues, you can:

### Option 1: Remove railway.json entirely
```bash
# Delete the railway.json file
rm backend/railway.json
```

### Option 2: Railway will use Procfile
Railway will automatically detect and use your `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 🚀 Manual Railway Settings Fix

### In Railway Dashboard:

1. **Go to your project settings**
2. **Deploy section:**
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/health`
   - Pre Deploy Command: (leave empty)
   - Build Command: (leave empty)

3. **Environment section:**
   - Make sure you have all required environment variables set
   - `OPENAI_API_KEY`
   - `YOUTUBE_API_KEY` (if using YouTube features)
   - Other variables from `env.example`

## 🔍 Current File Configuration

### `railway.json` (Updated)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "preDeployCommand": null
  }
}
```

### `runtime.txt`
```
python-3.10.12
```

### `requirements.txt`
```
fastapi==0.112.2
uvicorn[standard]==0.30.6
pydantic==2.9.2
httpx==0.27.2
python-dotenv==1.0.1
beautifulsoup4==4.12.3
yt-dlp==2025.1.12
openai==1.51.2
faiss-cpu>=1.8.0
numpy==1.26.4
```

## 🎯 Expected Result

After removing the pre-deploy command:
- ✅ Build phase completes successfully
- ✅ No pre-deploy command runs
- ✅ Application starts with startCommand
- ✅ Health check passes at `/health`

## 🚨 If Still Failing

### Check Railway Logs
1. Go to your failed deployment
2. Check **Deploy Logs** for specific errors
3. Look for any remaining pre-deploy commands

### Nuclear Option: Fresh Deploy
1. Delete the Railway project
2. Create a new project
3. Connect your GitHub repository
4. Set environment variables
5. Deploy without any custom commands

## 📞 Support

If issues persist:
1. Check Railway's [deployment troubleshooting guide](https://docs.railway.app/troubleshooting)
2. Join Railway's Discord for community support
3. Contact Railway support directly

The key is to **remove the pre-deploy command from Railway dashboard settings**! 🚀
