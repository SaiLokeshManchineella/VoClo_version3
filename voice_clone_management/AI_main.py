import os
import numpy as np
import pandas as pd
import librosa
import pickle
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Step 1: Load Dataset
def load_dataset(folder_path):
    data = []
    labels = []
    
    for label in ['real', 'fake']:
        folder = os.path.join(folder_path, label)
        for filename in os.listdir(folder):
            if filename.endswith('.wav') or filename.endswith('.mp3'):
                file_path = os.path.join(folder, filename)
                data.append(file_path)
                labels.append(label)
    
    return data, labels

# Step 2: Pre-processing
def preprocess_audio(file_path):
    # Load audio file
    y, sr = librosa.load(file_path, sr=None)
    
    # Noise Injection (Adding random noise)
    noise = np.random.randn(len(y))
    y_noisy = y + 0.005 * noise
    
    # Stretching (Time stretching)
    y_stretched = librosa.effects.time_stretch(y_noisy, rate=1.1)  # Stretching by 10%
    
    return y_stretched, sr

# Step 3: Feature Extraction
def extract_features(y, sr):
    # Zero Crossing Rate
    zcr = np.mean(librosa.feature.zero_crossing_rate(y))
    
    # MFCC
    mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T, axis=0)
    
    return np.hstack([zcr, mfccs])

# Step 4: Main Function
def main(folder_path):
    data, labels = load_dataset(folder_path)
    
    features = []
    
    for file_path in data:
        y_stretched, sr = preprocess_audio(file_path)
        feature_vector = extract_features(y_stretched, sr)
        features.append(feature_vector)
    
    # Convert to DataFrame
    X = np.array(features)
    y = np.array(labels)
    
    # Step 5: Data Splitting
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Step 6: Classification
    model = DecisionTreeClassifier()
    model.fit(X_train, y_train)
    
    # Step 7: Performance Estimation
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, pos_label='fake')
    recall = recall_score(y_test, y_pred, pos_label='fake')
    f1 = f1_score(y_test, y_pred, pos_label='fake')
    
    print(f'Accuracy: {accuracy:.2f}')
    print(f'Precision: {precision:.2f}')
    print(f'Recall: {recall:.2f}')
    print(f'F1 Score: {f1:.2f}')
    
    # Save the trained model
    with open('AIorHuman_model.pkl', 'wb') as model_file:
        pickle.dump(model, model_file)
    
    return model  # Return the trained model for prediction

# Step 8: Load Model Function
def load_model(model_path='AIorHuman_model.pkl'):
    with open(model_path, 'rb') as model_file:
        model = pickle.load(model_file)
    return model

# Step 9: Prediction Function
def predict_audio(model, audio_file_path):
    y_stretched, sr = preprocess_audio(audio_file_path)
    feature_vector = extract_features(y_stretched, sr).reshape(1, -1)  # Reshape for prediction
    prediction = model.predict(feature_vector)
    
    return prediction[0]  # Return the predicted label

# Run the main function and make a prediction
if __name__ == "__main__":
    dataset_folder = 'dataset'  # Change this to your dataset path
    trained_model = main(dataset_folder)
    
    # Example usage of the prediction function
    audio_to_predict = 'dataset/fake/Ali.wav'  # Change this to the audio file you want to predict
    result = predict_audio(trained_model, audio_to_predict)
    print(f'The predicted label for the audio file is: {result}')
