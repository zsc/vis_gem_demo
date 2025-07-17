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
        original_width, original_height = map(float, (original_width, original_height))

        # Gemini scaling logic
        # https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal/send-multimodal-prompts#image_requirements
        # Large images are scaled down to fit within a 3072x3072 square.
        # Small images are scaled up to a 768x768 square.
        
        scaled_width, scaled_height = original_width, original_height
        if max(original_width, original_height) > 3072:
            if original_width > original_height:
                scaled_width = 3072
                scaled_height = int(3072 * original_height / original_width)
            else:
                scaled_height = 3072
                scaled_width = int(3072 * original_width / original_height)
        elif min(original_width, original_height) < 768:
            if original_width < original_height:
                scaled_width = 768
                scaled_height = int(768 * original_height / original_width)
            else:
                scaled_height = 768
                scaled_width = int(768 * original_width / original_height)

        x_scale = original_width / float(scaled_width)
        y_scale = original_height / float(scaled_height)

        command = f"llm -m gemini-2.0-flash '细粒度描述这张图像内的文字并与坐标关联' -a '{image_path}'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        output = result.stdout

        # Extract json from the output
        json_match = re.search(r"```json\n(.*)\n```", output, re.DOTALL)
        if not json_match:
            print("Error: No JSON found in the output.")
            return None

        bounding_boxes = json.loads(json_match.group(1))

        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("sans-serif.ttf", 15)
        except IOError:
            font = ImageFont.load_default()

        print(x_scale, y_scale, 'x_scale')
        for box in bounding_boxes:
            box_2d = box['box_2d']
            label = box['label']
            
            # Adjust coordinates based on scaling
            y1 = int(box_2d[0] * y_scale)
            x1 = int(box_2d[1] * x_scale)
            y2 = int(box_2d[2] * y_scale)
            x2 = int(box_2d[3] * x_scale)

            # box_2d is [y1, x1, y2, x2]
            draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=2)
            
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
