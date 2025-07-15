import pyppeteer
hti = Html2Image(browser_executable="/usr/bin/google-chrome")
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tempfile
import shutil
import tempfile
import shutil
import json
import uuid
import base64
import atexit
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from fpdf import FPDF
from PIL import Image
from html2image import Html2Image
from persona_template import PersonaGenerator
from reddit_scraper import RedditScraper

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Configure directories
TEMP_DIR = tempfile.mkdtemp()
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize HTML to image converter
# hti = Html2Image(output_path=TEMP_DIR, size=(1600, 800))
CHROME_PATH = "/usr/bin/google-chrome"
hti = Html2Image(
    output_path=TEMP_DIR,
    size=(1600, 800),
    browser_executable=CHROME_PATH
)


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
                # Clean up the URL (remove query parameters)
                photo_url = redditor.icon_img.split('?')[0]
                persona_data['photo'] = photo_url
        except Exception as e:
            print(f"Couldn't fetch Reddit avatar: {e}")
            # Fallback to generated avatar
            persona_data['photo'] = generator._generate_svg_avatar(username)
        
        # Generate a unique ID for this persona
        persona_data['id'] = str(uuid.uuid4())
        
        # Save the JSON data temporarily
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
        # Render HTML content
        html_content = render_template('persona_card.html', persona=persona_data)
        html_path = os.path.join(TEMP_DIR, f'{persona_id}.html')
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if file_type == 'jpg':
            output_file = f'{persona_id}.jpg'
            hti.screenshot(
                html_file=html_path,
                save_as=output_file,
                size=(1600, 800)  # Explicitly set size here too
            )
            return send_file(
                os.path.join(TEMP_DIR, output_file),
                as_attachment=True,
                download_name=f"persona_{persona_id}.jpg",
                mimetype='image/jpeg'
            )

        
        elif file_type == 'pdf':
            # First generate a PNG with full width
            png_file = f'{persona_id}.png'
            hti.screenshot(
                html_file=html_path,
                save_as=png_file,
                size=(1600, 800)
            )
            
            # Convert PNG to PDF
            image_path = os.path.join(TEMP_DIR, png_file)
            pdf_path = os.path.join(TEMP_DIR, f'{persona_id}.pdf')
            
            image = Image.open(image_path)
            width, height = image.size
            
            # Create PDF with same dimensions as image
            pdf = FPDF(unit="pt", format=[width, height])
            pdf.add_page()
            pdf.image(image_path, 0, 0, width, height)
            pdf.output(pdf_path)
            
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"persona_{persona_id}.pdf",
                mimetype='application/pdf'
            )
    
    except Exception as e:
        return f"Error generating {file_type}: {str(e)}", 500
    
    finally:
        # Clean up temp files
        temp_files = [
            html_path,
            os.path.join(TEMP_DIR, f'{persona_id}.png'),
            os.path.join(TEMP_DIR, f'{persona_id}.jpg'),
            os.path.join(TEMP_DIR, f'{persona_id}.pdf')
        ]
        for file_path in temp_files:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error cleaning up {file_path}: {e}")

@app.route('/temp_uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Cleanup at exit
atexit.register(lambda: shutil.rmtree(TEMP_DIR, ignore_errors=True))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)