function DrawingCanvas() {
  return (
    <div className="drawing-area">
      <canvas id="drawing-board" width={800} height={500}></canvas>
    </div>
  );
}

export default DrawingCanvas;