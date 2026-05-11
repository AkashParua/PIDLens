/* Wireframe kit — shared chrome + primitives used by every screen variant. */

const NAV_STEPS = [
  { id: "parse",   num: "1", label: "Parse"        },
  { id: "triage",  num: "2", label: "Triage"       },
  { id: "annot",   num: "3", label: "Annotate"     },
  { id: "pre",     num: "4", label: "Preprocess"   },
  { id: "aug",     num: "5", label: "Augment"      },
  { id: "split",   num: "6", label: "Split"        },
  { id: "train",   num: "7", label: "Train"        },
  { id: "models",  num: "8", label: "Models"       },
  { id: "integ",   num: "9", label: "Integrations" },
];

function Win({ title, path, active, children }) {
  return (
    <div className="wf-win">
      <div className="wf-titlebar">
        <div className="wf-traffic"><span /><span /><span /></div>
        <div className="wf-title">{title}</div>
        <div className="wf-meta">{path || "—"}</div>
      </div>
      <div className="wf-shell">
        <Sidebar active={active} />
        {children}
      </div>
      <Statusbar />
    </div>
  );
}

function Sidebar({ active }) {
  return (
    <aside className="wf-side">
      <div className="wf-side-brand">
        annot.local
        <small>v0.4 · ~/datasets/cells</small>
      </div>
      <nav className="wf-nav">
        {NAV_STEPS.map((s, i) => {
          const idx = NAV_STEPS.findIndex(x => x.id === active);
          const cls = s.id === active ? "active" : (i < idx ? "done" : "");
          return (
            <div key={s.id} className={`wf-nav-item ${cls}`}>
              <span className="num">{s.num}</span>{s.label}
            </div>
          );
        })}
      </nav>
      <div className="wf-side-foot">
        642 imgs · 318 ann
      </div>
    </aside>
  );
}

function Statusbar({ extra }) {
  return (
    <div className="wf-statusbar">
      <span>ready</span>
      <span>•</span>
      <span>cwd ~/datasets/cells</span>
      <span>•</span>
      <span>yolov8</span>
      <div className="wf-spacer" />
      {extra}
      <span>cpu 14%</span>
      <span>•</span>
      <span>gpu idle</span>
    </div>
  );
}

function Toolbar({ children }) {
  return <div className="wf-toolbar">{children}</div>;
}

function Btn({ children, primary, ghost, sm, lg, kbd, style }) {
  const cls = ["wf-btn", primary && "primary", ghost && "ghost", sm && "sm", lg && "lg"].filter(Boolean).join(" ");
  return <button className={cls} style={style}>{children}{kbd && <span className="kbd">{kbd}</span>}</button>;
}

function Input({ value, placeholder, path, style }) {
  return <input className={`wf-input ${path ? "path" : ""}`} defaultValue={value} placeholder={placeholder} readOnly style={style} />;
}

function Ph({ label, style, className = "" }) {
  return <div className={`wf-ph ${className}`} style={style}>{label}</div>;
}

function Panel({ title, meta, children, style, bodyStyle, noBody }) {
  return (
    <div className="wf-panel" style={style}>
      {title && (
        <div className="wf-panel-h">
          <span>{title}</span>{meta && <small>{meta}</small>}
        </div>
      )}
      {!noBody && <div className="wf-panel-b" style={bodyStyle}>{children}</div>}
      {noBody && children}
    </div>
  );
}

function Chip({ children, solid, dot, style }) {
  const cls = ["wf-chip", solid && "solid", dot && "dot"].filter(Boolean).join(" ");
  return <span className={cls} style={style}>{children}</span>;
}

function Bbox({ x, y, w, h, label, dash, selected }) {
  return (
    <div className={`wf-bbox ${dash ? "dash" : ""}`} style={{ left: x, top: y, width: w, height: h }}>
      {label && <span className="lbl">{label}</span>}
      {selected && <><span className="handle tl"/><span className="handle tr"/><span className="handle bl"/><span className="handle br"/></>}
    </div>
  );
}

function Slider({ value = 0.5, style }) {
  return (
    <div className="wf-slider" style={style}>
      <span className="fill" style={{ width: `${value * 100}%` }} />
      <span className="knob" style={{ left: `${value * 100}%` }} />
    </div>
  );
}

// A canvas area showing one image placeholder with bboxes laid over it.
function ImageCanvas({ children, style, label = "img · 1920×1080", aspect }) {
  return (
    <div style={{ position: "relative", flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: 20, background: "var(--paper-2)", ...style }}>
      <div style={{ position: "relative", width: aspect ? "auto" : "100%", height: "100%", maxHeight: "100%", aspectRatio: aspect || "16/10", margin: "auto" }}>
        <Ph label={label} style={{ position: "absolute", inset: 0 }} />
        {children}
      </div>
    </div>
  );
}

// Bar chart placeholder
function Bars({ data, faded, style }) {
  return (
    <div className="wf-bars" style={style}>
      {data.map((v, i) => (
        <i key={i} className={faded && faded.includes(i) ? "faded" : ""} style={{ height: `${v}%` }} />
      ))}
    </div>
  );
}

// Line chart (simple svg polyline)
function LineChart({ points, style }) {
  // points: array of [x%, y%]; we'll fit to 100x100
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ");
  return (
    <div className="wf-ph chart" style={style}>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <path d={path} fill="none" stroke="var(--ink)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      </svg>
    </div>
  );
}

// Confusion matrix
function Matrix({ size = 5, style }) {
  const cells = [];
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const isDiag = r === c;
      const v = isDiag ? 0.7 + Math.random() * 0.25 : Math.random() * 0.15;
      cells.push(
        <div key={`${r}-${c}`} style={{ background: `rgba(0,0,0,${v.toFixed(2)})`, color: v > 0.4 ? "var(--paper)" : "var(--ink)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: 9 }}>
          {Math.round(v * 100)}
        </div>
      );
    }
  }
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${size}, 1fr)`, gap: 1, background: "var(--line)", border: "1px solid var(--line)", ...style }}>
      {cells}
    </div>
  );
}

// Thumbnail strip across the bottom of the annotation screen
function ThumbStrip({ count = 22, selectedIdx = 4, emptyEvery = 5 }) {
  const items = [];
  for (let i = 0; i < count; i++) {
    const sel = i === selectedIdx;
    const empty = i % emptyEvery === 3;
    items.push(
      <div key={i} className={`t ${sel ? "sel" : ""} ${empty ? "empty" : ""}`}>
        <Ph label="" />
        <span className="lbl">{String(i + 1).padStart(3, "0")}</span>
      </div>
    );
  }
  return <div className="wf-strip">{items}</div>;
}

// Class swatches for annotation
function ClassList({ classes, sel = 0 }) {
  return (
    <div>
      {classes.map((c, i) => (
        <div key={c.name} className="wf-class-row" style={i === sel ? { background: "var(--paper-2)" } : null}>
          <span className="sw" style={{ background: i % 2 === 0 ? "var(--ink)" : "var(--paper)" }} />
          <span>{c.name}</span>
          <span style={{ color: "var(--ink-3)", fontFamily: "var(--font-mono)", fontSize: 10 }}>{c.count}</span>
          <span className="kbd">{i + 1}</span>
        </div>
      ))}
    </div>
  );
}

// Export to window for cross-file use
Object.assign(window, {
  Win, Sidebar, Statusbar, Toolbar, Btn, Input, Ph, Panel, Chip, Bbox,
  Slider, ImageCanvas, Bars, LineChart, Matrix, ThumbStrip, ClassList,
  NAV_STEPS,
});
