# Pascua Baccarat Predictor

A Python-based advanced baccarat prediction application leveraging statistical analysis and pattern recognition.

## Features

- Baccarat game outcome prediction (Player, Banker, Tie)
- User authentication system
- Payment verification system
- Admin panel for user management
- History tracking and analysis

## Deployment Instructions for Streamlit Community Cloud

### Prerequisites

1. GitHub account
2. Firebase service account credentials

### Steps to Deploy

1. Create a public GitHub repository
2. Upload all project files to the repository
3. Make sure you include these files:
   - All Python files (app.py, auth_ui.py, etc.)
   - `.streamlit/config.toml` (already configured correctly)
   - `requirements.txt` (rename streamlit_requirements.txt to requirements.txt)

4. Go to [Streamlit Community Cloud](https://share.streamlit.io/)
5. Sign in with your GitHub account
6. Select your repository and branch
7. Set the main file path to "app.py"
8. Set up your Firebase credentials as secrets:
   - In Settings > Secrets
   - Add "FIREBASE_SERVICE_ACCOUNT" as the key
   - Paste your entire Firebase service account JSON as the value

### Testing

After deployment, verify:
- Login functionality works
- Firebase connection is established
- Payment verification system works properly

## Local Development

To run this app locally:

```bash
streamlit run app.py
```

## Required Environment Variables

- FIREBASE_SERVICE_ACCOUNT: Firebase service account credentials (JSON)

## Dependencies

- streamlit
- firebase-admin
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib
- google-cloud-firestore
- numpy
- pandas
- pytz
- streamlit-extras
- streamlit-option-menu
- cryptography