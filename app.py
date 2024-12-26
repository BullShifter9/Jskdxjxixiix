from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import os
from urllib.parse import urlparse
import re

app = Flask(__name__)

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def is_valid_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    youtube_regex_match = re.match(youtube_regex, url)
    return bool(youtube_regex_match)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.json
        url = data.get('url')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        if not is_valid_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info['title']
            sanitized_title = "".join(x for x in video_title if x.isalnum() or x in (' ','-','_'))
            output_file = f"{sanitized_title}.mp3"
            
            ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, output_file)
            ydl.download([url])

        return jsonify({
            'download_url': f'/download/{output_file}',
            'title': video_title
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    try:
        return send_file(
            os.path.join(DOWNLOAD_DIR, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True)
