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
            
        transcript_text = None
        try:
            # TRY Extraction
            try:
                # Attempt 1: Standard API
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                # Helper to extract text
                def get_text(t_fetch):
                    return " ".join([i['text'] for i in t_fetch])

                try:
                    # 1. English Manual
                    transcript_text = get_text(transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB']).fetch())
                except:
                    try:
                        # 2. English Auto
                        transcript_text = get_text(transcript_list.find_generated_transcript(['en']).fetch())
                    except:
                        # 3. Any Manual
                        manuals = [t for t in transcript_list if not t.is_generated]
                        if manuals:
                            transcript_text = get_text(manuals[0].fetch())
                        else:
                            # 4. Any Generated
                            gens = [t for t in transcript_list if t.is_generated]
                            if gens:
                                transcript_text = get_text(gens[0].fetch())
                            else:
                                raise Exception("No transcripts available via API.")
            except Exception as e1:
                # Attempt 2: Basic get_transcript fallback
                try:
                    transcript_fetch = YouTubeTranscriptApi.get_transcript(video_id)
                    transcript_text = " ".join([i['text'] for i in transcript_fetch])
                except Exception as e2:
                    # Attempt 3: ULTIMATE FALLBACK (Custom Scraper)
                    import urllib.request
                    import html as html_lib
                    
                    req = urllib.request.Request(f"https://www.youtube.com/watch?v={video_id}", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                    html_content = urllib.request.urlopen(req).read().decode('utf-8')
                    
                    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;\s*(?:var|</script>)', html_content)
                    if not match: raise Exception("No Transcript Found (Fallback Case 1)")
                    
                    player_resp = json.loads(match.group(1))
                    captions = player_resp.get('captions', {}).get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
                    if not captions: raise Exception("No Transcript Found (Fallback Case 2)")
                    
                    xml_data = urllib.request.urlopen(captions[0]['baseUrl']).read().decode('utf-8')
                    texts = re.findall(r'<text[^>]*>(.*?)</text>', xml_data)
                    if not texts: raise Exception("No Transcript Found (Fallback Case 3)")
                    
                    transcript_text = " ".join([html_lib.unescape(re.sub(r'<[^>]+>', '', t)) for t in texts])

            if not transcript_text:
                raise Exception("Could not retrieve transcript from any source.")

            # 2. Summarize
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Summarize this YouTube transcript in English with key takeaways and follow-up questions:
 
{transcript_text}"
            response = model.generate_content(prompt)
            
            # Send Success
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'summary': response.text}).encode('utf-8'))
            
        except Exception as e:
            msg = str(e)
            if any(term in msg for term in ["TranscriptsDisabled", "Subtitles are disabled", "No Transcript Found"]):
                msg = "The creator of this video has disabled third-party transcript access, or no subtitles exist. Please try a different video."
            self.send_error_response(500, msg)
            
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_error_response(self, status, message):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode('utf-8'))
