# 📧 Email Setup Guide - Car Wash API

This guide will walk you through setting up email authentication for your Car Wash API. The system supports automatic email verification during user registration and password reset functionality.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Provider Setup Guides](#provider-setup-guides)
   - [Gmail SMTP](#gmail-smtp-recommended-for-small-projects)
   - [SendGrid](#sendgrid-recommended-for-production)
   - [AWS SES](#aws-ses-enterprise-solution)
   - [Custom SMTP](#custom-smtp-server)
4. [Configuration Reference](#configuration-reference)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [Production Checklist](#production-checklist)

---

## 🎯 Overview

The email system automatically sends:
- **Verification emails** when users register
- **Password reset emails** when users request password resets
- **Welcome emails** after successful email verification
- **Password change notifications** for security

### Email Flow

```
User Registration → Email Verification → Welcome Email
User Forgot Password → Reset Email → Password Changed Notification
```

---

## 🚀 Quick Start

### 1. Development Mode (No SMTP needed)

For development and testing, the system uses a mock email provider:

```bash
# In your .env file
AUTH_EMAIL_PROVIDER=mock
```

This will log emails to the console instead of sending them.

### 2. Production Mode

For production, configure an SMTP provider:

```bash
# In your .env file
AUTH_EMAIL_PROVIDER=smtp
AUTH_SMTP_HOST=smtp.gmail.com
AUTH_SMTP_PORT=587
AUTH_SMTP_USERNAME=your-email@gmail.com
AUTH_SMTP_PASSWORD=your-app-password
AUTH_SMTP_USE_TLS=true
AUTH_FROM_EMAIL=noreply@yourcompany.com
AUTH_SUPPORT_EMAIL=support@yourcompany.com
AUTH_APP_URL=https://yourcompany.com
```

---

## 🔧 Provider Setup Guides

### Gmail SMTP (Recommended for Small Projects)

Gmail is perfect for development and small production deployments.

#### Step 1: Enable 2-Factor Authentication

1. Go to your [Google Account settings](https://myaccount.google.com)
2. Navigate to **Security** → **2-Step Verification**
3. Enable 2-Factor Authentication

#### Step 2: Generate App Password

1. In Security settings, find **App passwords**
2. Click **Select app** → **Other** → Enter "Car Wash API"
3. Click **Generate**
4. **Save the 16-character password** (you'll need this)

#### Step 3: Configure Environment Variables

```bash
# Add to your .env file
AUTH_EMAIL_PROVIDER=smtp
AUTH_SMTP_HOST=smtp.gmail.com
AUTH_SMTP_PORT=587
AUTH_SMTP_USERNAME=your-gmail@gmail.com
AUTH_SMTP_PASSWORD=abcd-efgh-ijkl-mnop  # 16-character app password
AUTH_SMTP_USE_TLS=true
AUTH_FROM_EMAIL=your-gmail@gmail.com
AUTH_SUPPORT_EMAIL=your-gmail@gmail.com
AUTH_APP_NAME=Car Wash Service
AUTH_APP_URL=https://yourcompany.com
```

#### Step 4: Test Configuration

```bash
python quick_email_test.py
```

**Gmail Limits:**
- 500 emails per day for free accounts
- 2,000 emails per day for Google Workspace accounts

---

### SendGrid (Recommended for Production)

SendGrid is a professional email service with high deliverability.

#### Step 1: Create SendGrid Account

1. Sign up at [SendGrid](https://sendgrid.com)
2. Verify your account via email
3. Complete the setup wizard

#### Step 2: Create API Key

1. Go to **Settings** → **API Keys**
2. Click **Create API Key**
3. Choose **Restricted Access**
4. Grant **Mail Send** permissions
5. Click **Create & View**
6. **Save the API key** (shown only once)

#### Step 3: Verify Sender Identity

1. Go to **Settings** → **Sender Authentication**
2. Choose **Single Sender Verification** (easier) or **Domain Authentication** (better)
3. For Single Sender: Enter your "from" email and verify it
4. For Domain: Follow DNS setup instructions

#### Step 4: Configure Environment Variables

```bash
# Add to your .env file
AUTH_EMAIL_PROVIDER=smtp
AUTH_SMTP_HOST=smtp.sendgrid.net
AUTH_SMTP_PORT=587
AUTH_SMTP_USERNAME=apikey  # Literally "apikey"
AUTH_SMTP_PASSWORD=SG.abcd1234...  # Your SendGrid API key
AUTH_SMTP_USE_TLS=true
AUTH_FROM_EMAIL=noreply@yourcompany.com  # Must be verified
AUTH_SUPPORT_EMAIL=support@yourcompany.com
AUTH_APP_NAME=Car Wash Service
AUTH_APP_URL=https://yourcompany.com
```

#### Step 5: Test Configuration

```bash
python quick_email_test.py
```

**SendGrid Benefits:**
- 100 emails/day free tier
- High deliverability rates
- Detailed analytics
- Professional reputation

---

### AWS SES (Enterprise Solution)

AWS Simple Email Service is perfect for large-scale applications.

#### Step 1: Set Up AWS Account

1. Create an [AWS account](https://aws.amazon.com)
2. Go to the **SES Console**
3. Choose your region (e.g., us-east-1)

#### Step 2: Verify Email/Domain

1. In SES Console, go to **Verified identities**
2. Click **Create identity**
3. Choose **Email address** or **Domain**
4. Follow verification process

#### Step 3: Create SMTP Credentials

1. In SES Console, go to **SMTP settings**
2. Click **Create SMTP credentials**
3. Enter username (e.g., carwash-api-smtp)
4. Click **Create user**
5. **Download credentials** (shown only once)

#### Step 4: Request Production Access

By default, SES is in sandbox mode (can only email verified addresses).

1. Go to **Account dashboard**
2. Click **Request production access**
3. Fill out the form explaining your use case
4. Wait for approval (usually 24-48 hours)

#### Step 5: Configure Environment Variables

```bash
# Add to your .env file
AUTH_EMAIL_PROVIDER=smtp
AUTH_SMTP_HOST=email-smtp.us-east-1.amazonaws.com  # Your region
AUTH_SMTP_PORT=587
AUTH_SMTP_USERNAME=AKIA...  # Your SES SMTP username
AUTH_SMTP_PASSWORD=BCdE...  # Your SES SMTP password
AUTH_SMTP_USE_TLS=true
AUTH_FROM_EMAIL=noreply@yourcompany.com  # Must be verified
AUTH_SUPPORT_EMAIL=support@yourcompany.com
AUTH_APP_NAME=Car Wash Service
AUTH_APP_URL=https://yourcompany.com
```

**AWS SES Benefits:**
- Extremely cost-effective (first 62,000 emails free)
- $0.10 per 1,000 emails after that
- High deliverability
- Scalable to millions of emails

---

### Custom SMTP Server

If you have your own SMTP server or use a different provider:

```bash
# Add to your .env file
AUTH_EMAIL_PROVIDER=smtp
AUTH_SMTP_HOST=mail.yourcompany.com
AUTH_SMTP_PORT=587  # or 25, 465, 2525
AUTH_SMTP_USERNAME=your-username
AUTH_SMTP_PASSWORD=your-password
AUTH_SMTP_USE_TLS=true  # or false for unencrypted
AUTH_FROM_EMAIL=noreply@yourcompany.com
AUTH_SUPPORT_EMAIL=support@yourcompany.com
AUTH_APP_NAME=Car Wash Service
AUTH_APP_URL=https://yourcompany.com
```

**Common SMTP Ports:**
- **587**: STARTTLS (recommended)
- **465**: SSL/TLS
- **25**: Unencrypted (not recommended)

---

## ⚙️ Configuration Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AUTH_EMAIL_PROVIDER` | Provider type | `smtp` or `mock` |
| `AUTH_SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `AUTH_SMTP_PORT` | SMTP server port | `587` |
| `AUTH_SMTP_USERNAME` | SMTP username | `your-email@gmail.com` |
| `AUTH_SMTP_PASSWORD` | SMTP password | `app-password-here` |
| `AUTH_SMTP_USE_TLS` | Use TLS encryption | `true` |
| `AUTH_FROM_EMAIL` | From email address | `noreply@company.com` |
| `AUTH_SUPPORT_EMAIL` | Support contact | `support@company.com` |
| `AUTH_APP_URL` | Your app URL | `https://yourapp.com` |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTH_APP_NAME` | App name in emails | `Car Wash Service` |
| `AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS` | Verification link expiry | `24` |
| `AUTH_EMAIL_VERIFICATION_RATE_LIMIT_MINUTES` | Resend rate limit | `5` |
| `AUTH_PASSWORD_RESET_EXPIRE_HOURS` | Reset link expiry | `2` |
| `AUTH_PASSWORD_RESET_RATE_LIMIT_HOURS` | Reset rate limit | `1` |

---

## 🧪 Testing

### 1. Test Email Service

```bash
python quick_email_test.py
```

### 2. Test Complete Registration Flow

```bash
# Start the API
python main.py

# In another terminal, test registration
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### 3. Check Logs

Look for email sending confirmation in the logs:
```
INFO:src.shared.services.email_service:[MOCK EMAIL] To: test@example.com, Subject: Verify Your Email
```

### 4. Test Email Templates

Templates are located in `src/shared/services/templates/`:
- `email_verification.html` - User registration verification
- `password_reset.html` - Password reset requests
- `welcome.html` - Welcome after verification

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Authentication failed" Error

**Symptoms:** SMTP authentication errors
**Solutions:**
- Verify username/password are correct
- For Gmail: Use App Password, not regular password
- For SendGrid: Username must be exactly "apikey"
- Check if 2FA is enabled (required for Gmail)

#### 2. "Connection refused" Error

**Symptoms:** Cannot connect to SMTP server
**Solutions:**
- Verify SMTP host and port
- Check firewall settings
- Ensure TLS settings match server requirements
- Try different ports (587, 465, 25)

#### 3. Emails Not Being Received

**Symptoms:** No errors but emails don't arrive
**Solutions:**
- Check spam/junk folders
- Verify sender email is authenticated
- For AWS SES: Ensure production access is approved
- Check email provider limits

#### 4. "Email not verified" Errors

**Symptoms:** SendGrid/SES rejects emails
**Solutions:**
- Complete sender verification process
- For domains: Set up DNS records
- Wait for verification to complete

### Debug Mode

Enable detailed logging:

```bash
# Add to your .env file
LOGGING_LOG_LEVEL=DEBUG
AUTH_ENABLE_SECURITY_LOGGING=true
```

### Testing with Different Providers

You can switch providers easily:

```bash
# Development
AUTH_EMAIL_PROVIDER=mock

# Testing with Gmail
AUTH_EMAIL_PROVIDER=smtp
AUTH_SMTP_HOST=smtp.gmail.com

# Production with SendGrid
AUTH_EMAIL_PROVIDER=smtp
AUTH_SMTP_HOST=smtp.sendgrid.net
```

---

## ✅ Production Checklist

### Before Going Live

- [ ] **SMTP Provider Configured**
  - [ ] API keys/passwords secured
  - [ ] Sender email verified
  - [ ] Domain authentication set up (if using)
  - [ ] Production access approved (AWS SES)

- [ ] **Email Templates Tested**
  - [ ] Verification emails working
  - [ ] Password reset emails working
  - [ ] Welcome emails working
  - [ ] Branding and links correct

- [ ] **Security Settings**
  - [ ] Strong SMTP passwords
  - [ ] TLS encryption enabled
  - [ ] Rate limiting configured
  - [ ] Environment variables secured

- [ ] **Monitoring**
  - [ ] Email sending logs monitored
  - [ ] Delivery rates tracked
  - [ ] Error alerting set up
  - [ ] Bounce handling configured

### Environment Variables Checklist

```bash
# Required for production
AUTH_EMAIL_PROVIDER=smtp
AUTH_SMTP_HOST=your-smtp-host
AUTH_SMTP_PORT=587
AUTH_SMTP_USERNAME=your-username
AUTH_SMTP_PASSWORD=your-secure-password
AUTH_SMTP_USE_TLS=true
AUTH_FROM_EMAIL=noreply@yourcompany.com
AUTH_SUPPORT_EMAIL=support@yourcompany.com
AUTH_APP_URL=https://yourcompany.com

# Recommended
AUTH_APP_NAME=Your App Name
LOGGING_LOG_LEVEL=INFO
AUTH_ENABLE_SECURITY_LOGGING=true
```

### Performance Considerations

- **Gmail**: Good for development, limited for production
- **SendGrid**: 100 emails/day free, then $15/month for 40K emails
- **AWS SES**: $0.10 per 1,000 emails after 62K free emails
- **Custom SMTP**: Depends on your server capabilities

---

## 🎉 Success!

Once configured, your API will automatically:

1. **Send verification emails** when users register
2. **Send password reset emails** when requested
3. **Send welcome emails** after verification
4. **Send security notifications** for password changes

Your users will receive professional, branded emails that enhance their experience with your Car Wash API! 🚗✨

---

## 💡 Need Help?

- Check the [Troubleshooting](#troubleshooting) section
- Review logs with `LOGGING_LOG_LEVEL=DEBUG`
- Test with `python quick_email_test.py`
- Ensure all environment variables are set correctly