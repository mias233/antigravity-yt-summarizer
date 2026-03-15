from http.server import BaseHTTPRequestHandler
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

# Hardcoded API Key provided by the user
api_key = "AIzaSyDLNs8RHW0ZZF7a17gIZrL_Y1X82qbY_2o"
genai.configure(api_key=api_key)

def extract_video_id(url):
        """Extract YouTube video ID from various URL formats."""
        pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
        match = re.search(pattern, url)
        return match.group(1) if match else None

class handler(BaseHTTPRequestHandler):
        def do_POST(self):
                    try:
                                    content_length = int(self.headers.get('Content-Length', 0))
                                    post_data = self.rfile.read(content_length)

            if not post_data:
                                self.send_error_response(400, "Empty request body")
                                return

            data = json.loads(post_data)
except Exception as e:
            self.send_error_response(400, f"Invalid JSON format: {str(e)}")
            return

        url = data.get('url', '')
        video_id = extract_video_id(url)

        if not video_id:
                        self.send_error_response(400, 'Invalid YouTube URL. Could not extract the video ID.')
                        return

        try:
                        # 1. Extract Transcript
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Helper to extract text
                        def get_text(t_fetch):
                                            return " ".join([i['text'] for i in t_fetch])

                        try:
                                            # 1. Try to find a manually created English transcript
                                            transcript_text = get_text(transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB']).fetch())
                                        except:
                try:
                                        # 2. Try to find an auto-generated English transcript
                                        transcript_text = get_text(transcript_list.find_generated_transcript(['en']).fetch())
                                    except:
                    try:
                                                # 3. Just grab ANY manual transcript
                                                manual_transcripts = [t for t in transcript_list if not t.is_generated]
                                                if manual_transcripts:
                                                                                first_manual = manual_transcripts[0]
                                                                                transcript_text = get_text(first_manual.fetch())
                    else:
                                                    # 4. Just grab ANY auto-generated transcript
                                                    generated_transcripts = [t for t in transcript_list if t.is_generated]
                                                    if generated_transcripts:
                                                                                        first_gen = generated_transcripts[0]
                                                                                        transcript_text = get_text(first_gen.fetch())
                    else:
                                                                        raise Exception("No transcripts found.")
except Exception as e:
                        raise Exception(f"Failed to extract transcript: {str(e)}")


            # 2. Summarize using Gemini
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
                        You are an expert content summarizer. Below is the transcript of a YouTube video. 
                                    Note: The transcript might be in a foreign language. YOU MUST PROCESS IT AND OUTPUT YOUR RESPONSE IN ENGLISH.

                                                            1. First, provide a concise, well-formatted summary of the key takeaways IN ENGLISH using bullet points.
                                                                        2. Then, generate exactly 3 insightful follow-up prompts or questions IN ENGLISH that the user can ask you to dive deeper into the video's topic. Format them clearly under the heading "### Follow-up Prompts".

                                                                                                Transcript:
                                                                                                            {transcript_text}
                                                                                                                        """

            response = model.generate_content(prompt)

            # Send Success Response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response_json = json.dumps({'summary': response.text})
            self.wfile.write(response_json.encode('utf-8'))

except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.send_error_response(500, error_msg)

    def do_OPTIONS(self):
                # Handle CORS preflight requests
                self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_error_response(self, status_code, message):
                self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode('utf-8'))
