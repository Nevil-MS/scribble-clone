import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
} from "react";

const DrawingCanvas = forwardRef(function DrawingCanvas(
  {
    round,
    color = "#000000",
    size = 5,
    tool = "pencil",
    onStroke,
  },
  ref
) {
  const canvasRef = useRef(null);

  const drawingRef = useRef(false);
  const lastPointRef = useRef(null);

  const historyRef = useRef([]);
  const currentStrokeRef = useRef(null);

  // Allows the fill tool to include anti-aliased pixels
  // that are slightly different from the target color.
  const FILL_TOLERANCE = 40;

  function fillWhiteBackground() {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    context.globalCompositeOperation = "source-over";
    context.fillStyle = "#ffffff";

    context.fillRect(
      0,
      0,
      canvas.width,
      canvas.height
    );
  }

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    context.lineCap = "round";
    context.lineJoin = "round";

    fillWhiteBackground();
  }, []);

  // Clear canvas whenever a new round begins
  useEffect(() => {
    const canvas = canvasRef.current;

    if (!canvas) {
      return;
    }

    const context = canvas.getContext("2d");

    context.clearRect(
      0,
      0,
      canvas.width,
      canvas.height
    );

    fillWhiteBackground();

    historyRef.current = [];
    drawingRef.current = false;
    lastPointRef.current = null;
    currentStrokeRef.current = null;
  }, [round]);

  function getPoint(event) {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();

    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    return {
      x: Math.floor(
        (event.clientX - rect.left) * scaleX
      ),
      y: Math.floor(
        (event.clientY - rect.top) * scaleY
      ),
    };
  }

  function hexToRgba(hex) {
    const value = hex.replace("#", "");

    const r = parseInt(value.substring(0, 2), 16);
    const g = parseInt(value.substring(2, 4), 16);
    const b = parseInt(value.substring(4, 6), 16);

    return [r, g, b, 255];
  }

  // Compare pixels using a small tolerance.
  // This prevents tiny anti-aliased pixels from being
  // left behind by the fill tool.
  function colorsMatch(a, b) {
    return (
      Math.abs(a[0] - b[0]) <= FILL_TOLERANCE &&
      Math.abs(a[1] - b[1]) <= FILL_TOLERANCE &&
      Math.abs(a[2] - b[2]) <= FILL_TOLERANCE &&
      Math.abs(a[3] - b[3]) <= FILL_TOLERANCE
    );
  }

  function drawStroke(stroke) {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    context.beginPath();

    context.moveTo(
      stroke.from.x,
      stroke.from.y
    );

    context.lineTo(
      stroke.to.x,
      stroke.to.y
    );

    context.lineWidth = stroke.size;

    if (stroke.tool === "eraser") {
      context.globalCompositeOperation = "destination-out";
      context.strokeStyle = "#000000";
    } else {
      context.globalCompositeOperation = "source-over";
      context.strokeStyle = stroke.color;
    }

    context.stroke();

    // Reset after every stroke
    context.globalCompositeOperation = "source-over";
  }

  function floodFill(startX, startY, fillColor) {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    const imageData = context.getImageData(
      0,
      0,
      canvas.width,
      canvas.height
    );

    const pixels = imageData.data;
    const width = canvas.width;
    const height = canvas.height;

    const startIndex =
      (startY * width + startX) * 4;

    const targetColor = [
      pixels[startIndex],
      pixels[startIndex + 1],
      pixels[startIndex + 2],
      pixels[startIndex + 3],
    ];

    const replacementColor = hexToRgba(fillColor);

    // Do nothing if the selected area is already
    // approximately the same color.
    if (colorsMatch(targetColor, replacementColor)) {
      return false;
    }

    const stack = [[startX, startY]];

    while (stack.length > 0) {
      const [x, y] = stack.pop();

      if (
        x < 0 ||
        x >= width ||
        y < 0 ||
        y >= height
      ) {
        continue;
      }

      const index = (y * width + x) * 4;

      const currentColor = [
        pixels[index],
        pixels[index + 1],
        pixels[index + 2],
        pixels[index + 3],
      ];

      // Only fill pixels that belong to the original region.
      if (!colorsMatch(currentColor, targetColor)) {
        continue;
      }

      pixels[index] = replacementColor[0];
      pixels[index + 1] = replacementColor[1];
      pixels[index + 2] = replacementColor[2];
      pixels[index + 3] = replacementColor[3];

      stack.push([x + 1, y]);
      stack.push([x - 1, y]);
      stack.push([x, y + 1]);
      stack.push([x, y - 1]);
    }

    context.putImageData(imageData, 0, 0);

    return true;
  }

  function redrawCanvas() {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    context.clearRect(
      0,
      0,
      canvas.width,
      canvas.height
    );

    // Restore the white canvas before replaying history.
    fillWhiteBackground();

    for (const action of historyRef.current) {
      if (action.type === "stroke") {
        for (const stroke of action.strokes) {
          drawStroke(stroke);
        }
      }

      if (action.type === "fill") {
        floodFill(
          action.x,
          action.y,
          action.color
        );
      }
    }
  }

  function startDrawing(event) {
    const point = getPoint(event);

    if (tool === "fill") {
      const filled = floodFill(
        point.x,
        point.y,
        color
      );

      if (filled) {
        const action = {
          type: "fill",
          x: point.x,
          y: point.y,
          color,
        };

        historyRef.current.push(action);

        onStroke?.(action);
      }

      return;
    }

    drawingRef.current = true;
    lastPointRef.current = point;

    currentStrokeRef.current = {
      type: "stroke",
      strokes: [],
    };
  }

  function draw(event) {
    if (!drawingRef.current) {
      return;
    }

    const currentPoint = getPoint(event);
    const previousPoint = lastPointRef.current;

    const stroke = {
      from: previousPoint,
      to: currentPoint,
      color,
      size,
      tool,
    };

    drawStroke(stroke);

    currentStrokeRef.current.strokes.push(stroke);

    onStroke?.(stroke);

    lastPointRef.current = currentPoint;
  }

  function stopDrawing() {
    if (!drawingRef.current) {
      return;
    }

    drawingRef.current = false;

    if (
      currentStrokeRef.current &&
      currentStrokeRef.current.strokes.length > 0
    ) {
      historyRef.current.push(
        currentStrokeRef.current
      );
    }

    currentStrokeRef.current = null;
    lastPointRef.current = null;
  }

  function undo() {
    if (historyRef.current.length === 0) {
      return;
    }

    historyRef.current.pop();

    redrawCanvas();
  }

  function clearCanvas() {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    context.clearRect(
      0,
      0,
      canvas.width,
      canvas.height
    );

    fillWhiteBackground();

    historyRef.current = [];

    drawingRef.current = false;
    lastPointRef.current = null;
    currentStrokeRef.current = null;
  }

  useImperativeHandle(ref, () => ({
    undo,
    clearCanvas,
  }));

  return (
    <div className="drawing-area">
      <canvas
        ref={canvasRef}
        id="drawing-board"
        width={800}
        height={500}
        onMouseDown={startDrawing}
        onMouseMove={draw}
        onMouseUp={stopDrawing}
        onMouseLeave={stopDrawing}
      />
    </div>
  );
});

export default DrawingCanvas;