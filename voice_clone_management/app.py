import streamlit as st
import librosa
import numpy as np
import pickle
import eyed3
import os
import platform
import tempfile
import pyaudio
import soundfile as sf
import time
import wave
import base64

# Set page configuration
st.set_page_config(
    page_title="VoClo - Voice Cloning Manager",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
VOICES_DIR = "cloned_voices"
RECORDED_DIR = "recorded_voices"
os.makedirs(VOICES_DIR, exist_ok=True)
os.makedirs(RECORDED_DIR, exist_ok=True)

# Configure ffmpeg path for Windows
if platform.system() == 'Windows':
    AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
    AudioSegment.ffmpeg = r"C:\ffmpeg\bin\ffmpeg.exe"
    AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"

def load_css():
    st.markdown("""
    <style>
        /* Modern Elite Application Color Scheme */
        :root {
            --primary-color: #2563EB;           /* Vibrant blue */
            --primary-light: #DBEAFE;           /* Light blue for backgrounds */
            --primary-dark: #1E40AF;            /* Dark blue for hover states */
            --secondary-color: #4B5563;         /* Medium gray for text */
            --background-color: #F8FAFC;        /* Off-white background */
            --card-background: #F0F0F0;         /* Pure white for cards FFFFFF */
            --text-color: #1E293B;              /* Dark slate for text 1E293B */
            --text-light: #64748B;              /* Light slate for secondary text 64748B */
            --border-color: #E2E8F0;            /* Light gray for borders */
            --sidebar-bg: #F0F0F0;              /* Dark background for sidebar */
            --sidebar-text: #F8FAFC;            /* Light text for sidebar */
            --sidebar-highlight: #3B82F6;       /* Highlight for active sidebar item */
            --success-color: #10B981;           /* Green */
            --error-color: #EF4444;             /* Red */
            --warning-color: #F59E0B;           /* Amber */
        }
        
        /* Global styles */
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            font-size: 16px;
            line-height: 1.5;
        }
        
        /* Main container styling */
        .main .block-container {
            padding: 2rem 1rem 1rem 1rem;
            max-width: 100%;
        }
        
        /* Make main content area white with shadow */
        .stApp {
            background-color: var(--background-color);
        }
        
        /* SIDEBAR STYLING - Complete redesign */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-bg) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1) !important;
        }
        
        [data-testid="stSidebar"] > div:first-child {
            background-color: var(--sidebar-bg) !important;
            padding: 2rem 1rem;
        }
        
        /* Fixed radio button labels in sidebar */
        .stRadio > div {
            background-color: var(--sidebar-bg) !important;
        }
        
        .stRadio > div > div {
            background-color: transparent !important;
        }
        
        .stRadio > div > div > label {
            color: var(--sidebar-text) !important;
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            transition: all 0.2s ease;
            border-left: 3px solid transparent;
            background-color: rgba(255, 255, 255, 0.05);
        }
        
        /* Make radio label text explicitly visible */
        .stRadio [data-testid="stMarkdownContainer"] {
            color: var(--sidebar-text) !important;
            font-weight: 500;
        }
        
        .stRadio > div > div > label:hover {
            background-color: rgba(255, 255, 255, 0.1);
            border-left: 3px solid var(--sidebar-highlight);
        }
        
        /* Custom styling for checked radio items */
        .stRadio input[type="radio"]:checked + div {
            color: white !important;
        }
        
        /* Sidebar markdown text */
        [data-testid="stSidebar"] [data-testid="stMarkdown"] {
            color: var(--sidebar-text) !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdown"] p {
            color: var(--sidebar-text) !important;
        }
        
        /* Bottom info in sidebar */
        [data-testid="stSidebar"] > div:first-child > div:last-child {
            margin-top: auto;
            padding-top: 1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.7) !important;
        }
        
        /* NAVBAR STYLING - Polished with shadow */
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 1.5rem;
            background-color: var(--card-background);
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
            border-radius: 0.5rem;
        }
        
        .navbar-logo {
            display: flex;
            align-items: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary-color);
            letter-spacing: -0.5px;
        }
        
        .navbar-menu {
            display: flex;
            align-items: center;
        }
        
        .navbar-item {
            margin-left: 1.5rem;
            text-decoration: none;
            color: var(--text-color);
            font-weight: 500;
            font-size: 0.875rem;
            transition: color 0.2s;
            position: relative;
            padding: 0.5rem 0;
        }
        
        .navbar-item:hover {
            color: var(--primary-color);
        }
        
        .navbar-item:hover:after {
            content: '';
            position: absolute;
            left: 0;
            bottom: 0;
            width: 100%;
            height: 2px;
            background-color: var(--primary-color);
            transition: width 0.2s ease;
        }
        
        .logout-btn {
            background-color: var(--primary-color);
            color: white !important;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.3s;
            margin-left: 1.5rem;
            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
        }
        
        .logout-btn:hover {
            background-color: var(--primary-dark);
            box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
        }
        
        /* Section styling */
        .section-card {
            background-color: var(--card-background);
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-color);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
        }
        
        .section-title {
            color: var(--primary-color);
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.75rem;
            display: flex;
            align-items: center;
        }
        
        .section-title:before {
            content: '';
            display: inline-block;
            width: 4px;
            height: 1rem;
            background-color: var(--primary-color);
            margin-right: 0.5rem;
            border-radius: 2px;
        }
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-color);
            font-weight: 600;
            letter-spacing: -0.025em;
            margin-bottom: 1rem;
        }
        
        p {
            color: var(--text-color);
            margin-bottom: 1rem;
        }
        
        small, .text-muted {
            color: var(--text-light);
        }
        
        /* Button styling */
        .stButton > button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 0.375rem;
            padding: 0.5rem 1rem;
            font-weight: 500;
            font-size: 0.875rem;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
        }
        
        .stButton > button:hover {
            background-color: var(--primary-dark);
            box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3) !important;
            transform: translateY(-1px);
        }
        
        .stButton > button:active {
            transform: translateY(0px);
        }
        
        /* Make download buttons distinct */
        .stDownloadButton > button {
            background-color: var(--success-color);
            color: white;
            border-radius: 0.375rem;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2) !important;
        }
        
        .stDownloadButton > button:hover {
            background-color: #0D9488;
            box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3) !important;
        }
        
        /* Form elements */
        .stTextInput > div > div > input, 
        .stTextArea > div > div > textarea {
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            padding: 0.625rem 0.75rem;
            background-color: white;
            color: var(--text-color);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus, 
        .stTextArea > div > div > textarea:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
        }
        
        .stTextInput > div > label, 
        .stTextArea > div > label {
            color: var(--text-color);
            font-weight: 500;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }
        
        /* Selectbox styling - improved visibility */
        .stSelectbox > div {
            color: var(--text-color);
        }
        
        .stSelectbox > div > div > div {
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            padding: 0.5rem 0.75rem;
            background-color: white;
            color: var(--text-color) !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            font-size: 0.9rem;
        }
        
        .stSelectbox > div [data-testid="stMarkdownContainer"] p {
            color: var(--text-color) !important;
        }
        
        .stSelectbox > div > div > div > div {
            color: var(--text-color) !important;
        }
        
        /* File uploader */
        [data-testid="stFileUploader"] {
            background-color: white;
            border: 1px dashed var(--border-color);
            border-radius: 0.5rem;
            padding: 1rem;
            transition: all 0.2s ease;
        }
        
        [data-testid="stFileUploader"]:hover {
            background-color: var(--primary-light);
            border-color: var(--primary-color);
        }
        
        /* Slider styling */
        [data-testid="stSlider"] > div {
            padding: 1rem 0;
        }
        
        [data-testid="stSlider"] > div > div > div > div {
            background-color: var(--primary-color);
        }
        
        /* Status messages */
        .stSuccess, div[data-baseweb="notification"] {
            color: var(--success-color);
            background-color: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--success-color);
            border-radius: 0.375rem;
            padding: 0.75rem 1rem;
        }
        
        .stError {
            color: var(--error-color);
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--error-color);
            border-radius: 0.375rem;
            padding: 0.75rem 1rem;
        }
        
        .stInfo {
            color: var(--primary-color);
            background-color: rgba(37, 99, 235, 0.1);
            border: 1px solid var(--primary-color);
            border-radius: 0.375rem;
            padding: 0.75rem 1rem;
        }
        
        .stWarning {
            color: var(--warning-color);
            background-color: rgba(245, 158, 11, 0.1);
            border: 1px solid var(--warning-color);
            border-radius: 0.375rem;
            padding: 0.75rem 1rem;
        }
        
        /* Progress bar */
        .stProgress > div > div > div {
            background-color: var(--primary-color);
        }
        
        /* Table styling */
        table {
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            margin: 1rem 0;
            border-radius: 0.5rem;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }
        
        th {
            background-color: var(--primary-light);
            color: var(--primary-dark);
            font-weight: 600;
            padding: 0.75rem 1rem;
            text-align: left;
            font-size: 0.875rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        td {
            padding: 0.75rem 1rem;
            color: var(--text-color);
            border-bottom: 1px solid var(--border-color);
            font-size: 0.875rem;
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        tr:nth-child(even) {
            background-color: rgba(241, 245, 249, 0.5);
        }
        
        tr:hover {
            background-color: var(--primary-light);
        }
        
        /* Audio player */
        audio {
            width: 100%;
            margin: 0.75rem 0;
            border-radius: 0.375rem;
            background-color: var(--primary-light);
        }
        
        /* Classification result formatting */
        h3 span {
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            display: inline-block;
            font-color: var(--text-color);
        }
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 2.5rem;
            border-radius: 0.375rem 0.375rem 0 0;
            padding: 0 1rem;
            background-color: #f1f5f9;
            border: 1px solid var(--border-color);
            border-bottom: none;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: white;
            border-color: var(--border-color);
            border-bottom: none;
        }
        
        .stTabs [data-baseweb="tab-panel"] {
            background-color: white;
            border: 1px solid var(--border-color);
            border-radius: 0 0.375rem 0.375rem 0.375rem;
            padding: 1rem;
        }
        
        /* Profile name visibility improvements */
        .profile-name {
            background-color: var(--primary-light);
            color: var(--primary-dark);
            padding: 0.75rem 1rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
            font-weight: 600;
            font-color: var(--primary-dark);
            border-left: 4px solid var(--primary-color);
        }
        
        /* Voice profile styling */
        .voice-profile {
            margin-bottom: 1.5rem;
            padding: 1rem;
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            background-color: #FAFAFA;
        }
        
        /* Improved device selection */
        .device-selector {
            background-color: white;
            padding: 0.75rem;
            border-radius: 0.5rem;
            border: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }
        
        .device-selector h4 {
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .device-selector .stSelectbox [data-testid="stMarkdownContainer"] p {
            color: var(--text-color) !important;
        }

                /* File uploader styling */
        [data-testid="stFileUploader"] {
            background-color: #F0F0F0; /* Change background color */
            border: 2px dashed #2563EB; /* Change border color */
            border-radius: 0.5rem;
            padding: 1rem;
            transition: all 0.2s ease;
        }

        [data-testid="stFileUploader"]:hover {
            background-color: #E6F7FF; /* Change background color on hover */
            border-color: #1E40AF; /* Change border color on hover */
        }

        [data-testid="stFileUploader"] > div {
            color: #330033; /* Change text color */
        }
        
        /* Heading styling */
        .stHeading {
            background-color: #F0F8FF; /* Change background color */
            padding: 1rem; /* Add padding for better spacing */
            border-radius: 0.5rem; /* Optional: add rounded corners */
        }

        .stHeading h3 {
            color: #0A0A0A; /* Change text color */
            font-weight: bold; /* Optional: make text bold */
        }
                
    </style>
    """, unsafe_allow_html=True)

# Function for logo and navbar
def navbar():
    # Logo URL or base64 encoded image
    logo_html = """
    <div class="navbar">
        <div class="navbar-logo">
            🎙️ VoClo
        </div>
        <div class="navbar-menu">
            <a href="http://127.0.0.1:5000/voice_auth" class="navbar-item">Home page</a>
            <a href="http://127.0.0.1:5000" class="navbar-item logout-btn">Logout</a>
        </div>
    </div>
    """
    st.markdown(logo_html, unsafe_allow_html=True)

# Function for section heading
def section_heading(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def load_model(model_path='trained_model.pkl'):
    with open(model_path, 'rb') as model_file:
        model = pickle.load(model_file)
    return model

def preprocess_audio(file_path):
    y, sr = librosa.load(file_path, sr=None)
    noise = np.random.randn(len(y))
    y_noisy = y + 0.005 * noise
    y_stretched = librosa.effects.time_stretch(y=y_noisy, rate=1.1)
    return y_stretched, sr

def extract_features(y, sr):
    zcr = np.mean(librosa.feature.zero_crossing_rate(y))
    mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T, axis=0)
    return np.hstack([zcr, mfccs])

def predict_audio(model, audio_file_path):
    y_stretched, sr = preprocess_audio(audio_file_path)
    feature_vector = extract_features(y_stretched, sr).reshape(1, -1)
    prediction = model.predict(feature_vector)
    return prediction[0]

def get_metadata(mp3_file_path):
    """
    Retrieve metadata from an MP3 file
    """
    try:
        if not os.path.exists(mp3_file_path):
            st.error(f"File not found: {mp3_file_path}")
            return None

        audiofile = eyed3.load(mp3_file_path)
        if audiofile is None or audiofile.tag is None:
            return {
                'name': "Unknown",
                'title': os.path.basename(mp3_file_path),
                'album': "VoClo Cloned Voices",
                'description': "No metadata available"
            }

        return {
            'name': audiofile.tag.artist or "Unknown",
            'title': audiofile.tag.title or os.path.basename(mp3_file_path),
            'album': audiofile.tag.album or "VoClo Cloned Voices",
            'description': audiofile.tag.comments[0].text if audiofile.tag.comments else "No description"
        }
    except Exception as e:
        st.error(f"Error reading metadata: {str(e)}")
        return None

def add_metadata_to_mp3(mp3_file_path, metadata):
    """
    Add metadata to an MP3 file
    """
    try:
        if not os.path.exists(mp3_file_path):
            st.error(f"MP3 file not found: {mp3_file_path}")
            return False

        audiofile = eyed3.load(mp3_file_path)
        if audiofile is None:
            audiofile = eyed3.File(mp3_file_path)
            audiofile.initTag()
        elif audiofile.tag is None:
            audiofile.initTag()

        audiofile.tag.artist = metadata['name']
        audiofile.tag.title = metadata['title']
        audiofile.tag.album = "VoClo Cloned Voices"
        audiofile.tag.comments.set(metadata['description'])
        audiofile.tag.save()
        return True
    except Exception as e:
        st.error(f"Error adding metadata: {str(e)}")
        return False

def convert_wav_to_mp3(wav_file_path):
    """
    Convert WAV file to MP3
    """
    try:
        if not os.path.exists(wav_file_path):
            st.error(f"WAV file not found: {wav_file_path}")
            return None

        mp3_file_path = wav_file_path.replace('.wav', '.mp3')
        st.info(f"Converting {wav_file_path} to MP3...")
        
        audio = AudioSegment.from_wav(wav_file_path)
        audio.export(mp3_file_path, format="mp3")
        
        if os.path.exists(mp3_file_path):
            st.success("Conversion successful!")
            return mp3_file_path
        else:
            st.error("MP3 file not created after conversion")
            return None
    except Exception as e:
        st.error(f"Error converting WAV to MP3: {str(e)}")
        return None

def save_cloned_voice(uploaded_file, metadata):
    """
    Save uploaded voice file and add metadata
    """
    try:
        person_dir = os.path.join(VOICES_DIR, metadata['name'])
        os.makedirs(person_dir, exist_ok=True)
        
        base_filename = f"{metadata['title']}_{np.random.randint(1000, 9999)}"
        wav_path = os.path.join(person_dir, f"{base_filename}.wav")
        
        # Save WAV file
        with st.spinner("Saving WAV file..."):
            with open(wav_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        # Convert to MP3
        with st.spinner("Converting to MP3..."):
            mp3_path = convert_wav_to_mp3(wav_path)
            if not mp3_path:
                return wav_path, None
        
        # Add metadata
        with st.spinner("Adding metadata..."):
            if not add_metadata_to_mp3(mp3_path, metadata):
                return wav_path, mp3_path
        
        return wav_path, mp3_path
    except Exception as e:
        st.error(f"Error in save_cloned_voice: {str(e)}")
        return None, None

# List available audio devices
def list_audio_devices():
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append({"index": i, "name": device['name']})
    
    return input_devices

def record_with_file_uploader():
    uploaded_file = st.file_uploader("Upload a recorded voice sample", type=["wav", "mp3"])
    if uploaded_file:
        timestamp = int(time.time())
        filename = f"uploaded_voice_{timestamp}{os.path.splitext(uploaded_file.name)[1]}"
        filepath = os.path.join(RECORDED_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Audio saved to {filepath}")
        return filepath
    return None

# Modified record audio function with device selection
# Function to record audio using PyAudio
def record_audio(duration=5, sample_rate=44100):
    """
    Record audio using PyAudio as an alternative to sounddevice.
    """
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, 
                            input=True, frames_per_buffer=1024)
        
        frames = []
        for _ in range(0, int(sample_rate / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        timestamp = int(time.time())
        filename = f"recorded_voice_{timestamp}.wav"
        filepath = os.path.join(RECORDED_DIR, filename)
        
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        
        st.success(f"Audio saved to {filepath}")
        return filepath
    except Exception as e:
        st.error(f"Error recording audio: {str(e)}")
        return None
def upload_voice_module():
    """Function to handle the upload cloned voice page"""
    section_heading("Upload Cloned Voice")
    
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Upload cloned voice file", type=['wav'])
        
        if uploaded_file:
            st.audio(uploaded_file)
            
            with st.form("voice_metadata"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Person's Name")
                with col2:
                    title = st.text_input("Voice Title")
                
                description = st.text_area("Description")
                
                submit = st.form_submit_button("Save Voice Profile")
                
                if submit and name and title:
                    metadata = {
                        'name': name,
                        'title': title,
                        'description': description
                    }
                    
                    wav_path, mp3_path = save_cloned_voice(uploaded_file, metadata)
                    if wav_path and mp3_path:
                        st.success("Voice profile saved successfully!")
                        
                        with open(mp3_path, "rb") as file:
                            st.download_button(
                                "Download MP3 with Metadata",
                                file,
                                file_name=os.path.basename(mp3_path)
                            )
        
        st.markdown('</div>', unsafe_allow_html=True)

def view_profiles_module():
    """Function to handle the view voice profiles page"""
    section_heading("Voice Profiles")
    
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        
        if os.path.exists(VOICES_DIR):
            profiles_found = False
            for person in os.listdir(VOICES_DIR):
                person_dir = os.path.join(VOICES_DIR, person)
                if os.path.isdir(person_dir):
                    profiles_found = True
                    st.subheader(person)
                    
                    for voice_file in os.listdir(person_dir):
                        if voice_file.endswith('.mp3'):
                            file_path = os.path.join(person_dir, voice_file)
                            metadata = get_metadata(file_path)
                            
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                if metadata:
                                    st.write(f"Title: {metadata['title']}")
                                    st.write(f"Description: {metadata['description']}")
                            
                            with col2:
                                wav_file = file_path.replace('.mp3', '.wav')
                                if os.path.exists(wav_file):
                                    st.audio(wav_file)
                            
                            st.markdown("---")
            
            if not profiles_found:
                st.info("No voice profiles found. Please upload some voices first.")
        
        st.markdown('</div>', unsafe_allow_html=True)

def classify_voice_module():
    """Function to handle the classify voice page"""
    section_heading("AI/Human Voice Classification")
    
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        
        try:
            model = load_model()
            
            # Create tabs for the classification methods
            upload_tab, record_tab, previous_tab = st.tabs(["Upload Audio", "Record Voice", "Previous Recordings"])
            
            with upload_tab:
                uploaded_file = st.file_uploader("Choose an audio file for classification", type=["wav", "mp3"])
                
                if uploaded_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getbuffer())
                        temp_path = tmp_file.name
                    
                    try:
                        st.audio(temp_path)
                        result = predict_audio(model, temp_path)
                        st.markdown(f"<h3>Classification Result: <span style='color:{('#FF5733' if result=='AI' else '#33A1FF')};'>{result}</span></h3>", unsafe_allow_html=True)
                        
                        # Option to save the uploaded file
                        if st.button("Save this file to recordings"):
                            timestamp = int(time.time())
                            save_filename = f"saved_upload_{timestamp}{os.path.splitext(uploaded_file.name)[1]}"
                            save_path = os.path.join(RECORDED_DIR, save_filename)
                            
                            with open(save_path, "wb") as f:
                                uploaded_file.seek(0)  # Reset file pointer
                                f.write(uploaded_file.getbuffer())
                            
                            st.success(f"File saved to recordings as {save_filename}")
                        
                    except Exception as e:
                        st.error(f"Error during classification: {str(e)}")
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
            
            with record_tab:
                st.write("Record your voice for classification")
                
                # Get available audio devices
                input_devices = list_audio_devices()
                
                if input_devices:
                    st.write("Available input devices:")
                    selected_device = st.selectbox(
                        "Select input device", 
                        options=range(len(input_devices)),
                        format_func=lambda x: f"{input_devices[x]['index']}: {input_devices[x]['name']}"
                    )
                    device_index = input_devices[selected_device]['index']
                else:
                    st.warning("No input devices found. Please use the upload option instead.")
                    device_index = None
                
                duration = st.slider("Recording duration (seconds)", min_value=3, max_value=15, value=5)
                
                col1, col2 = st.columns(2)
                with col1:
                    if device_index is not None and st.button("Start Recording"):
                        recorded_file = record_audio(duration=duration, device=device_index)
                        
                        if recorded_file and os.path.exists(recorded_file):
                            st.audio(recorded_file)
                            
                            try:
                                result = predict_audio(model, recorded_file)
                                st.markdown(f"<h3>Classification Result: <span style='color:{('#FF5733' if result=='AI' else '#33A1FF')};'>{result}</span></h3>", unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"Error during classification: {str(e)}")
                
                with col2:
                    st.write("Or upload a pre-recorded file:")
                    recorded_file = record_with_file_uploader()
                    
                    if recorded_file and os.path.exists(recorded_file):
                        st.audio(recorded_file)
                        
                        if st.button("Classify Uploaded Recording"):
                            try:
                                result = predict_audio(model, recorded_file)
                                st.markdown(f"<h3>Classification Result: <span style='color:{('#FF5733' if result=='AI' else '#33A1FF')};'>{result}</span></h3>", unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"Error during classification: {str(e)}")
            
            with previous_tab:
                # Display previous recordings
                st.subheader("Previous Recordings")
                if os.path.exists(RECORDED_DIR):
                    recordings = [f for f in os.listdir(RECORDED_DIR) if f.endswith(('.wav', '.mp3'))]
                    
                    if recordings:
                        selected_recording = st.selectbox("Select a previous recording", recordings)
                        recording_path = os.path.join(RECORDED_DIR, selected_recording)
                        
                        st.audio(recording_path)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Classify Selected Recording"):
                                try:
                                    result = predict_audio(model, recording_path)
                                    st.markdown(f"<h3>Classification Result: <span style='color:{('#FF5733' if result=='AI' else '#33A1FF')};'>{result}</span></h3>", unsafe_allow_html=True)
                                except Exception as e:
                                    st.error(f"Error during classification: {str(e)}")
                        
                        with col2:
                            if st.button("Delete Recording"):
                                try:
                                    os.remove(recording_path)
                                    st.success(f"Deleted {selected_recording}")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Error deleting file: {str(e)}")
                    else:
                        st.info("No previous recordings found.")
                        
        except Exception as e:
            st.error(f"Error loading classification model: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Apply styling
    load_css()
    
    # Display top navigation bar
    navbar()
    
    # Main content with sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-nav">', unsafe_allow_html=True)
        
        # Add logo to sidebar
        st.markdown('<div style="text-align: center; margin-bottom: 30px;"><h2 style="color: #4A6FE3;">🎙️ VoClo</h2></div>', unsafe_allow_html=True)
        
        # Use radio buttons styled as navigation items
        page = st.radio(
            "",
            ["Upload Cloned Voice", "View Voice Profiles", "Classify Voice"],
            label_visibility="collapsed"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add info section at bottom of sidebar
        st.markdown('---')
        st.markdown('<div style="font-size: 0.8em; color: #6C757D;">VoClo - Voice Cloning Manager<br>Version 1.0<br>© 2025 All rights reserved</div>', unsafe_allow_html=True)
    
    # Main content area
    if page == "Upload Cloned Voice":
        upload_voice_module()
    
    elif page == "View Voice Profiles":
        view_profiles_module()
    
    elif page == "Classify Voice":
        classify_voice_module()

if __name__ == "__main__":
    main()
