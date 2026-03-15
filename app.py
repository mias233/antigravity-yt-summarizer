import streamlit as st
from youtube_transcript_api import YouTub
def get_transcript(video_id):
          try:
                        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                        transcript = " ".join([t['text'] for t in transcript_list])
                        return transcript
except Exception as e:
        return f"Error: {str(e)}"

def generate_summary(transcript):
          model = genai.GenerativeModel('gemini-1.5-flash')
          prompt = f"Summary with bullets and 3 questions: {transcript}"
          response = model.generate_content(prompt)
          return response.text
      
st.set_page_config(page_title="YouTube Summarizer")
st.title("YouTube Summarizer")
st.markdown("Enter URL.")
youtube_url = st.text_input("URL")
if st.button("Summarize"):
          if youtube_url:
                        video_id = get_video_id(youtube_url)
                        if video_id:
                                          with st.spinner("Wait..."):
                                                                transcript = get_transcript(video_id)
                                                                if not transcript.startswith("Error"):
                                                                                          st.markdown(generate_summary(transcript))
                                                                else:
                                                                                          st.error(transcript)
                                                                      eTranscriptApi
import google.generativeai as genai
import re

GEMINI_API_KEY = "AIzaSyDLNs8RHW0ZZF7a17gIZrL_Y1X82qbY_2o"
genai.configure(api_key=GEMINI_API_KEY)

def get_video_id(url):
          pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
          match = re.search(pattern, url)
          return match.group(1) if match else None
      
