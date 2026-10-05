function CanvasToolbar({
  hidden,
  tool,
  setTool,
  color,
  setColor,
  size,
  setSize,
  onUndo,
  onClear,
}) {
  const colors = [
    { name: "white", value: "#ffffff" },
    { name: "lightgrey", value: "#d3d3d3" },
    { name: "grey", value: "#808080" },
    { name: "black", value: "#000000" },

    { name: "pink", value: "#ff69b4" },
    { name: "red", value: "#ff0000" },
    { name: "orange", value: "#ff8c00" },
    { name: "brown", value: "#8b4513" },

    { name: "yellow", value: "#ffff00" },
    { name: "lime", value: "#7fff00" },
    { name: "green", value: "#008000" },
    { name: "cyan", value: "#00e5ff" },

    { name: "blue", value: "#0066ff" },
    { name: "purple", value: "#8000ff" },
  ];

  return (
    <div className={`canvas-toolbar ${hidden ? "toolbar-hidden" : ""}`}>

      <div className="tool-group">

        <button
          title="Pencil"
          className={tool === "pencil" ? "active-tool" : ""}
          onClick={() => setTool("pencil")}
        >
          Pencil
        </button>

        <button
          title="Eraser"
          className={tool === "eraser" ? "active-tool" : ""}
          onClick={() => setTool("eraser")}
        >
          Eraser
        </button>

        <button
          title="Fill"
          className={tool === "fill" ? "active-tool" : ""}
          onClick={() => setTool("fill")}
        >
          Fill
        </button>

        <button
  title="Undo"
  onClick={onUndo}
>
  Undo
</button>

<button
  title="Clear"
  onClick={onClear}
>
  Clear
</button>

      </div>

      <div className="brush-group">

        <button
          title="Small"
          className={size === 3 ? "active-tool" : ""}
          onClick={() => setSize(3)}
        >
          •
        </button>

        <button
          title="Medium"
          className={size === 7 ? "active-tool" : ""}
          onClick={() => setSize(7)}
        >
          ●
        </button>

        <button
          title="Large"
          className={size === 14 ? "active-tool" : ""}
          onClick={() => setSize(14)}
        >
          ⬤
        </button>

      </div>

      <div className="color-palette">

        {colors.map((item) => (
          <button
            key={item.name}
            className={`${item.name} ${
              color === item.value ? "active-color" : ""
            }`}
            title={item.name}
            onClick={() => {
              setColor(item.value);
              setTool("pencil");
            }}
          />
        ))}

      </div>

    </div>
  );
}

export default CanvasToolbar;