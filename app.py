from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import re

app = Flask(__name__)

# डाउनलोड फोल्डर (अगर नहीं है तो बना देंगे)
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# फ़ाइल नाम से अवैध कैरेक्टर हटाने के लिए
def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)

# वीडियो की जानकारी लेने के लिए (बिना डाउनलोड किए)
def get_video_info(url):
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'success': True,
                'title': info.get('title', 'video'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0)
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}

# वीडियो डाउनलोड करने के लिए
def download_video(url):
    try:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = clean_filename(info.get('title', 'video'))
            video_ext = info.get('ext', 'mp4')
            filename = f"{video_title}.{video_ext}"
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
            return {'success': True, 'file_path': file_path, 'filename': filename}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# होम पेज
@app.route('/')
def index():
    return render_template('index.html')

# वीडियो की जानकारी देने वाला API
@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'URL नहीं दिया गया'})
    result = get_video_info(url)
    return jsonify(result)

# डाउनलोड करने वाला API
@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'URL नहीं दिया गया'})
    result = download_video(url)
    if result['success']:
        return send_file(
            result['file_path'],
            as_attachment=True,
            download_name=result['filename']
        )
    else:
        return jsonify({'success': False, 'error': result['error']})

# यह लाइन सिर्फ local run के लिए है, Render पर gunicorn use करेगा
if __name__ == '__main__':
    app.run(debug=True)