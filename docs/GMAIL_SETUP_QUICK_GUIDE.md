# 🚀 Gmail SMTP Quick Setup Guide

**Get email verification working in 5 minutes!**

## Step 1: Enable 2-Factor Authentication

1. Go to [Google Account Settings](https://myaccount.google.com)
2. Click **Security** in the left menu
3. Find **2-Step Verification** and turn it ON
4. Follow the setup process (you'll need your phone)

## Step 2: Generate App Password

1. Still in Security settings, scroll to **App passwords**
2. Click **App passwords** (you might need to sign in again)
3. Select app: **Other (Custom name)**
4. Type: **Car Wash API**
5. Click **Generate**
6. **COPY THE 16-CHARACTER PASSWORD** (like: `abcd efgh ijkl mnop`)
7. Click **Done**

## Step 3: Update Your .env File

```bash
# Add these lines to your .env file
AUTH_EMAIL_PROVIDER=smtp
AUTH_SMTP_HOST=smtp.gmail.com
AUTH_SMTP_PORT=587
AUTH_SMTP_USERNAME=your-gmail@gmail.com
AUTH_SMTP_PASSWORD=abcd-efgh-ijkl-mnop  # The 16-char app password
AUTH_SMTP_USE_TLS=true
AUTH_FROM_EMAIL=your-gmail@gmail.com
AUTH_SUPPORT_EMAIL=your-gmail@gmail.com
AUTH_APP_NAME=Car Wash Service
AUTH_APP_URL=https://yourcompany.com
```

## Step 4: Test It

```bash
# Test the email system
python quick_email_test.py

# Start the API
python main.py

# Test registration (in another terminal)
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-test@gmail.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

## Step 5: Check Your Email!

You should receive a beautiful verification email with:
- Your app branding
- Secure verification link
- Professional styling

## ✅ Done!

Your email verification is now working! Users will automatically receive:
- **Verification emails** when they register
- **Password reset emails** when they forget passwords
- **Welcome emails** after verification
- **Security notifications** for password changes

## 🚨 Important Notes

- **Never use your regular Gmail password** - only use the 16-character App Password
- **Keep the App Password secure** - treat it like a password
- **Free Gmail accounts** have a limit of 500 emails per day
- **Google Workspace accounts** can send up to 2,000 emails per day

## 🔧 Troubleshooting

**"Authentication failed"?**
- Make sure you're using the App Password, not your regular password
- Check that 2FA is enabled
- Verify the email address is correct

**"Connection refused"?**
- Check your internet connection
- Verify the SMTP settings are correct
- Make sure TLS is enabled

**Emails not arriving?**
- Check the spam/junk folder
- Make sure the recipient email is valid
- Check Gmail's sending limits

## 🚀 Next Steps

For production use, consider upgrading to:
- **SendGrid** (100 emails/day free, then $15/month)
- **AWS SES** ($0.10 per 1,000 emails)
- **Google Workspace** (higher limits)

Happy emailing! 📧✨