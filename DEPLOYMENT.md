# Deployment Guide

## Environment Variables

You need to set the following environment variables in your Render dashboard:

### Required Variables

1. **BOT_TOKEN**: Your Telegram bot token from @BotFather
2. **USE_WEBHOOK**: Set to `true` for production (webhook mode)
3. **WEBHOOK_URL**: Your Render app URL (e.g., `https://your-app-name.onrender.com`)

### Optional Variables

- **PORT**: Port number (Render sets this automatically, default is 10000)

## Render Deployment Steps

1. **Stop any local bot instances** to avoid conflicts
   - Make sure no bot is running on your local machine
   - Check for any other deployments using the same bot token

2. **Set Environment Variables in Render**:
   - Go to your Render dashboard
   - Navigate to your service
   - Go to "Environment" tab
   - Add the following variables:
     ```
     BOT_TOKEN=<your_bot_token>
     USE_WEBHOOK=true
     WEBHOOK_URL=https://<your-app-name>.onrender.com
     ```

3. **Deploy**:
   - Render will automatically deploy when you push to your repository
   - Or manually trigger a deploy from the Render dashboard

4. **Verify Deployment**:
   - Check the logs in Render dashboard
   - You should see: "Using webhook mode: https://your-app-name.onrender.com"
   - Test the bot by sending `/start` command in Telegram

## Local Development

For local development, you can use polling mode:

1. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set:
   ```
   BOT_TOKEN=your_bot_token
   USE_WEBHOOK=false
   ```

3. Run the bot:
   ```bash
   python bot.py
   ```

## Troubleshooting

### "Conflict: terminated by other getUpdates request"

This error means multiple bot instances are running. To fix:

1. **Stop all local instances** of the bot
2. **Check Render logs** to ensure only one instance is running
3. **Delete webhook** if switching from webhook to polling:
   ```bash
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook
   ```

### Webhook not receiving updates

1. Verify `WEBHOOK_URL` is correct in environment variables
2. Check Render logs for webhook setup confirmation
3. Ensure your Render app is not sleeping (use a cron job to keep it awake)

### Bot not responding

1. Check Render logs for errors
2. Verify `BOT_TOKEN` is correct
3. Ensure `USE_WEBHOOK=true` is set in production

