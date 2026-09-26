# Perfect Circle: a Computer Vision Mini-Game

Draw a circle with your mouse and get an objective score of how close it is to a perfect one. The drawing is analysed with classic computer vision: contour extraction, image moments and shape metrics.

## How it works

1. **Drawing**: the player draws a closed shape on an OpenCV canvas.
2. **Closure check**: the shape counts as closed if the start and end points are within 20 px; otherwise the player gets a warning.
3. **Reference circle**: the centre is taken from the contour's image moments (centre of mass), and the radius is the mean distance from the centre to the drawn points.
4. **Visual feedback**: areas outside the ideal circle are highlighted in red, areas inside it in blue.
5. **Metrics** shown under the canvas:

| Metric | Meaning |
|---|---|
| RMSE | Root-mean-square deviation of the drawn points from the ideal radius (px) |
| Max Dev | Largest single deviation (px) |
| Area Ratio | Drawn area / ideal circle area (1.0 is perfect) |
| Circularity | `4π · area / perimeter²` (1.0 for a perfect circle) |
| Smoothness | Number of vertices after polygon approximation (`approxPolyDP`) |

## Quick start

```bash
pip install -r requirements.txt
python perfect_circle.py
```

Hold the left mouse button to draw, release to get the score, and press **`q`** to quit.

## Files

| File | Description |
|---|---|
| `perfect_circle.py` | The game (recommended entry point) |
| `circle.ipynb` | Notebook version used during development |

## Tech stack

Python · OpenCV · NumPy

## License

[MIT](LICENSE)
