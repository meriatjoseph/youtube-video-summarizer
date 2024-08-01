import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import os
from youtube_transcript_api import YouTubeTranscriptApi
import time
import requests

# Load environment variables
load_dotenv()

# Configure Google Generative AI with API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define the prompt for summarization
prompt = """You are a YouTube video summarizer. You will be taking the transcript text
and summarizing the entire video, providing the important summary in points within 250 words. 
Please provide the summary of the text given here: """

# Function to extract transcript details from a YouTube video URL
def extract_transcript_details(youtube_video_url):
    max_retries = 3
    retry_delay = 10  # seconds

    for attempt in range(max_retries):
        try:
            # Extract video ID from the URL
            if 'v=' in youtube_video_url:
                video_id = youtube_video_url.split("v=")[-1].split("&")[0]
            else:
                st.error("Invalid YouTube URL format. Ensure it contains 'v='.")
                return None

            # Fetch transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            transcript = ""
            for entry in transcript_list:
                transcript += " " + entry['text']
                
            return transcript
        except requests.ConnectionError as e:
            st.error(f"Network issue: {e}. Retrying...")
            time.sleep(retry_delay)  # Wait before retrying
        except Exception as e:
            st.error(f"Error fetching transcript: {e}")
            return None
    st.error("Failed to fetch transcript after multiple attempts.")
    return None

# Function to generate content using Google Gemini Pro with retry logic
def generate_gemini_content(transcript_text, prompt):
    max_retries = 5
    retry_delay = 60  # seconds

    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt + transcript_text)
            return response.text
        except Exception as e:
            if "429" in str(e):
                st.error(f"API quota exceeded. Attempt {attempt + 1} of {max_retries}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                st.error(f"Error generating content: {e}")
                return None
    st.error("Failed to generate content after multiple attempts.")
    return None

# Streamlit app layout
st.title('YouTube Transcript to Detailed Notes Converter')
youtube_link = st.text_input('Enter YouTube Video Link:')

# Display YouTube thumbnail if link is provided
if youtube_link:
    try:
        # Extract video ID from the URL
        if 'v=' in youtube_link:
            video_id = youtube_link.split("v=")[-1].split("&")[0]
            st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)
        else:
            st.error("Invalid YouTube URL format. Please ensure it contains 'v='.")
    except Exception as e:
        st.error(f"Error displaying thumbnail: {e}")

# Get detailed notes when the button is clicked
if st.button("Get Detailed Notes"):
    if youtube_link:
        transcript_text = extract_transcript_details(youtube_link)
        if transcript_text:
            summary = generate_gemini_content(transcript_text, prompt)
            if summary:
                st.markdown("## Detailed Notes:")
                st.write(summary)
            else:
                st.error("Failed to generate summary.")
        else:
            st.error("No transcript available for the provided video.")
    else:
        st.error("Please enter a valid YouTube link.")

