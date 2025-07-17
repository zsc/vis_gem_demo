本 python + html demo 目的是可视化 gemini 检测到的文字框精确度。
用户在 demo 上传图片，然后调下面命令生成文字框，然后可视化成一张新的图片与原来图片 side-by-side。

# 以下是一些 llm 命令运行示例。可以加一次 llm 运行（“纯文字模式”）来约束输出格式更容易被后面利用。

% llm -m gemini-2.0-flash '细粒度描述这张图像内的文字并与坐标关联' -a "截屏2025-07-16 09.50.10.png"            
好的，这是图像中文字的细粒度描述以及对应的坐标位置：
                                                                               
*   **Genetic Programming for 2048** 位于 (30, 25) 附近
*   **Train** 位于 (156, 152) 附近
*   **Test** 位于 (206, 152) 附近
*   **Game Board** 位于 (30, 243) 附近
*   **Score: 27200 | Max Tile: 2048** 位于 (30, 307) 附近
*   **16** 位于 (78, 406) 附近
*   **2048** 位于 (175, 406) 附近
*   **4** 位于 (272, 406) 附近
*   **2** 位于 (369, 406) 附近
*   **8** 位于 (78, 519) 附近
*   **128** 位于 (175, 519) 附近
(略)

% llm -m gemini-2.0-flash '细粒度描述这张图像内的文字并与坐标关联' -a 'uploads/8de2f4dc-e7e8-4746-a149-66cc96b73b90_截屏2025-07-16 09.50.10.png'
Here are the bounding box detections:
```json
[
  {"box_2d": [50, 26, 92, 518], "label": "Genetic Programming for 2048"},
  {"box_2d": [169, 46, 191, 84], "label": "Train"},
  {"box_2d": [169, 123, 191, 152], "label": "Test"},
  {"box_2d": [276, 26, 306, 185], "label": "Game Board"},
  {"box_2d": [364, 26, 388, 122], "label": "Score: 27200"},
  {"box_2d": [364, 139, 388, 247], "label": "| Max Tile: 2048"},
  {"box_2d": [476, 64, 511, 98], "label": "16"},
  {"box_2d": [476, 151, 511, 215], "label": "2048"},
(略)

# scaling logic
from google import genai
from google.genai import types
from PIL import Image
import json

client = genai.Client()
prompt = "Detect the all of the prominent items in the image. The box_2d should be [ymin, xmin, ymax, xmax] normalized to 0-1000."

image = Image.open("/path/to/image.png")

config = types.GenerateContentConfig(
  response_mime_type="application/json"
  )

response = client.models.generate_content(model="gemini-2.5-flash",
                                          contents=[image, prompt],
                                          config=config
                                          )

width, height = image.size
bounding_boxes = json.loads(response.text)

converted_bounding_boxes = []
for bounding_box in bounding_boxes:
    abs_y1 = int(bounding_box["box_2d"][0]/1000 * height)
    abs_x1 = int(bounding_box["box_2d"][1]/1000 * width)
    abs_y2 = int(bounding_box["box_2d"][2]/1000 * height)
    abs_x2 = int(bounding_box["box_2d"][3]/1000 * width)
    converted_bounding_boxes.append([abs_x1, abs_y1, abs_x2, abs_y2])

print("Image size: ", width, height)
print("Bounding boxes:", converted_bounding_boxes)

