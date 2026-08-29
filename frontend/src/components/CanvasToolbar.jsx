function CanvasToolbar({ hidden }) {
  return (
    <div className={`canvas-toolbar ${hidden ? "toolbar-hidden" : ""}`}>
      <div className="tool-group">
        <button title="Pencil">✏</button>
        <button title="Eraser">⌫</button>
        <button title="Fill">▣</button>
      </div>

      <div className="brush-group">
        <button>•</button>
        <button>●</button>
        <button>⬤</button>
      </div>

      <div className="color-palette">
        <button className="white"></button>
        <button className="lightgrey"></button>
        <button className="grey"></button>
        <button className="black"></button>

        <button className="pink"></button>
        <button className="red"></button>
        <button className="orange"></button>
        <button className="brown"></button>

        <button className="yellow"></button>
        <button className="lime"></button>
        <button className="green"></button>
        <button className="cyan"></button>

        <button className="blue"></button>
        <button className="purple"></button>
      </div>
    </div>
  );
}

export default CanvasToolbar;