from http.server import BaseHTTPRequestHandler
import json, re, urllib.request, html, google.generativeai as genai

genai.configure(api_key="AIzaSyDLNs8RHW0ZZF7a17gIZrL_Y1X82qbY_2o")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            data = json.loads(post_data)
            url = data.get('url', '')
            video_id = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url).group(1)
            
            # Scraper
            req = urllib.request.Request(f"https://www.youtube.com/watch?v={video_id}", headers={'User-Agent': 'Mozilla/5.0'})
            html_content = urllib.request.urlopen(req).read().decode('utf-8')
            match = re.search(r'ytInitialPlayerResponses*=s*({.+?})s*;', html_content)
            if not match: raise Exception("No player data")
            
            player_resp = json.loads(match.group(1))
            tracks = player_resp.get('captions', {}).get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
            if not tracks: raise Exception("No transcripts found on YouTube.")
            
            xml_data = urllib.request.urlopen(tracks[0]['baseUrl']).read().decode('utf-8')
            transcript = " ".join([html.unescape(re.sub(r'<[^>]+>', '', t)) for t in re.findall(r'<text[^>]*>(.*?)</text>', xml_data)])
            
            summary = genai.GenerativeModel('gemini-1.5-flash').generate_content(f"Summarize: {transcript[:30000]}").text
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'summary': summary}).encode())
        except Exception as e:
            self.send_response(200)
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
