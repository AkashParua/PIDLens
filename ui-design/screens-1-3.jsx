/* Screens 1-3: Parse landing, Image triage, Annotation canvas */

// ============ 1. PARSE / DIRECTORY PICKER ============

function Parse_V1() {
  return (
    <Win title="Parse directory" path="~/datasets/cells" active="parse">
      <main className="wf-main">
        <Toolbar>
          <Btn>← Back</Btn>
          <div className="wf-divider" />
          <Input path value="/Users/me/datasets/cells" />
          <Btn>Browse…</Btn>
          <Btn primary>Parse</Btn>
          <div className="wf-spacer" />
          <Chip dot>watching</Chip>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 12, padding: 16, minHeight: 0 }}>
          <Panel title="Drop directory or click to browse" meta="recursive">
            <div className="wf-ph" style={{ height: 360, border: "2px dashed var(--line)", flexDirection: "column", gap: 14 }}>
              <div style={{ fontSize: 22, color: "var(--ink-2)", fontFamily: "var(--font-ui)" }}>⤓</div>
              <div style={{ fontSize: 12, color: "var(--ink-2)", fontFamily: "var(--font-ui)" }}>drop a folder of images here</div>
              <div className="wf-meta-line">expects: *.jpg *.png · optional /labels/*.txt (yolov8)</div>
            </div>
            <div style={{ display: "flex", gap: 6, marginTop: 12, flexWrap: "wrap" }}>
              <Chip>↺ recursive</Chip><Chip>+ watch for new files</Chip><Chip>read existing labels</Chip>
            </div>
          </Panel>
          <Panel title="Recent" meta="9 directories">
            <div className="wf-list">
              {[
                ["~/datasets/cells",        "642 imgs", "318 ann"],
                ["~/work/microscopy/run3",  "1.2k imgs", "1.2k ann"],
                ["~/datasets/holdout-v2",   "84 imgs", "0 ann"],
                ["~/scans/ocr-batch",       "210 imgs", "210 ann"],
                ["~/datasets/cells-v0",     "642 imgs", "642 ann"],
                ["~/tmp/unsorted",          "37 imgs", "—"],
              ].map((r, i) => (
                <div key={i} className={`wf-list-row ${i === 0 ? "sel" : ""}`}>
                  <span style={{ flex: 1 }} className="mono">{r[0]}</span>
                  <span className="mono">{r[1]}</span>
                  <span className="mono">{r[2]}</span>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </main>
    </Win>
  );
}

function Parse_V2() {
  return (
    <Win title="Parse directory" path="~/datasets/cells" active="parse">
      <main className="wf-main">
        <Toolbar>
          <Btn>↑ Up</Btn>
          <Input path value="/Users/me/datasets/cells" />
          <Btn>Refresh</Btn>
          <div className="wf-spacer" />
          <Btn primary>Parse · 642 files</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "260px 1fr", minHeight: 0 }}>
          <Panel style={{ borderTop: 0, borderLeft: 0, borderBottom: 0 }} noBody>
            <div style={{ padding: "8px 0" }}>
              {[
                { d: 0, n: "datasets", o: true },
                { d: 1, n: "cells", o: true, sel: true },
                { d: 2, n: "images", o: true },
                { d: 3, n: "001.jpg" },{ d: 3, n: "002.jpg" },{ d: 3, n: "003.jpg" },{ d: 3, n: "…" },
                { d: 2, n: "labels", o: true },
                { d: 3, n: "001.txt" },{ d: 3, n: "002.txt" },{ d: 3, n: "…" },
                { d: 2, n: "data.yaml" },
                { d: 1, n: "holdout-v2" },
                { d: 1, n: "cells-v0" },
                { d: 0, n: "scans" },
              ].map((r, i) => (
                <div key={i} className={`wf-tree-row ${r.sel ? "sel" : ""}`}>
                  <span className="ind" style={{ width: r.d * 10 }} />
                  <span className="ico">{r.n.includes(".") ? "•" : r.o ? "▾" : "▸"}</span>
                  <span>{r.n}</span>
                </div>
              ))}
            </div>
          </Panel>
          <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
            <div style={{ padding: 12, display: "flex", gap: 12, borderBottom: "1px solid var(--line)" }}>
              <StatBlock label="images" value="642" sub=".jpg .png" />
              <StatBlock label="with labels" value="318" sub="49.5%" />
              <StatBlock label="un-annotated" value="324" sub="needs work" />
              <StatBlock label="classes detected" value="4" sub="data.yaml" />
              <StatBlock label="orphan labels" value="2" sub="missing img" />
            </div>
            <div style={{ flex: 1, overflow: "hidden", padding: 0 }}>
              <div className="wf-panel-h" style={{ borderBottom: "1px solid var(--line)" }}>
                <span>Parse preview</span><small>showing 12 of 642</small>
              </div>
              <div className="wf-list">
                {[
                  ["001.jpg", "1920×1080", "✓ 3 boxes", "cell, nucleus"],
                  ["002.jpg", "1920×1080", "✓ 1 box", "cell"],
                  ["003.jpg", "1920×1080", "— no labels", "—"],
                  ["004.jpg", "1920×1080", "✓ 5 boxes", "cell, debris"],
                  ["005.jpg", "1024×768",  "— no labels", "—"],
                  ["006.jpg", "1920×1080", "⚠ orphan label", "—"],
                  ["007.jpg", "1920×1080", "✓ 2 boxes", "nucleus"],
                  ["008.jpg", "1920×1080", "— no labels", "—"],
                  ["009.jpg", "1920×1080", "✓ 4 boxes", "cell"],
                ].map((r, i) => (
                  <div key={i} className="wf-list-row">
                    <span className="mono" style={{ width: 80 }}>{r[0]}</span>
                    <span className="mono" style={{ width: 80, color: "var(--ink-3)" }}>{r[1]}</span>
                    <span style={{ width: 130 }}>{r[2]}</span>
                    <span style={{ flex: 1, color: "var(--ink-2)" }}>{r[3]}</span>
                    <Btn sm>open in directory</Btn>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </Win>
  );
}

function StatBlock({ label, value, sub }) {
  return (
    <div style={{ flex: 1, border: "1px solid var(--line)", padding: 10, background: "var(--paper)" }}>
      <div style={{ fontSize: 9, textTransform: "uppercase", color: "var(--ink-3)", letterSpacing: ".08em", fontFamily: "var(--font-mono)" }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 600, margin: "2px 0", fontFamily: "var(--font-ui)" }}>{value}</div>
      <div className="wf-meta-line">{sub}</div>
    </div>
  );
}

function Parse_V3() {
  return (
    <Win title="annot.local — parse" path="~/datasets/cells" active="parse">
      <main className="wf-main">
        <div style={{ padding: "20px 22px 12px", borderBottom: "1px solid var(--line-2)" }}>
          <div className="wf-h2" style={{ marginBottom: 10 }}>Step 1 — parse directory</div>
          <div className="wf-h1" style={{ marginBottom: 12 }}>Point at a folder. We'll find images & existing labels.</div>
          <div style={{ display: "flex", gap: 6 }}>
            <Input path value="~/datasets/cells" style={{ height: 32, fontSize: 12 }} />
            <Btn lg>browse</Btn>
            <Btn lg primary>parse →</Btn>
          </div>
          <div style={{ display: "flex", gap: 14, marginTop: 10 }}>
            <label style={{ display: "flex", gap: 5, alignItems: "center", fontSize: 11, color: "var(--ink-2)" }}><input type="checkbox" defaultChecked readOnly /> recursive</label>
            <label style={{ display: "flex", gap: 5, alignItems: "center", fontSize: 11, color: "var(--ink-2)" }}><input type="checkbox" defaultChecked readOnly /> read existing yolov8 labels</label>
            <label style={{ display: "flex", gap: 5, alignItems: "center", fontSize: 11, color: "var(--ink-2)" }}><input type="checkbox" readOnly /> watch for new files</label>
          </div>
        </div>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 0, minHeight: 0 }}>
          <ParseSummaryCol title="found" rows={[["images", "642"], [".jpg", "601"], [".png", "41"], ["folders", "3"]]} />
          <ParseSummaryCol title="annotations" rows={[["labels present", "318"], ["classes", "4"], ["avg boxes/img", "2.7"], ["orphan labels", "2"]]} />
          <ParseSummaryCol title="warnings" rows={[["un-annotated", "324"], ["odd dims", "12"], ["dupe md5", "0"], ["empty txt", "1"]]} accent />
        </div>
        <div style={{ borderTop: "1px solid var(--line)", padding: "10px 22px", display: "flex", alignItems: "center", gap: 8 }}>
          <span className="wf-meta-line">last parsed 2 min ago · ~/datasets/cells</span>
          <div className="wf-spacer" />
          <Btn>show in directory</Btn>
          <Btn primary>continue to triage →</Btn>
        </div>
      </main>
    </Win>
  );
}

function ParseSummaryCol({ title, rows, accent }) {
  return (
    <div style={{ borderRight: "1px solid var(--line-2)", padding: "16px 22px" }}>
      <div className="wf-h2" style={{ marginBottom: 12, color: accent ? "var(--ink)" : "var(--ink-2)" }}>{title}</div>
      {rows.map(([k, v], i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "8px 0", borderTop: i === 0 ? "none" : "1px solid var(--line-2)" }}>
          <span style={{ fontSize: 12, color: "var(--ink-2)" }}>{k}</span>
          <span style={{ fontSize: 18, fontWeight: 600, fontFamily: "var(--font-mono)" }}>{v}</span>
        </div>
      ))}
    </div>
  );
}

// ============ 2. IMAGE GALLERY / TRIAGE ============

function Triage_V1() {
  return (
    <Win title="Image triage" path="~/datasets/cells · 642 imgs" active="triage">
      <main className="wf-main">
        <Toolbar>
          <Chip solid>all 642</Chip>
          <Chip>annotated 318</Chip>
          <Chip>un-annotated 324</Chip>
          <Chip>orphan 2</Chip>
          <Chip>flagged 7</Chip>
          <div className="wf-divider" />
          <Btn ghost>sort: name ↓</Btn>
          <Btn ghost>thumb: m</Btn>
          <div className="wf-spacer" />
          <Input placeholder="filter…" style={{ width: 180 }} />
          <Btn primary>start annotating →</Btn>
        </Toolbar>
        <div style={{ flex: 1, overflow: "hidden", padding: 12, display: "grid", gridTemplateColumns: "repeat(8, 1fr)", gridAutoRows: "104px", gap: 8 }}>
          {Array.from({ length: 32 }).map((_, i) => {
            const empty = [2,5,8,11,14,17,19,22,26,30].includes(i);
            const flagged = [4, 18].includes(i);
            return (
              <div key={i} style={{ position: "relative" }}>
                <Ph label="" style={{ position: "absolute", inset: 0 }} className={empty ? "" : "thumb"} />
                {!empty && (
                  <>
                    <Bbox x={12} y={14} w={28} h={20} />
                    <Bbox x={50} y={40} w={36} h={28} />
                  </>
                )}
                <div style={{ position: "absolute", top: 4, left: 4, display: "flex", gap: 3 }}>
                  <span style={{ background: empty ? "var(--paper)" : "var(--ink)", color: empty ? "var(--ink-2)" : "var(--paper)", border: "1px solid var(--line)", fontSize: 9, padding: "0 4px", fontFamily: "var(--font-mono)" }}>{empty ? "—" : `${(i % 4) + 1} ▢`}</span>
                  {flagged && <span style={{ background: "var(--paper)", color: "var(--ink)", border: "1px solid var(--ink)", fontSize: 9, padding: "0 4px", fontFamily: "var(--font-mono)" }}>!</span>}
                </div>
                <div style={{ position: "absolute", bottom: 4, left: 4, fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--ink-3)", background: "var(--paper)", padding: "0 3px", border: "1px solid var(--line)" }}>{String(i + 1).padStart(3, "0")}.jpg</div>
              </div>
            );
          })}
        </div>
      </main>
    </Win>
  );
}

function Triage_V2() {
  const rows = [
    ["001.jpg", "1920×1080", 3, "cell, nucleus", "✓"],
    ["002.jpg", "1920×1080", 1, "cell", "✓"],
    ["003.jpg", "1920×1080", 0, "—", "—"],
    ["004.jpg", "1920×1080", 5, "cell, debris", "✓"],
    ["005.jpg", "1024×768",  0, "—", "—"],
    ["006.jpg", "1920×1080", 0, "—", "⚠"],
    ["007.jpg", "1920×1080", 2, "nucleus", "✓"],
    ["008.jpg", "1920×1080", 0, "—", "—"],
    ["009.jpg", "1920×1080", 4, "cell", "✓"],
    ["010.jpg", "1920×1080", 0, "—", "—"],
    ["011.jpg", "1920×1080", 6, "cell, nucleus, debris", "✓"],
    ["012.jpg", "1920×1080", 0, "—", "—"],
  ];
  return (
    <Win title="Image triage — list" path="~/datasets/cells" active="triage">
      <main className="wf-main">
        <Toolbar>
          <Btn ghost>view: list</Btn><Btn ghost>view: grid</Btn>
          <div className="wf-divider" />
          <Chip>filter: all</Chip><Chip>class: any</Chip><Chip>≥1 box</Chip>
          <div className="wf-spacer" />
          <Btn>export csv</Btn>
          <Btn primary>annotate next un-annotated</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.4fr 1fr", minHeight: 0 }}>
          <div style={{ overflow: "hidden", display: "flex", flexDirection: "column", borderRight: "1px solid var(--line)" }}>
            <div className="wf-list-row" style={{ background: "var(--paper-2)", fontWeight: 500, color: "var(--ink-2)" }}>
              <span style={{ width: 24 }}><input type="checkbox" readOnly /></span>
              <span style={{ width: 40 }} />
              <span style={{ width: 90 }}>file</span>
              <span style={{ width: 80 }}>dims</span>
              <span style={{ width: 50 }}>boxes</span>
              <span style={{ flex: 1 }}>classes</span>
              <span style={{ width: 30 }}>state</span>
            </div>
            <div className="wf-list" style={{ overflow: "auto", flex: 1 }}>
              {rows.map((r, i) => (
                <div key={i} className={`wf-list-row ${i === 3 ? "sel" : ""}`}>
                  <span style={{ width: 24 }}><input type="checkbox" readOnly /></span>
                  <Ph label="" style={{ width: 34, height: 24 }} />
                  <span className="mono" style={{ width: 90 }}>{r[0]}</span>
                  <span className="mono" style={{ width: 80, color: "var(--ink-3)" }}>{r[1]}</span>
                  <span className="mono" style={{ width: 50 }}>{r[2]}</span>
                  <span style={{ flex: 1, color: "var(--ink-2)" }}>{r[3]}</span>
                  <span className="mono" style={{ width: 30 }}>{r[4]}</span>
                </div>
              ))}
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
            <div style={{ padding: 14, borderBottom: "1px solid var(--line)" }}>
              <div className="wf-h1" style={{ marginBottom: 4 }}>004.jpg</div>
              <div className="wf-meta-line">1920×1080 · 5 boxes · cell, debris · last edited 2d ago</div>
            </div>
            <div style={{ flex: 1, position: "relative", padding: 14, background: "var(--paper-2)" }}>
              <div style={{ position: "relative", width: "100%", height: "100%" }}>
                <Ph label="preview · 004.jpg" style={{ position: "absolute", inset: 0 }} />
                <Bbox x={40} y={60} w={120} h={84} label="cell" />
                <Bbox x={180} y={130} w={90} h={70} label="cell" />
                <Bbox x={260} y={40} w={64} h={50} label="debris" />
              </div>
            </div>
            <div style={{ padding: 10, borderTop: "1px solid var(--line)", display: "flex", gap: 6 }}>
              <Btn>show in directory</Btn>
              <Btn>flag</Btn>
              <Btn>remove from set</Btn>
              <div className="wf-spacer" />
              <Btn primary>open in annotator →</Btn>
            </div>
          </div>
        </div>
      </main>
    </Win>
  );
}

function Triage_V3() {
  return (
    <Win title="Image triage — gallery" path="~/datasets/cells" active="triage">
      <main className="wf-main">
        <Toolbar>
          <Input placeholder="filter by name or class…" style={{ width: 240 }} />
          <div className="wf-divider" />
          <Btn ghost>group by: status</Btn>
          <div className="wf-spacer" />
          <span className="wf-meta-line">selected 0</span>
          <Btn>bulk remove</Btn>
          <Btn primary>start session</Btn>
        </Toolbar>
        <div style={{ flex: 1, overflow: "hidden", padding: "14px 18px" }}>
          <SectionRow title="un-annotated · 324" />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gridAutoRows: "70px", gap: 6, marginBottom: 18 }}>
            {Array.from({ length: 24 }).map((_, i) => (
              <div key={i} style={{ position: "relative" }}>
                <Ph label="" style={{ position: "absolute", inset: 0 }} />
                <span style={{ position: "absolute", top: 3, left: 3, fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--ink-3)", background: "var(--paper)", padding: "0 3px" }}>{String(100 + i).padStart(3, "0")}</span>
              </div>
            ))}
          </div>
          <SectionRow title="annotated · 318" />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gridAutoRows: "70px", gap: 6 }}>
            {Array.from({ length: 24 }).map((_, i) => (
              <div key={i} style={{ position: "relative" }}>
                <Ph label="" style={{ position: "absolute", inset: 0 }} />
                <Bbox x={6} y={10} w={20} h={14} />
                <Bbox x={32} y={28} w={26} h={20} />
                <span style={{ position: "absolute", top: 3, left: 3, fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--paper)", background: "var(--ink)", padding: "0 3px" }}>{(i % 5) + 1}▢</span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </Win>
  );
}

function SectionRow({ title }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, margin: "0 0 8px" }}>
      <span className="wf-h2">{title}</span>
      <span style={{ flex: 1, height: 1, background: "var(--line-2)" }} />
      <Btn sm ghost>collapse</Btn>
    </div>
  );
}

// ============ 3. ANNOTATION CANVAS ============

const CLASSES = [
  { name: "cell",     count: 482 },
  { name: "nucleus",  count: 213 },
  { name: "debris",   count: 64 },
  { name: "artifact", count: 9 },
];

function Annot_V1() {
  return (
    <Win title="Annotate · 004.jpg" path="img 004 / 642" active="annot">
      <main className="wf-main">
        <Toolbar>
          <Btn>◀ prev</Btn><Btn>next ▶</Btn>
          <div className="wf-divider" />
          <Btn>↺ undo</Btn><Btn>↻ redo</Btn>
          <div className="wf-divider" />
          <Btn ghost kbd="b">▢ box</Btn>
          <Btn ghost kbd="v">↖ select</Btn>
          <Btn ghost kbd="h">✋ pan</Btn>
          <div className="wf-divider" />
          <span className="wf-meta-line">004.jpg · 1920×1080 · 5 boxes</span>
          <div className="wf-spacer" />
          <Btn>show in directory</Btn>
          <Btn>remove image</Btn>
          <Btn primary>save · ⌘S</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
          {/* left: classes */}
          <div style={{ width: 168, borderRight: "1px solid var(--line)", display: "flex", flexDirection: "column", minHeight: 0 }}>
            <div className="wf-panel-h"><span>Classes</span><small>4</small></div>
            <ClassList classes={CLASSES} sel={0} />
            <div style={{ padding: 10, borderTop: "1px solid var(--line-2)" }}>
              <Btn sm style={{ width: "100%" }}>+ add class</Btn>
            </div>
            <div className="wf-panel-h" style={{ borderTop: "1px solid var(--line)" }}><span>Shortcuts</span></div>
            <div style={{ padding: 10, fontSize: 10, color: "var(--ink-2)", lineHeight: 1.8 }}>
              <div><span style={{ fontFamily: "var(--font-mono)" }}>1–4</span> pick class</div>
              <div><span style={{ fontFamily: "var(--font-mono)" }}>b</span> draw box</div>
              <div><span style={{ fontFamily: "var(--font-mono)" }}>del</span> remove box</div>
              <div><span style={{ fontFamily: "var(--font-mono)" }}>← →</span> prev / next img</div>
              <div><span style={{ fontFamily: "var(--font-mono)" }}>⌘D</span> dir of img</div>
            </div>
          </div>
          {/* canvas */}
          <ImageCanvas label="004.jpg · 1920×1080">
            <Bbox x="10%" y="20%" w="22%" h="36%" label="cell" />
            <Bbox x="36%" y="44%" w="18%" h="28%" label="cell" />
            <Bbox x="58%" y="14%" w="14%" h="22%" label="debris" selected />
            <Bbox x="74%" y="46%" w="20%" h="34%" label="cell" dash />
          </ImageCanvas>
          {/* right: attrs */}
          <div style={{ width: 196, borderLeft: "1px solid var(--line)", display: "flex", flexDirection: "column" }}>
            <div className="wf-panel-h"><span>Selected box</span><small>#3</small></div>
            <div style={{ padding: 10, display: "flex", flexDirection: "column", gap: 8 }}>
              <Row k="class" v="debris" />
              <Row k="x · y" v="1112 · 152" />
              <Row k="w · h" v="269 · 238" />
              <Row k="area" v="64 022 px" />
              <Row k="iou (auto)" v="—" />
              <div style={{ borderTop: "1px solid var(--line-2)", paddingTop: 8, marginTop: 4 }}>
                <Btn sm style={{ width: "100%" }}>delete · del</Btn>
              </div>
            </div>
            <div className="wf-panel-h" style={{ borderTop: "1px solid var(--line)" }}><span>This image — boxes</span><small>4</small></div>
            <div className="wf-list">
              {["cell", "cell", "debris", "cell"].map((c, i) => (
                <div key={i} className={`wf-list-row ${i === 2 ? "sel" : ""}`} style={{ padding: "5px 10px" }}>
                  <span className="mono">#{i + 1}</span>
                  <span style={{ flex: 1 }}>{c}</span>
                  <span className="mono" style={{ color: "var(--ink-3)" }}>{200 + i * 70}px</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <ThumbStrip count={20} selectedIdx={3} />
      </main>
    </Win>
  );
}

function Row({ k, v }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 8, fontSize: 11 }}>
      <span style={{ color: "var(--ink-3)", width: 70, fontFamily: "var(--font-mono)", fontSize: 10 }}>{k}</span>
      <span style={{ flex: 1, fontFamily: "var(--font-mono)" }}>{v}</span>
    </div>
  );
}

