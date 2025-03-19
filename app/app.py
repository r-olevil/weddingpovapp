from flask import Flask, render_template, request, redirect, url_for, session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pickle

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure random key

# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRETS_FILE = 'client_secrets.json'
FOLDER_ID = 'your-google-drive-folder-id'  # Replace with your folder ID

def get_drive_service():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))
    credentials = pickle.loads(session['credentials'])
    return build('drive', 'v3', credentials=credentials)

@app.route('/')
def index():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))
    return render_template('index.html', folder_id=FOLDER_ID)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    
    drive_service = get_drive_service()
    file_metadata = {
        'name': file.filename,
        'parents': [FOLDER_ID]
    }
    media = MediaFileUpload(file.stream, resumable=True)
    drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    return redirect(url_for('index'))

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)
    session['credentials'] = pickle.dumps(flow.credentials)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)