# Render.com Deployment Guide

## Quick Deploy to Render.com (FREE)

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub (recommended for auto-deploy)

### Step 2: Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `selvar2/sample-workflow`
3. Select the `workflow2` branch

### Step 3: Configure Service
| Setting | Value |
|---------|-------|
| **Name** | `servicenow-incident-processor` |
| **Region** | Choose nearest to you |
| **Branch** | `workflow2` |
| **Root Directory** | `servicenow-mcp` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && pip install -r web_ui/requirements.txt` |
| **Start Command** | `cd web_ui && gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120 app:app` |
| **Plan** | `Free` |

### Step 4: Add Environment Variables
In the Render dashboard, add these environment variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `SERVICENOW_INSTANCE_URL` | `https://dev282453.service-now.com` | Your ServiceNow instance |
| `SERVICENOW_USERNAME` | Your username | Keep secret |
| `SERVICENOW_PASSWORD` | Your password | Keep secret |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | Your AWS key | Keep secret |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret | Keep secret |
| `REDSHIFT_DATABASE` | `dev` | Database name |
| `REDSHIFT_DB_USER` | `awsuser` | Database user |

### Step 5: Deploy
1. Click **"Create Web Service"**
2. Wait for build to complete (~2-3 minutes)
3. Your app will be live at: `https://servicenow-incident-processor.onrender.com`

---

## Alternative: One-Click Deploy

You can also use the `render.yaml` Blueprint:
1. Go to Render Dashboard
2. Click **"New +"** → **"Blueprint"**
3. Select your repository
4. Render will auto-detect `render.yaml`
5. Add your secret environment variables
6. Deploy!

---

## After Deployment

### Your Public URL
```
https://servicenow-incident-processor.onrender.com
```

### Features Available
- ✅ Process incidents from anywhere
- ✅ Monitor ServiceNow incidents
- ✅ HTTPS secured
- ✅ Auto-deploys on git push
- ✅ Free SSL certificate

### Notes
- Free tier spins down after 15 min inactivity
- First request after sleep takes ~30 seconds
- 750 free hours/month (enough for always-on)

---

## Troubleshooting

### View Logs
- Go to Render Dashboard → Your Service → "Logs"

### Check Health
- Visit: `https://your-app.onrender.com/api/status`

### Redeploy
- Push to GitHub, or
- Click "Manual Deploy" in Render Dashboard
