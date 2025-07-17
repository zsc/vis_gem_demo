from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import re
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def process_image(image_path, original_filename):
    """
    Processes the image using the llm command, draws bounding boxes, and saves the new image.
    """
    try:
        command = f"llm -m gemini-2.0-flash '细粒度描述这张图像内的文字并与坐标关联' -a '{image_path}'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        output = result.stdout

        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("sans-serif.ttf", 15)
        except IOError:
            font = ImageFont.load_default()

        for line in output.splitlines():
            match = re.search(r"'\s*位于\s*\((\d+),\s*(\d+)\)\s*附近", line)
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                text = line.split("'")[1]
                
                try:
                    bbox = font.getbbox(text)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except AttributeError:
                    # Fallback for older Pillow versions
                    text_width, text_height = draw.textsize(text, font=font)


                draw.rectangle([(x, y), (x + text_width, y + text_height)], outline="red", width=2)
                draw.text((x, y - text_height - 5), text, fill="red", font=font)


        processed_filename = f"processed_{original_filename}"
        processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        img.save(processed_path)
        return processed_filename
    except subprocess.CalledProcessError as e:
        print(f"Error processing image: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        original_filename = f"{uuid.uuid4()}_{file.filename}"
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(original_path)

        processed_filename = process_image(original_path, original_filename)

        return render_template('index.html', original_image=original_filename, processed_image=processed_filename)

@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5010)