function Annot_V2() {
  return (
    <Win title="Annotate · 004.jpg" path="img 004 / 642" active="annot">
      <main className="wf-main">
        <Toolbar>
          <div style={{ display: "flex", gap: 0, border: "1px solid var(--line)", borderRadius: 3 }}>
            <Btn ghost kbd="b" style={{ borderRadius: 0, borderRight: "1px solid var(--line)" }}>▢ box</Btn>
            <Btn ghost kbd="v" style={{ borderRadius: 0, borderRight: "1px solid var(--line)" }}>↖</Btn>
            <Btn ghost kbd="h" style={{ borderRadius: 0 }}>✋</Btn>
          </div>
          <div className="wf-divider" />
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-3)" }}>class</span>
          {CLASSES.map((c, i) => (
            <Chip key={c.name} solid={i === 0} dot>{i + 1} {c.name}</Chip>
          ))}
          <div className="wf-spacer" />
          <Btn>⌘D show in directory</Btn>
          <Btn>remove image</Btn>
          <Btn primary>save · ⌘S</Btn>
        </Toolbar>
        <ImageCanvas label="004.jpg · 1920×1080" style={{ flex: "1 1 auto" }}>
          <Bbox x="8%" y="22%" w="24%" h="40%" label="cell" />
          <Bbox x="38%" y="48%" w="20%" h="30%" label="cell" />
          <Bbox x="62%" y="12%" w="16%" h="24%" label="debris" selected />
          <Bbox x="78%" y="50%" w="18%" h="30%" label="cell" />
          {/* live cursor draw indicator */}
          <div style={{ position: "absolute", left: "40%", top: "20%", width: 1, height: "60%", background: "var(--ink)", opacity: .3 }} />
          <div style={{ position: "absolute", left: "8%", top: "30%", height: 1, width: "84%", background: "var(--ink)", opacity: .3 }} />
        </ImageCanvas>
        <div style={{ display: "flex", borderTop: "1px solid var(--line)" }}>
          <div style={{ flex: 1, display: "flex", alignItems: "center", padding: "6px 12px", gap: 12, borderRight: "1px solid var(--line)", fontSize: 11, color: "var(--ink-2)" }}>
            <span className="wf-meta-line">img 4 / 642</span>
            <span className="wf-meta-line">·</span>
            <span className="wf-meta-line">4 boxes</span>
            <span className="wf-meta-line">·</span>
            <span className="wf-meta-line">selected: debris #3 · 269×238 @ 1112,152</span>
            <div className="wf-spacer" />
            <Btn sm>◀</Btn><Btn sm>▶</Btn>
          </div>
        </div>
        <ThumbStrip count={26} selectedIdx={3} />
      </main>
    </Win>
  );
}

