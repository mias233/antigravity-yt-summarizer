from http.server import BaseHTTPRequestHandler
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

# Hardcoded API Key
api_key = "AIzaSyDLNs8RHW0ZZF7a17gIZrL_Y1X82qbY_2o"
genai.configure(api_key=api_key)

def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data) if post_data else {}
        except Exception as e:
            self.send_error_response(400, f"Invalid JSON: {str(e)}")
            return

        url = data.get('url', '')
        video_id = extract_video_id(url)
        if not video_id:
            self.send_error_response(400, 'Invalid URL')
            return
            
        transcript_text = None
        try:
            # TRY 1: list_transcripts
            try:
                ts = YouTubeTranscriptApi.list_transcripts(video_id)
                try:
                    transcript_text = " ".join([i['text'] for i in ts.find_manually_created_transcript(['en', 'en-US']).fetch()])
                except:
                    try:
                        transcript_text = " ".join([i['text'] for i in ts.find_generated_transcript(['en']).fetch()])
                    except:
                        transcript_text = " ".join([i['text'] for i in list(ts)[0].fetch()])
            except:
                # TRY 2: get_transcript
                try:
                    transcript_text = " ".join([i['text'] for i in YouTubeTranscriptApi.get_transcript(video_id)])
                except:
                    # TRY 3: Scraper
                    import urllib.request
                    import html
                    r = urllib.request.Request(f"https://www.youtube.com/watch?v={video_id}", headers={'User-Agent': 'Mozilla/5.0'})
                    c = urllib.request.urlopen(r).read().decode('utf-8')
                    m = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;\s*(?:var|</script>)', c)
                    if m:
                        p = json.loads(m.group(1))
                        cap = p.get('captions', {}).get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
                        if cap:
                            xml = urllib.request.urlopen(cap[0]['baseUrl']).read().decode('utf-8')
                            transcript_text = " ".join([html.unescape(re.sub(r'<[^>]+>', '', t)) for t in re.findall(r'<text[^>]*>(.*?)</text>', xml)])

            if not transcript_text: raise Exception("No Transcript")

            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Summarize this in English:\
\
{transcript_text}"
            response = model.generate_content(prompt)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'summary': response.text}).encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(500, str(e))
            
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_error_response(self, status, msg):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': msg}).encode('utf-8'))
