from http.server import BaseHTTPRequestHandler
import json, re, google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
genai.configure(api_key="AIzaSyDLNs8RHW0ZZF7a17gIZrL_Y1X82qbY_2o")

def extract(url):
    m = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return m.group(1) if m else None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            l = int(self.headers.get('Content-Length', 0))
            d = json.loads(self.rfile.read(l)) if l > 0 else {}
            v = extract(d.get('url', ''))
            if not v: raise Exception("Invalid URL")
            t = ""
            try:
                ts = YouTubeTranscriptApi.list_transcripts(v)
                try: t = " ".join([i['text'] for i in ts.find_manually_created_transcript(['en']).fetch()])
                except: t = " ".join([i['text'] for i in list(ts)[0].fetch()])
            except:
                try: t = " ".join([i['text'] for i in YouTubeTranscriptApi.get_transcript(v)])
                except:
                    import urllib.request as ur, html
                    c = ur.urlopen(ur.Request(f"https://www.youtube.com/watch?v={v}", headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf-8')
                    m = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;', c)
                    if m:
                        p = json.loads(m.group(1))
                        tr = p.get('captions', {}).get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
                        if tr: t = " ".join([html.unescape(re.sub(r'<[^>]+>', '', x)) for x in re.findall(r'<text[^>]*>(.*?)</text>', ur.urlopen(tr[0]['baseUrl']).read().decode('utf-8'))])
            if not t: raise Exception("No transcript available")
            m = genai.GenerativeModel('gemini-1.5-flash')
            s = m.generate_content(f"Summarize this YouTube transcript: {t[:30000]}").text
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'summary': s}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
