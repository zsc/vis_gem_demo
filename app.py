from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import re
import uuid
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def process_image(image_path, original_filename):
    """
    Processes the image using the llm command, draws bounding boxes, and saves the new image.
    """
    try:
        img = Image.open(image_path)
        original_width, original_height = img.size

        # The prompt now asks for coordinates normalized to 0-1000.
        prompt = "细粒度描述这张图像内的文字并与坐标关联. The box_2d should be [ymin, xmin, ymax, xmax] normalized to 0-1000."
        command = f"llm -m gemini-2.0-flash \"{prompt}\" -a '{image_path}'"
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        output = result.stdout

        # Extract json from the output
        json_match = re.search(r"```json\n(.*)\n```", output, re.DOTALL)
        if not json_match:
            # Fallback for non-json output for safety
            json_match = re.search(r"\[\\s*\{.*\}\\s*\]", output, re.DOTALL)
            if not json_match:
                print("Error: No JSON found in the output.")
                return None
            json_str = json_match.group(0)
        else:
            json_str = json_match.group(1)

        bounding_boxes = json.loads(json_str)

        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("sans-serif.ttf", 15)
        except IOError:
            font = ImageFont.load_default()

        for box in bounding_boxes:
            box_2d = box['box_2d']
            label = box.get('label', '') # Use .get for safety
            
            # Convert normalized coordinates to absolute pixel values
            y1 = int(box_2d[0] / 1000 * original_height)
            x1 = int(box_2d[1] / 1000 * original_width)
            y2 = int(box_2d[2] / 1000 * original_height)
            x2 = int(box_2d[3] / 1000 * original_width)

            draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)
            
            # Draw text label
            text_position = (x1, y1 - 20) # 20 pixels above the box
            draw.text(text_position, label, fill="red", font=font)

        processed_filename = f"processed_{original_filename}"
        processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        img.save(processed_path)
        return processed_filename
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
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
