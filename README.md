# weddingpovapp

Let’s create a web application for uploading wedding day pictures, where guests can share their point-of-view (POV) photos to a central Google Drive folder. It’ll use Python, Flask, Docker, and be deployed on GCP Compute Engine. The app will be functional and aesthetically pleasing with a simple upload button.

---

### Project: Wedding Day POV Photo Upload App

#### Overview
- **Frontend**: Clean HTML with an upload button and wedding-themed styling.
- **Backend**: Flask with Google Drive API to upload photos.
- **Storage**: Google Drive folder (central repository).
- **Container**: Dockerized app.
- **Deployment**: GCP Compute Engine.

---

### Step 1: Set Up Google Drive API

1. **Enable Google Drive API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Create a project (e.g., `wedding-photos`) or use an existing one.
   - Navigate to **APIs & Services** → **Library**, search for "Google Drive API," and enable it.

2. **Create OAuth 2.0 Credentials**:
   - Go to **APIs & Services** → **Credentials**.
   - Click **Create Credentials** → **OAuth 2.0 Client IDs**.
   - Application type: **Web Application**.
   - Authorized redirect URIs: `http://localhost:5000/oauth2callback` (for local testing).
   - Download the JSON file (rename it to `client_secrets.json`) and save it in `wedding-photos/app/`.

3. **Create a Shared Google Drive Folder**:
   - In Google Drive, create a folder (e.g., "Wedding POV Photos").
   - Share it: Right-click → **Share** → "Anyone with the link can edit" (or restrict to guests’ emails later).
   - Note the folder ID from the URL: `https://drive.google.com/drive/folders/[FOLDER-ID]`.

---

### Step 2: Set Up the Project Locally

#### Directory Structure
```
wedding-photos/
├── app/
│   ├── static/
│   │   └── css/
│   │       └── style.css
│   ├── templates/
│   │   └── index.html
│   ├── app.py
│   ├── client_secrets.json  # From Google Cloud
│   └── token.json         # Will be generated after authentication
├── Dockerfile
└── requirements.txt
```

1. Create the directory structure:
   ```bash
   mkdir -p wedding-photos/app/static/css wedding-photos/app/templates
   cd wedding-photos
   ```

---

### Step 3: Write the Flask Application

#### `app/app.py`
```python
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
```

#### `app/templates/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wedding Day POV Photos</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Share Your Wedding Day Moments</h1>
        <p>Upload your photos to our shared album!</p>
        <form method="post" action="{{ url_for('upload_file') }}" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required>
            <button type="submit">Upload Photo</button>
        </form>
        <p><a href="https://drive.google.com/drive/folders/{{ folder_id }}" target="_blank">View Photos on Google Drive</a></p>
    </div>
</body>
</html>
```

#### `app/static/css/style.css`
```css
body {
    font-family: 'Arial', sans-serif;
    background-color: #f9f1f0;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 600px;
    margin: 0 auto;
    text-align: center;
    background-color: #fff;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

h1 {
    color: #d66c7e;
    font-size: 2.5em;
    margin-bottom: 10px;
}

p {
    color: #555;
    font-size: 1.2em;
    margin: 10px 0;
}

input[type="file"] {
    margin: 20px 0;
    display: block;
    width: 100%;
}

button {
    background-color: #d66c7e;
    color: white;
    padding: 12px 25px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1.1em;
}

button:hover {
    background-color: #b55a67;
}

a {
    color: #d66c7e;
    text-decoration: none;
    font-weight: bold;
}

a:hover {
    text-decoration: underline;
}
```

#### `requirements.txt`
```
Flask==2.3.3
google-auth-oauthlib==1.0.0
google-auth-httplib2==0.1.0
google-api-python-client==2.70.0
```

---

### Step 4: Containerize the App with Docker

#### `Dockerfile`
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 5000

CMD ["python", "app.py"]
```

#### Build and Test Locally
1. Build the Docker image:
   ```bash
   docker build -t wedding-photos-app .
   ```
2. Run the container:
   ```bash
   docker run -p 5000:5000 -v $(pwd)/app:/app wedding-photos-app
   ```
   - The `-v` ensures `token.json` persists locally during testing.
3. Open `http://localhost:5000`:
   - Authorize with Google the first time.
   - Upload a photo and check Google Drive.

---

### Step 5: Deploy to GCP Compute Engine

#### Prerequisites
- GCP account and project set up.
- Google Cloud SDK installed (`gcloud` CLI).
- Docker installed locally.

#### Procedure
1. **Push to Google Container Registry (GCR)**:
   - Tag the image:
     ```bash
     docker tag wedding-photos-app gcr.io/[PROJECT-ID]/wedding-photos-app
     ```
     Replace `[PROJECT-ID]` with your GCP project ID.
   - Authenticate with GCP:
     ```bash
     gcloud auth configure-docker
     ```
   - Push the image:
     ```bash
     docker push gcr.io/[PROJECT-ID]/wedding-photos-app
     ```

2. **Create a Compute Engine VM**:
   - Go to GCP Console → Compute Engine → Create Instance.
   - Name: `wedding-photos-vm`.
   - Machine type: `e2-micro`.
   - Boot disk: Ubuntu 20.04 LTS.
   - Firewall: Allow HTTP traffic (port 80) and add a rule for port 5000.
   - Create the VM.

3. **SSH into the VM**:
   ```bash
   gcloud compute ssh wedding-photos-vm --project=[PROJECT-ID]
   ```

4. **Install Docker on the VM**:
   ```bash
   sudo apt update
   sudo apt install -y docker.io
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker $USER
   # Log out and back in, or run `newgrp docker`
   ```

5. **Pull and Run the Container**:
   - Pull the image:
     ```bash
     docker pull gcr.io/[PROJECT-ID]/wedding-photos-app
     ```
   - Run with a volume for `token.json`:
     ```bash
     docker run -d -p 5000:5000 -v /mnt/app:/app gcr.io/[PROJECT-ID]/wedding-photos-app
     ```
   - Create the directory: `sudo mkdir -p /mnt/app`.

6. **Update OAuth Redirect URI**:
   - In Google Cloud Console → **Credentials**, edit the OAuth 2.0 Client ID.
   - Add a new redirect URI: `http://[EXTERNAL-IP]:5000/oauth2callback` (find the external IP in Compute Engine).

7. **Access the App**:
   - Get the VM’s external IP from GCP Console.
   - Visit `http://[EXTERNAL-IP]:5000`, authorize with Google, and upload photos.

---

### Step 6: Verify and Use
- Guests can visit the URL, upload photos, and they’ll appear in the Google Drive folder.
- The link on the page directs them to view the shared album.

---

### Notes
- **Security**: Currently, the app requires the VM runner to authenticate. For guest access without individual logins, consider:
  - Using a service account (stored securely) instead of OAuth.
  - Restricting the Drive folder to invited guests’ emails.
- **Aesthetics**: The pastel wedding theme (soft pinks and whites) makes it visually appealing.
- **HTTPS**: For production, set up a domain and SSL via GCP Load Balancer.

This creates a central repository on Google Drive for all guests’ POV wedding photos. Let me know if you need adjustments or additional features!
