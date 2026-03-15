import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

GEMINI_API_KEY = "AIzaSyDLNs8RHW0ZZF7a17gIZrL_Y1X82qbY_2o"
genai.configure(api_key=GEMINI_API_KEY)

def get_video_id(url):
      pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
      match = re.search(pattern, url)
      return match.group(1) if match else None
  def get_transcript(video_id):
        try:
                  transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                  transcript = " ".join([t['text'] for t in transcript_list])
                  return transcript
except Exception as e:
        return f"Error: {str(e)}"

def generate_summary(transcript):
      model = genai.GenerativeModel('gemini-1.5-flash')
      prompt = f"Please provide a concise summary of the transcript with bullet points and 3 follow-up questions: {{transcript}}
      response = model.generate_content(prompt)
      return response.text

  st.set_page_config(page_title="YouTube Summarizer")
  st.title("YouTube Summarizer")
  st.markdown("Enter a YouTube URL below to get a summary.")

  youtube_url = st.text_input("YouTube Video URL")

  if st.button("Summarize"):
      if youtube_url:
          video_id = get_video_id(youtube_url)
          if video_id:
              with st.spinner("Processing..."):
                  transcript = get_transcript(video_id)
                  if not transcript.startswith("Error"):
                      summary = generate_summary(transcript)
                      st.markdown(summary)
                  else:
                      st.error(transcript)
          else:
              st.error("Invalid URL")
  
