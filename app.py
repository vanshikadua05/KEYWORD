import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import logging
import nltk
from flask import Flask, request, jsonify, render_template
from requests_oauthlib import OAuth2Session
from pymongo import MongoClient

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

from flask import Flask, render_template, request, jsonify
import nlp_utils
import file_utils

# Google OAuth Config
GOOGLE_CLIENT_ID = ""
GOOGLE_CLIENT_SECRET = ""
REDIRECT_URI = "http://localhost:5000/api/callback"

AUTHORIZATION_BASE_URL = ""
TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
USER_INFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")
# Connect to MongoDB
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['vanshikadb']
users_collection = db['users']  # collection = table

googleLogin = {}
from flask import session, redirect, url_for
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users_collection.find_one({'username': username, 'password': password})
        
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if username already exists
        existing_user = users_collection.find_one({'username': username})
        
        if existing_user:
            return render_template('signup.html', error='User already exists')
        
        # Insert new user
        users_collection.insert_one({'username': username, 'password': password})
        
        return redirect(url_for('index'))
    return render_template('signup.html')



@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user', None)
    return redirect(url_for('login'))



@app.route('/')
def index():
    # Handle both normal and Google login users
    if 'username' not in session and 'user' not in session:
        return redirect(url_for('login'))

    # check that user session has email/name
    if 'user' in session:
        user = session['user']
        if not user.get('email') or not user.get('name'):
            return redirect(url_for('login'))

    #  you already have 'username'
    return render_template('index.html', user=session.get('user'))



@app.route('/process', methods=['POST'])
def process_text():
    """Process the text for keyword extraction and topic modeling."""
    try:
        
        data = request.get_json()   #converts the json data into python dictionary (to retrieve data)
        text = data.get('text', '')
        num_keywords = int(data.get('num_keywords', 10))
        num_topics = int(data.get('num_topics', 5))
        min_topic_words = int(data.get('min_topic_words', 5))
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        
        keywords = nlp_utils.extract_keywords(text, num_keywords)
        
   
        topics = nlp_utils.extract_topics(text, num_topics, min_topic_words)
        
    
        stats = nlp_utils.get_text_stats(text)
        
        return jsonify({     #converts python file into json
            'keywords': keywords,
            'topics': topics,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Get a specific analysis by ID."""
    
    return jsonify({'error': 'Analysis not found'}), 404

@app.route('/upload-file', methods=['POST'])
def upload_file():
    """Process uploaded file and extract text for analysis."""
    try:
      
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        uploaded_file = request.files['file']
        
        if uploaded_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
          
        file_data = uploaded_file.read()
        filename = uploaded_file.filename
        
        logger.info(f"Processing uploaded file: {filename}")
        
        try:
            extracted_text = file_utils.extract_text_from_file(file_data, filename)
            
            num_keywords = int(request.form.get('num_keywords', 10))
            num_topics = int(request.form.get('num_topics', 5))
            min_topic_words = int(request.form.get('min_topic_words', 5))
            
            if extracted_text:
                
                keywords = nlp_utils.extract_keywords(extracted_text, num_keywords)
                
                topics = nlp_utils.extract_topics(extracted_text, num_topics, min_topic_words)
                
                stats = nlp_utils.get_text_stats(extracted_text)
                
                return jsonify({
                    'extracted_text': extracted_text,
                    'keywords': keywords,
                    'topics': topics,
                    'stats': stats,
                    'filename': filename
                })
            else:
                return jsonify({'error': 'Failed to extract text from file'}), 400
                
        except ValueError as ve:
            logger.error(f"Invalid file type error: {str(ve)}")
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            return jsonify({'error': f"Error processing file: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"Error handling file upload: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/request', methods=['POST'])
def google_login_request():
    print("Google client id", GOOGLE_CLIENT_ID)
    google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=REDIRECT_URI, scope=["openid", "email", "profile"])
    authorization_url, state = google.authorization_url(AUTHORIZATION_BASE_URL, access_type="offline", prompt="consent")
    session['oauth_state'] = state
    return jsonify({'url': authorization_url})

@app.route('/api/callback')
def google_callback():
    google = OAuth2Session(GOOGLE_CLIENT_ID, state=session['oauth_state'], redirect_uri=REDIRECT_URI)
    print("google", google)
    token = google.fetch_token(TOKEN_URL, client_secret=GOOGLE_CLIENT_SECRET, authorization_response=request.url)

    session['oauth_token'] = token

    google = OAuth2Session(GOOGLE_CLIENT_ID, token=token)
    userinfo = google.get(USER_INFO_URL).json()

    email = userinfo.get('email')
    name = userinfo.get('name')

    # Store user in session
    session['user'] = {
        'email': email,
        'name': name,
        'is_authenticated': True,
        'google_login': True
    }
    # Check if user already exists in MongoDB
    existing_user = users_collection.find_one({'username': email})

    if not existing_user:
       users_collection.insert_one({'username': email, 'password': None, 'name': name, 'google_login': True})

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
