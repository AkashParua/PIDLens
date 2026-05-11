/* Screens 4-6: Preprocessing pipeline, Augmentation, Split */

// ============ 4. PREPROCESSING / MORPHOLOGICAL OPS ============

const PRE_OPS = [
  { name: "Resize",       params: "1280 × 720 · bilinear", scope: "global" },
  { name: "Grayscale",    params: "luma 709",              scope: "global" },
  { name: "Threshold",    params: "otsu · invert",         scope: "global" },
  { name: "Dilate",       params: "3×3 cross · iter 2",    scope: "global" },
  { name: "cv2.fillPoly", params: "contours ≥ 80 px²",     scope: "local"  },
  { name: "Morph close",  params: "5×5 ellipse · iter 1",  scope: "box 3"  },
];

function Pre_V1() {
  return (
    <Win title="Preprocess pipeline" path="version v3 (unsaved)" active="pre">
      <main className="wf-main">
        <Toolbar>
          <Btn>+ op</Btn>
          <Btn>↑ load .yaml</Btn>
          <Btn>save .yaml</Btn>
          <div className="wf-divider" />
          <span className="wf-meta-line">version: v3 · 6 ops · scope global+local</span>
          <div className="wf-spacer" />
          <Btn>preview</Btn>
          <Btn primary>apply → write versioned dir</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "340px 1fr 220px", minHeight: 0 }}>
          {/* Card stack */}
          <div style={{ borderRight: "1px solid var(--line)", overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div className="wf-panel-h"><span>Pipeline</span><small>drag to reorder</small></div>
            <div style={{ padding: 10, display: "flex", flexDirection: "column", gap: 6, overflow: "auto", flex: 1 }}>
              {PRE_OPS.map((o, i) => (
                <div key={i} className="wf-card" style={i === 3 ? { borderColor: "var(--ink)" } : null}>
                  <div className="grip" />
                  <div className="body">
                    <div className="h">
                      <span style={{ width: 14, height: 14, border: "1px solid var(--ink)", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontFamily: "var(--font-mono)" }}>{i + 1}</span>
                      {o.name}
                      <small>{o.scope}</small>
                    </div>
                    <div className="wf-meta-line">{o.params}</div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", borderLeft: "1px solid var(--line-2)" }}>
                    <button className="wf-btn ghost sm" style={{ borderRadius: 0, height: 18, padding: "0 8px" }}>edit</button>
                    <button className="wf-btn ghost sm" style={{ borderRadius: 0, height: 18, padding: "0 8px" }}>×</button>
                  </div>
                </div>
              ))}
              <button className="wf-btn" style={{ borderStyle: "dashed", height: 32 }}>+ add operation</button>
            </div>
          </div>
          {/* Preview big */}
          <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
            <div style={{ padding: "10px 12px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", gap: 10 }}>
              <span className="wf-h2">live preview</span>
              <Chip>after step 4 · dilate</Chip>
              <div className="wf-spacer" />
              <Btn sm>◀ before</Btn><Btn sm>after ▶</Btn>
              <Btn sm>fit</Btn>
            </div>
            <div style={{ flex: 1, padding: 14, background: "var(--paper-2)", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div style={{ position: "relative" }}>
                <Ph label="before · 004.jpg" style={{ position: "absolute", inset: 0 }} />
                <span style={{ position: "absolute", top: 6, left: 6, fontFamily: "var(--font-mono)", fontSize: 9, background: "var(--paper)", padding: "1px 5px", border: "1px solid var(--line)" }}>before</span>
              </div>
              <div style={{ position: "relative" }}>
                <Ph label="after · step 4" style={{ position: "absolute", inset: 0 }} />
                <span style={{ position: "absolute", top: 6, left: 6, fontFamily: "var(--font-mono)", fontSize: 9, background: "var(--ink)", color: "var(--paper)", padding: "1px 5px" }}>after</span>
              </div>
            </div>
          </div>
          {/* Right: metadata yaml */}
          <div style={{ borderLeft: "1px solid var(--line)", display: "flex", flexDirection: "column" }}>
            <div className="wf-panel-h"><span>metadata.yaml</span><small>v3</small></div>
            <pre style={{ margin: 0, padding: 12, fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-2)", whiteSpace: "pre-wrap", lineHeight: 1.5, flex: 1, overflow: "auto" }}>
{`version: v3
parent: v2
created: 2026-05-11
ops:
  - resize:
      size: [1280, 720]
      interp: bilinear
  - grayscale:
      luma: rec709
  - threshold:
      method: otsu
      invert: true
  - dilate:
      kernel: [3, 3]
      shape: cross
      iter: 2
  - fillPoly:
      min_area: 80
  - morph_close:
      scope: box[3]
      kernel: [5, 5]
      shape: ellipse
      iter: 1
out: ~/datasets/cells/v3/
originals: untouched
`}
            </pre>
          </div>
        </div>
      </main>
    </Win>
  );
}

function Pre_V2() {
  return (
    <Win title="Preprocess pipeline — split preview" path="v3" active="pre">
      <main className="wf-main">
        <Toolbar>
          <Chip solid>v3 · unsaved</Chip>
          <Chip>v2</Chip><Chip>v1</Chip><Chip>v0 (originals)</Chip>
          <div className="wf-spacer" />
          <Btn>diff vs v2</Btn>
          <Btn primary>save version → ~/datasets/cells/v3</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
          {/* Top: before-after side-by-side big */}
          <div style={{ flex: "1 1 0", display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8, padding: 12, borderBottom: "1px solid var(--line)" }}>
            {["original", "step 2 · gray", "step 3 · thresh", "step 4 · dilate"].map((lbl, i) => (
              <div key={lbl} style={{ position: "relative" }}>
                <Ph label="" style={{ position: "absolute", inset: 0 }} />
                <span style={{ position: "absolute", top: 6, left: 6, fontFamily: "var(--font-mono)", fontSize: 9, background: i === 3 ? "var(--ink)" : "var(--paper)", color: i === 3 ? "var(--paper)" : "var(--ink)", padding: "1px 5px", border: "1px solid var(--line)" }}>{lbl}</span>
                <span style={{ position: "absolute", bottom: 6, right: 6, fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--ink-3)" }}>004.jpg</span>
              </div>
            ))}
          </div>
          {/* Bottom: ops as horizontal cards */}
          <div style={{ flex: "0 0 auto", padding: "10px 12px", overflow: "hidden" }}>
            <div className="wf-h2" style={{ marginBottom: 8 }}>pipeline · 6 ops · scope global+local</div>
            <div style={{ display: "flex", gap: 8, overflow: "auto" }}>
              {PRE_OPS.map((o, i) => (
                <div key={i} className="wf-card" style={{ flex: "0 0 200px", flexDirection: "column", borderColor: i === 3 ? "var(--ink)" : "var(--line)" }}>
                  <div className="body" style={{ width: "100%" }}>
                    <div className="h">
                      <span style={{ fontFamily: "var(--font-mono)", color: "var(--ink-3)" }}>0{i + 1}</span>
                      {o.name}
                    </div>
                    <Ph label="" style={{ height: 50, marginBottom: 6 }} />
                    <div className="wf-meta-line" style={{ marginBottom: 4 }}>{o.params}</div>
                    <Chip dot>{o.scope}</Chip>
                  </div>
                </div>
              ))}
              <button className="wf-btn" style={{ flex: "0 0 60px", borderStyle: "dashed", fontSize: 18, height: "auto" }}>+</button>
            </div>
          </div>
        </div>
      </main>
    </Win>
  );
}

function Pre_V3() {
  // Each card embeds its own mini preview
  return (
    <Win title="Preprocess pipeline" path="v3" active="pre">
      <main className="wf-main">
        <Toolbar>
          <Btn>+ op</Btn>
          <Btn ghost>preset · binarize blobs</Btn>
          <Btn ghost>preset · ocr clean</Btn>
          <div className="wf-spacer" />
          <span className="wf-meta-line">applies to 642 images · originals untouched</span>
          <Btn primary>apply →</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", padding: 14, gap: 14, alignContent: "start", overflow: "auto", background: "var(--paper-2)" }}>
          {PRE_OPS.concat([{ name: "Save out", params: "→ ~/datasets/cells/v3", scope: "—" }]).map((o, i) => (
            <div key={i} className="wf-card" style={{ flexDirection: "column", background: "var(--paper)" }}>
              <div style={{ display: "flex", alignItems: "center", padding: "6px 10px", borderBottom: "1px solid var(--line-2)" }}>
                <span className="grip" style={{ background: "transparent", border: 0, borderRight: 0, marginRight: 6, width: 16, padding: 0, display: "inline-flex" }} />
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-3)", marginRight: 6 }}>0{i + 1}</span>
                <span style={{ fontSize: 11, fontWeight: 500 }}>{o.name}</span>
                <span style={{ marginLeft: "auto", display: "flex", gap: 4 }}>
                  <Btn sm ghost>edit</Btn>
                  <Btn sm ghost>×</Btn>
                </span>
              </div>
              <div style={{ display: "flex", height: 90 }}>
                <div style={{ flex: 1, position: "relative", borderRight: "1px solid var(--line-2)" }}>
                  <Ph label="" style={{ position: "absolute", inset: 0 }} />
                  <span style={{ position: "absolute", top: 4, left: 4, fontSize: 8, fontFamily: "var(--font-mono)", background: "var(--paper)", padding: "0 3px" }}>in</span>
                </div>
                <div style={{ flex: 1, position: "relative" }}>
                  <Ph label="" style={{ position: "absolute", inset: 0 }} />
                  <span style={{ position: "absolute", top: 4, left: 4, fontSize: 8, fontFamily: "var(--font-mono)", background: "var(--ink)", color: "var(--paper)", padding: "0 3px" }}>out</span>
                </div>
              </div>
              <div style={{ padding: "6px 10px", borderTop: "1px solid var(--line-2)", display: "flex", alignItems: "center", gap: 6 }}>
                <span className="wf-meta-line" style={{ flex: 1 }}>{o.params}</span>
                <Chip dot>{o.scope}</Chip>
              </div>
            </div>
          ))}
        </div>
      </main>
    </Win>
  );
}

// ============ 5. AUGMENTATION ============

const AUGS = [
  { name: "Horizontal flip", on: true,  v: 0.5,  unit: "p" },
  { name: "Rotate",          on: true,  v: 0.4,  unit: "±15°" },
  { name: "Brightness",      on: true,  v: 0.3,  unit: "±0.3" },
  { name: "Gaussian blur",   on: false, v: 0.2,  unit: "σ 1.2" },
  { name: "Random crop",     on: true,  v: 0.5,  unit: "0.7–1.0" },
  { name: "Hue jitter",      on: false, v: 0.15, unit: "±0.1" },
  { name: "Cutout",          on: true,  v: 0.3,  unit: "1–3 px holes" },
  { name: "Mosaic",          on: false, v: 0.5,  unit: "p 0.5" },
];

function Aug_V1() {
  return (
    <Win title="Data augmentation" path="multiplier 4× → 2 568 imgs" active="aug">
      <main className="wf-main">
        <Toolbar>
          <Btn>load preset</Btn><Btn>save preset</Btn>
          <div className="wf-divider" />
          <span className="wf-meta-line">applied at training-time · seed 42</span>
          <div className="wf-spacer" />
          <Btn>reroll preview</Btn>
          <Btn primary>continue to split →</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "300px 1fr", minHeight: 0 }}>
          {/* augs list */}
          <div style={{ borderRight: "1px solid var(--line)", overflow: "auto" }}>
            {AUGS.map((a, i) => (
              <div key={a.name} style={{ display: "flex", alignItems: "center", padding: "10px 12px", borderBottom: "1px solid var(--line-2)", gap: 10, opacity: a.on ? 1 : 0.5 }}>
                <span style={{ width: 14, height: 14, border: "1px solid var(--ink)", background: a.on ? "var(--ink)" : "var(--paper)", display: "inline-block" }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, fontWeight: 500 }}>{a.name}</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
                    <Slider value={a.v} style={{ flex: 1 }} />
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--ink-3)", width: 60, textAlign: "right" }}>{a.unit}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {/* sample grid */}
          <div style={{ padding: 14, overflow: "auto" }}>
            <div style={{ display: "flex", alignItems: "center", marginBottom: 10 }}>
              <span className="wf-h2">samples from 004.jpg</span>
              <div className="wf-spacer" />
              <Chip>16 variants</Chip>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
              {Array.from({ length: 16 }).map((_, i) => (
                <div key={i} style={{ position: "relative", aspectRatio: "1/1" }}>
                  <Ph label="" style={{ position: "absolute", inset: 0 }} />
                  <Bbox x="22%" y="30%" w="35%" h="38%" />
                  <span style={{ position: "absolute", top: 4, left: 4, fontFamily: "var(--font-mono)", fontSize: 8, background: "var(--paper)", padding: "0 3px", border: "1px solid var(--line)" }}>#{i + 1}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </Win>
  );
}

function Aug_V2() {
  return (
    <Win title="Augmentations — toggle + sample row" path="4× multiplier" active="aug">
      <main className="wf-main">
        <Toolbar>
          <Chip>multiplier 4×</Chip>
          <Chip>seed 42</Chip>
          <Chip>~ 2 568 imgs at train</Chip>
          <div className="wf-spacer" />
          <Btn>reroll</Btn>
          <Btn primary>continue →</Btn>
        </Toolbar>
        <div style={{ flex: 1, overflow: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 8 }}>
          {AUGS.map((a, i) => (
            <div key={a.name} className="wf-card" style={{ alignItems: "center", opacity: a.on ? 1 : .5 }}>
              <div className="grip" />
              <div style={{ padding: "10px 12px", width: 220, borderRight: "1px solid var(--line-2)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ width: 12, height: 12, border: "1px solid var(--ink)", background: a.on ? "var(--ink)" : "transparent" }} />
                  <span style={{ fontSize: 12, fontWeight: 500 }}>{a.name}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 6 }}>
                  <Slider value={a.v} style={{ flex: 1 }} />
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--ink-3)", width: 60, textAlign: "right" }}>{a.unit}</span>
                </div>
              </div>
              <div style={{ flex: 1, display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 4, padding: 6 }}>
                {Array.from({ length: 6 }).map((_, j) => (
                  <div key={j} style={{ position: "relative", aspectRatio: "1/1" }}>
                    <Ph label="" style={{ position: "absolute", inset: 0 }} />
                    {a.on && <Bbox x="22%" y="26%" w="44%" h="40%" />}
                  </div>
                ))}
              </div>
            </div>
          ))}
          <button className="wf-btn" style={{ borderStyle: "dashed", height: 30, alignSelf: "flex-start" }}>+ add augmentation</button>
        </div>
      </main>
    </Win>
  );
}

function Aug_V3() {
  return (
    <Win title="Augmentations" path="3 enabled · 4× total" active="aug">
      <main className="wf-main">
        <Toolbar>
          <Btn ghost>preset · default</Btn>
          <Btn ghost>preset · aggressive</Btn>
          <Btn ghost>preset · none</Btn>
          <div className="wf-spacer" />
          <Btn primary>continue to split →</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, padding: 14, overflow: "auto", alignContent: "start" }}>
          {AUGS.map((a) => (
            <div key={a.name} className="wf-card" style={{ flexDirection: "column", opacity: a.on ? 1 : .55 }}>
              <div style={{ display: "flex", alignItems: "center", padding: "8px 10px", borderBottom: "1px solid var(--line-2)" }}>
                <span style={{ width: 12, height: 12, border: "1px solid var(--ink)", background: a.on ? "var(--ink)" : "transparent", marginRight: 8 }} />
                <span style={{ fontSize: 11, fontWeight: 500 }}>{a.name}</span>
                <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--ink-3)" }}>{a.unit}</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 3, padding: 6 }}>
                {Array.from({ length: 3 }).map((_, j) => (
                  <div key={j} style={{ position: "relative", aspectRatio: "4/3" }}>
                    <Ph label="" style={{ position: "absolute", inset: 0 }} />
                    {a.on && <Bbox x="22%" y="26%" w="44%" h="40%" />}
                  </div>
                ))}
              </div>
              <div style={{ padding: "6px 10px", borderTop: "1px solid var(--line-2)", display: "flex", alignItems: "center", gap: 8 }}>
                <Slider value={a.v} style={{ flex: 1 }} />
                <span className="wf-meta-line">prob</span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </Win>
  );
}

// ============ 6. SPLIT ============

function Split_V1() {
  return (
    <Win title="Train / val / test split" path="642 imgs · seed 42" active="split">
      <main className="wf-main">
        <Toolbar>
          <Chip>strategy · stratified</Chip>
          <Chip>seed 42</Chip>
          <Btn ghost>shuffle</Btn>
          <div className="wf-spacer" />
          <Btn>export splits.txt</Btn>
          <Btn primary>continue →</Btn>
        </Toolbar>
        <div style={{ flex: 1, padding: 22, overflow: "auto" }}>
          <div className="wf-h2" style={{ marginBottom: 8 }}>ratio · drag handles</div>
          <div style={{ position: "relative", height: 48, border: "1px solid var(--line)", marginBottom: 10 }}>
            <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: "70%", background: "var(--ink)", color: "var(--paper)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: 12 }}>train · 70% · 449</div>
            <div style={{ position: "absolute", left: "70%", top: 0, bottom: 0, width: "20%", background: "var(--ink-3)", color: "var(--paper)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: 12 }}>val · 20% · 128</div>
            <div style={{ position: "absolute", left: "90%", top: 0, bottom: 0, width: "10%", background: "var(--ink-4)", color: "var(--ink)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: 12 }}>test · 10% · 65</div>
          </div>
          <div className="wf-h2" style={{ marginTop: 18, marginBottom: 8 }}>class balance across splits</div>
          <div className="wf-panel">
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
              <thead>
                <tr style={{ background: "var(--paper-2)", textAlign: "left" }}>
                  <th style={{ padding: 8, fontWeight: 500 }}>class</th>
                  <th style={{ padding: 8, fontWeight: 500, width: 80, fontFamily: "var(--font-mono)" }}>train</th>
                  <th style={{ padding: 8, fontWeight: 500, width: 80, fontFamily: "var(--font-mono)" }}>val</th>
                  <th style={{ padding: 8, fontWeight: 500, width: 80, fontFamily: "var(--font-mono)" }}>test</th>
                  <th style={{ padding: 8, fontWeight: 500 }}>distribution</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["cell",     338, 96, 48, [70, 20, 10]],
                  ["nucleus",  149, 43, 21, [70, 20, 10]],
                  ["debris",    45, 13,  6, [70, 20, 10]],
                  ["artifact",   6,  2,  1, [67, 22, 11]],
                ].map((r, i) => (
                  <tr key={i} style={{ borderTop: "1px solid var(--line-2)" }}>
                    <td style={{ padding: 8 }}>{r[0]}</td>
                    <td style={{ padding: 8, fontFamily: "var(--font-mono)" }}>{r[1]}</td>
                    <td style={{ padding: 8, fontFamily: "var(--font-mono)" }}>{r[2]}</td>
                    <td style={{ padding: 8, fontFamily: "var(--font-mono)" }}>{r[3]}</td>
                    <td style={{ padding: 8 }}>
                      <div style={{ display: "flex", height: 8, border: "1px solid var(--line)" }}>
                        <span style={{ width: `${r[4][0]}%`, background: "var(--ink)" }} />
                        <span style={{ width: `${r[4][1]}%`, background: "var(--ink-3)" }} />
                        <span style={{ width: `${r[4][2]}%`, background: "var(--ink-4)" }} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="wf-meta-line" style={{ marginTop: 12 }}>writes ~/datasets/cells/v3/splits/{`{train,val,test}`}.txt — paths only · originals untouched</div>
        </div>
      </main>
    </Win>
  );
}

function Split_V2() {
  const cols = [
    { name: "train", pct: 70, n: 449, color: "var(--ink)" },
    { name: "val",   pct: 20, n: 128, color: "var(--ink-3)" },
    { name: "test",  pct: 10, n:  65, color: "var(--ink-4)" },
  ];
  return (
    <Win title="Split — three buckets" path="seed 42" active="split">
      <main className="wf-main">
        <Toolbar>
          <Btn ghost>random</Btn>
          <Btn ghost>stratified by class</Btn>
          <Btn ghost>folder-aware</Btn>
          <div className="wf-spacer" />
          <Btn>reshuffle</Btn>
          <Btn primary>save splits.txt</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, padding: 14, minHeight: 0 }}>
          {cols.map((c) => (
            <div key={c.name} className="wf-panel" style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
              <div className="wf-panel-h">
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ width: 12, height: 12, background: c.color }} />{c.name}
                </span>
                <small>{c.pct}% · {c.n} imgs</small>
              </div>
              <div style={{ padding: 8, borderBottom: "1px solid var(--line-2)" }}>
                <Slider value={c.pct / 100} />
              </div>
              <div style={{ padding: "8px 10px", display: "flex", flexDirection: "column", gap: 5, fontSize: 11 }}>
                {[
                  ["cell", Math.round(482 * c.pct / 100)],
                  ["nucleus", Math.round(213 * c.pct / 100)],
                  ["debris", Math.round(64 * c.pct / 100)],
                  ["artifact", Math.round(9 * c.pct / 100)],
                ].map(([k, v]) => (
                  <div key={k} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>{k}</span><span className="mono">{v}</span>
                  </div>
                ))}
              </div>
              <div style={{ flex: 1, padding: 8, display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gridAutoRows: "32px", gap: 3, overflow: "hidden", borderTop: "1px solid var(--line-2)" }}>
                {Array.from({ length: 30 }).map((_, i) => (
                  <Ph key={i} label="" />
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>
    </Win>
  );
}

function Split_V3() {
  return (
    <Win title="Split — distribution check" path="v3 · 642 imgs" active="split">
      <main className="wf-main">
        <Toolbar>
          <Btn ghost>strategy: stratified</Btn>
          <Btn ghost>seed: 42</Btn>
          <div className="wf-spacer" />
          <Btn primary>save and continue →</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: 14, padding: 14, minHeight: 0 }}>
          <Panel title="ratios" meta="drag to adjust">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 10 }}>
              {/* Donut placeholder */}
              <svg viewBox="0 0 36 36" style={{ width: 180, height: 180 }}>
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--line-2)" strokeWidth="3" />
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--ink)" strokeWidth="3" strokeDasharray="70 30" transform="rotate(-90 18 18)" />
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--ink-3)" strokeWidth="3" strokeDasharray="20 80" strokeDashoffset="-70" transform="rotate(-90 18 18)" />
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--ink-4)" strokeWidth="3" strokeDasharray="10 90" strokeDashoffset="-90" transform="rotate(-90 18 18)" />
                <text x="18" y="20" textAnchor="middle" fontSize="4" fontFamily="var(--font-mono)" fill="var(--ink)">642 imgs</text>
              </svg>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 6 }}>
              {[
                ["train", 70, 449, "var(--ink)"],
                ["val",   20, 128, "var(--ink-3)"],
                ["test",  10,  65, "var(--ink-4)"],
              ].map(([k, p, n, c]) => (
                <div key={k} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 11 }}>
                  <span style={{ width: 12, height: 12, background: c }} />
                  <span style={{ flex: 1 }}>{k}</span>
                  <span className="mono">{p}%</span>
                  <span className="mono" style={{ width: 50, textAlign: "right" }}>{n}</span>
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="class balance check" meta="warns if any class < 1% in val/test">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
              {["cell", "nucleus", "debris", "artifact"].map((c, i) => (
                <div key={c} style={{ border: "1px solid var(--line-2)", padding: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 500, marginBottom: 6 }}>{c}</div>
                  <div style={{ height: 60, display: "flex", alignItems: "flex-end", gap: 4, marginBottom: 4 }}>
                    <i style={{ flex: 1, background: "var(--ink)",   height: `${[100, 95, 80, 30][i]}%`, display: "block" }} />
                    <i style={{ flex: 1, background: "var(--ink-3)", height: `${[28, 24, 18, 12][i]}%`, display: "block" }} />
                    <i style={{ flex: 1, background: "var(--ink-4)", height: `${[14, 12, 9, 5][i]}%`, display: "block" }} />
                  </div>
                  <div className="wf-meta-line">{["ok", "ok", "ok", "⚠ thin"][i]}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 14, fontSize: 11, color: "var(--ink-2)" }}>
              <Chip>⚠ artifact has only 1 example in test</Chip>
            </div>
          </Panel>
        </div>
      </main>
    </Win>
  );
}

Object.assign(window, {
  Pre_V1, Pre_V2, Pre_V3,
  Aug_V1, Aug_V2, Aug_V3,
  Split_V1, Split_V2, Split_V3,
});
