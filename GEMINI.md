本 python + html demo 目的是可视化 gemini 检测到的文字框，并将文字译成中文，再叠加显示到原图上。
用户在 demo 上传图片，然后参照以下生成文字框和把文字译成中文，然后可视化成一张新的图片与原来图片 side-by-side。

llm --schema '{
  "type": "object",
  "properties": {
    "labeled_boxes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "label_translated": {
            "type": "string"
          },
          "box_2d": {
            "type": "array",
            "items": {
                "type": "integer"
            }
          }
        }
      }
    }
  }
}' 'Detect the all of the text boxes in the image. The box_2d should be [ymin, xmin, ymax, xmax] normalized to 0-1000. The label should be translated into Chinese.' -a ~/Desktop/"截屏2025-07-16 09.50.10.png"

{
  "labeled_boxes": [
    {
      "box_2d": [
        162,
        46,
        198,
        84
      ],
      "label_translated": "训练"
    },
    {
      "box_2d": [
        162,
        121,
        198,
        156
      ],
      "label_translated": "测试"
    },
    {
      "box_2d": [
        414,
        632,
        447,
        840
      ],
      "label_translated": "run_20250716_093043_best.json"
    },
    {
      "box_2d": [
        414,
        849,
        458,
        959
      ],
      "label_translated": "Refresh List"
    },
    {
      "box_2d": [
        530,
        632,
        566,
        999
      ],
      "label_translated": "2"
    },
    {
      "box_2d": [
        597,
        643,
        624,
        720
      ],
      "label_translated": "New Game"
    },
    {
      "box_2d": [
        597,
        767,
        624,
        843
      ],
      "label_translated": "Let Al Play"
    }
  ]
}