function Annot_V3() {
  // Floating tool palette, max canvas
  return (
    <Win title="Annotate" path="004.jpg · img 4/642" active="annot">
      <main className="wf-main" style={{ position: "relative" }}>
        <ImageCanvas label="004.jpg · 1920×1080" style={{ padding: 0 }}>
          <Bbox x="10%" y="18%" w="26%" h="44%" label="cell" />
          <Bbox x="42%" y="48%" w="20%" h="30%" label="cell" selected />
          <Bbox x="66%" y="12%" w="18%" h="26%" label="debris" />
          <Bbox x="78%" y="56%" w="18%" h="30%" label="cell" />
        </ImageCanvas>
        {/* Floating top-left: classes */}
        <div style={{ position: "absolute", top: 12, left: 12, width: 152, background: "var(--paper)", border: "1px solid var(--line)", padding: 8 }}>
          <div style={{ fontSize: 10, color: "var(--ink-3)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 6, fontFamily: "var(--font-mono)" }}>class · 1–4</div>
          {CLASSES.map((c, i) => (
            <div key={c.name} style={{ display: "flex", alignItems: "center", gap: 6, padding: "3px 0", background: i === 1 ? "var(--paper-2)" : "transparent", margin: "0 -4px", paddingLeft: 4, paddingRight: 4, fontSize: 11 }}>
              <span style={{ width: 8, height: 8, background: i === 1 ? "var(--ink)" : "transparent", border: "1px solid var(--ink)" }} />
              <span>{c.name}</span>
              <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--ink-3)" }}>{i + 1}</span>
            </div>
          ))}
        </div>
        {/* Floating top-right: tools */}
        <div style={{ position: "absolute", top: 12, right: 12, display: "flex", flexDirection: "column", gap: 4, background: "var(--paper)", border: "1px solid var(--line)", padding: 4 }}>
          {[["▢", "b"], ["↖", "v"], ["✋", "h"], ["⌫", "del"], ["⤓", "s"]].map(([t, k]) => (
            <div key={k} style={{ display: "flex", alignItems: "center", gap: 6, padding: "3px 6px", fontSize: 11 }}>
              <span style={{ width: 14, textAlign: "center" }}>{t}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--ink-3)" }}>{k}</span>
            </div>
          ))}
        </div>
        {/* Floating bottom-left: status */}
        <div style={{ position: "absolute", bottom: 12, left: 12, background: "var(--paper)", border: "1px solid var(--line)", padding: "6px 10px", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-2)" }}>
          004.jpg · 1920×1080 · 4 boxes · sel #2 cell
        </div>
        {/* Floating bottom-right: navigation */}
        <div style={{ position: "absolute", bottom: 12, right: 12, display: "flex", gap: 4 }}>
          <Btn>◀</Btn>
          <Btn>▶</Btn>
          <Btn>⌘D dir</Btn>
          <Btn primary>save</Btn>
        </div>
      </main>
    </Win>
  );
}

Object.assign(window, {
  Parse_V1, Parse_V2, Parse_V3,
  Triage_V1, Triage_V2, Triage_V3,
  Annot_V1, Annot_V2, Annot_V3,
});
