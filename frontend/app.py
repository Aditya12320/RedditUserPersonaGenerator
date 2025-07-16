import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tempfile
import shutil
import json
import uuid
import base64
import atexit
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from fpdf import FPDF, HTMLMixin
from PIL import Image, ImageDraw, ImageFont
from html2image import Html2Image
from persona_template import PersonaGenerator
from reddit_scraper import RedditScraper

class PDF(FPDF, HTMLMixin):
    pass

app = Flask(__name__, static_folder='static', template_folder='templates')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

TEMP_DIR = tempfile.mkdtemp()
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize HTML to image converter
try:
    hti = Html2Image(
        output_path=TEMP_DIR,
        size=(1600, 900),
        browser_executable='google-chrome' if os.name == 'posix' else None
    )
except Exception as e:
    print(f"Html2Image initialization failed, using fallback: {e}")
    class SimpleScreenshot:
        def screenshot(self, html_file=None, save_as=None, size=None):
            img = Image.new('RGB', size or (1600, 900), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            d.text((100, 100), "Persona Card", fill=(0, 0, 0), font=font)
            img.save(os.path.join(TEMP_DIR, save_as))
    
    hti = SimpleScreenshot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    username = request.form.get('username', '').strip()
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    try:
        scraper = RedditScraper()
        posts, comments = scraper.get_user_data(username)
        
        if not posts and not comments:
            return jsonify({'error': 'No data found for this user'}), 404
        
        generator = PersonaGenerator()
        persona_data = generator.generate_persona_json(username, posts, comments)
        
        # Get Reddit profile photo
        try:
            redditor = scraper.reddit.redditor(username)
            if hasattr(redditor, 'icon_img') and redditor.icon_img:
                photo_url = redditor.icon_img.split('?')[0]
                persona_data['photo'] = photo_url
        except Exception as e:
            print(f"Couldn't fetch Reddit avatar: {e}")
            persona_data['photo'] = generator._generate_svg_avatar(username)
        
        persona_data['id'] = str(uuid.uuid4())
        
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{persona_data["id"]}.json')
        with open(json_path, 'w') as f:
            json.dump(persona_data, f)
        
        return jsonify(persona_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<persona_id>/<file_type>')
def download(persona_id, file_type):
    json_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{persona_id}.json')
    
    if not os.path.exists(json_path):
        return "Persona data not found", 404
    
    with open(json_path, 'r') as f:
        persona_data = json.load(f)
    
    if file_type == 'json':
        return jsonify(persona_data)
    
    try:
        if file_type == 'pdf':
            # First generate the JPG image
            html_content = render_template('persona_card.html', persona=persona_data)
            html_path = os.path.join(TEMP_DIR, f'{persona_id}.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            img_path = os.path.join(TEMP_DIR, f'{persona_id}.jpg')
            hti.screenshot(
                html_file=html_path,
                save_as=f'{persona_id}.jpg',
                size=(1600, 1200)
            )
            
            # Convert JPG to PDF
            pdf_path = os.path.join(TEMP_DIR, f'{persona_id}.pdf')
            image = Image.open(img_path)
            image.convert('RGB').save(pdf_path)
            
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"persona_{persona_id}.pdf",
                mimetype='application/pdf'
            )
        
        elif file_type == 'jpg':
            # Existing JPG generation code
            html_content = render_template('persona_card.html', persona=persona_data)
            html_path = os.path.join(TEMP_DIR, f'{persona_id}.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            img_path = os.path.join(TEMP_DIR, f'{persona_id}.jpg')
            hti.screenshot(
                html_file=html_path,
                save_as=f'{persona_id}.jpg',
                size=(1600, 1200)
            )
            
            return send_file(
                img_path,
                as_attachment=True,
                download_name=f"persona_{persona_id}.jpg",
                mimetype='image/jpeg'
            )
    
    except Exception as e:
        return f"Error generating {file_type}: {str(e)}", 500
    finally:
        temp_files = [
            os.path.join(TEMP_DIR, f'{persona_id}.pdf'),
            os.path.join(TEMP_DIR, f'{persona_id}.jpg'),
            os.path.join(TEMP_DIR, f'{persona_id}.html')
        ]
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

@app.route('/temp_uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

atexit.register(lambda: shutil.rmtree(TEMP_DIR, ignore_errors=True))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)