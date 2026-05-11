/* Screens 7-9: Training loop, Model registry, Integrations */

// ============ 7. TRAINING ============

function Train_V1() {
  return (
    <Win title="Train · rf-detr · run 14" path="epoch 27 / 100" active="train">
      <main className="wf-main">
        <Toolbar>
          <Chip solid dot>running</Chip>
          <Chip>rf-detr · base</Chip>
          <Chip>batch 16</Chip>
          <Chip>lr 1e-4</Chip>
          <Chip>v3 · 642 imgs · 4×</Chip>
          <div className="wf-spacer" />
          <Btn>pause</Btn>
          <Btn>stop</Btn>
          <Btn primary>save checkpoint</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "260px 1fr", minHeight: 0 }}>
          {/* config */}
          <div style={{ borderRight: "1px solid var(--line)", overflow: "auto" }}>
            <div className="wf-panel-h"><span>Config</span><small>locked</small></div>
            <div style={{ padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
              <Row k="model"     v="rf-detr/base" />
              <Row k="weights"   v="coco-pretrained" />
              <Row k="classes"   v="4" />
              <Row k="epochs"    v="100" />
              <Row k="batch"     v="16" />
              <Row k="lr"        v="1e-4" />
              <Row k="optim"     v="adamw" />
              <Row k="scheduler" v="cosine" />
              <Row k="warmup"    v="500 steps" />
              <Row k="img size"  v="640" />
              <Row k="device"    v="cuda:0" />
              <Row k="seed"      v="42" />
            </div>
            <div className="wf-panel-h" style={{ borderTop: "1px solid var(--line)" }}><span>Progress</span></div>
            <div style={{ padding: 12 }}>
              <div className="wf-meta-line" style={{ marginBottom: 6 }}>epoch 27 / 100 · 27%</div>
              <div style={{ height: 6, background: "var(--line-2)" }}><div style={{ width: "27%", height: "100%", background: "var(--ink)" }} /></div>
              <div className="wf-meta-line" style={{ marginTop: 8 }}>eta · 1h 38m · 4.2 it/s</div>
            </div>
            <div className="wf-panel-h" style={{ borderTop: "1px solid var(--line)" }}><span>Best so far</span></div>
            <div style={{ padding: 12, fontSize: 11, color: "var(--ink-2)" }}>
              <Row k="mAP@50" v="0.642" />
              <Row k="mAP@50-95" v="0.418" />
              <Row k="epoch" v="24" />
            </div>
          </div>
          {/* charts + log */}
          <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
            <div style={{ flex: "1 1 0", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, padding: 10, borderBottom: "1px solid var(--line)" }}>
              <Panel title="loss" meta="train ─── val">
                <LineChart style={{ height: 160 }} points={[[0, 80], [10, 60], [22, 52], [38, 40], [56, 33], [72, 28], [88, 24], [100, 22]]} />
              </Panel>
              <Panel title="mAP" meta="@50 / @50-95">
                <LineChart style={{ height: 160 }} points={[[0, 90], [10, 70], [22, 56], [38, 46], [56, 40], [72, 36], [88, 34], [100, 33]]} />
              </Panel>
              <Panel title="precision">
                <LineChart style={{ height: 120 }} points={[[0, 60], [20, 50], [40, 42], [60, 36], [80, 32], [100, 30]]} />
              </Panel>
              <Panel title="recall">
                <LineChart style={{ height: 120 }} points={[[0, 70], [20, 56], [40, 50], [60, 44], [80, 40], [100, 36]]} />
              </Panel>
            </div>
            {/* log */}
            <div style={{ flex: "0 0 160px", borderTop: "1px solid var(--line)" }}>
              <div className="wf-panel-h"><span>log</span><small>tail -f train.log</small></div>
              <pre style={{ margin: 0, padding: "8px 12px", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-2)", lineHeight: 1.55, height: 110, overflow: "auto", background: "var(--paper-2)" }}>
{`[27/100] 4.2 it/s  loss 0.241  cls 0.082  box 0.118  giou 0.041
[27/100] eval val   mAP@50 0.639  mAP@50-95 0.415  P 0.71  R 0.66
[27/100] saving checkpoint → runs/14/last.pt
[27/100] lr 9.2e-5 (cosine)
[28/100] training… 1/40 batches`}
              </pre>
            </div>
          </div>
        </div>
      </main>
    </Win>
  );
}

function Train_V2() {
  return (
    <Win title="Train · run 14" path="epoch 27/100" active="train">
      <main className="wf-main">
        <Toolbar>
          <Chip solid dot>running · 27%</Chip>
          <span className="wf-meta-line">eta 1h 38m · 4.2 it/s · cuda:0</span>
          <div className="wf-spacer" />
          <Btn>pause</Btn><Btn>stop</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", borderBottom: "1px solid var(--line)" }}>
            {[
              ["loss",      "0.241",  "↓ 0.014"],
              ["mAP@50",    "0.639",  "↑ 0.012"],
              ["precision", "0.71",   "↑ 0.02"],
              ["recall",    "0.66",   "↓ 0.01"],
            ].map(([k, v, d]) => (
              <div key={k} style={{ padding: 14, borderRight: "1px solid var(--line-2)" }}>
                <div style={{ fontSize: 10, color: "var(--ink-3)", textTransform: "uppercase", letterSpacing: ".08em", fontFamily: "var(--font-mono)" }}>{k}</div>
                <div style={{ fontSize: 26, fontWeight: 600, fontFamily: "var(--font-mono)" }}>{v}</div>
                <div className="wf-meta-line">{d} vs last</div>
              </div>
            ))}
          </div>
          <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0, minHeight: 0 }}>
            <div style={{ borderRight: "1px solid var(--line)", padding: 12, display: "flex", flexDirection: "column" }}>
              <div className="wf-h2" style={{ marginBottom: 6 }}>loss · train vs val</div>
              <LineChart style={{ flex: 1 }} points={[[0, 80], [10, 60], [22, 52], [38, 40], [56, 33], [72, 28], [88, 24], [100, 22]]} />
            </div>
            <div style={{ padding: 12, display: "flex", flexDirection: "column" }}>
              <div className="wf-h2" style={{ marginBottom: 6 }}>mAP@50 / @50-95</div>
              <LineChart style={{ flex: 1 }} points={[[0, 95], [12, 80], [25, 65], [40, 52], [56, 44], [72, 38], [88, 34], [100, 32]]} />
            </div>
          </div>
          <div style={{ flex: "0 0 200px", borderTop: "1px solid var(--line)", background: "#111", color: "#cfc", padding: "10px 14px", fontFamily: "var(--font-mono)", fontSize: 10, lineHeight: 1.6, overflow: "auto" }}>
{`$ python train.py --cfg runs/14/cfg.yaml --resume runs/14/last.pt
[25/100] loss 0.268  mAP@50 0.621  P 0.69  R 0.65  4.1 it/s  eta 1h 49m
[26/100] loss 0.255  mAP@50 0.628  P 0.70  R 0.66  4.2 it/s  eta 1h 44m
[27/100] loss 0.241  mAP@50 0.639  P 0.71  R 0.66  4.2 it/s  eta 1h 38m
[27/100] ✓ saved runs/14/best.pt (mAP@50 0.639)
[28/100] training…  ▮▮▮▱▱▱▱▱  1/40`}
          </div>
        </div>
      </main>
    </Win>
  );
}

function Train_V3() {
  return (
    <Win title="Train · run 14" path="rf-detr base" active="train">
      <main className="wf-main">
        <Toolbar>
          <Btn>new run</Btn>
          <Btn>duplicate config</Btn>
          <div className="wf-spacer" />
          <Btn>pause</Btn><Btn primary>save & exit</Btn>
        </Toolbar>
        <div style={{ flex: 1, overflow: "auto" }}>
          {/* hero: progress */}
          <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--line-2)" }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
              <span className="wf-h1">run 14 · rf-detr</span>
              <Chip solid dot>running</Chip>
              <span className="wf-meta-line">started 2026-05-11 14:08 · cuda:0</span>
              <div className="wf-spacer" />
              <span className="wf-h1" style={{ fontFamily: "var(--font-mono)" }}>27 / 100</span>
            </div>
            <div style={{ height: 8, background: "var(--line-2)", marginTop: 10 }}>
              <div style={{ width: "27%", height: "100%", background: "var(--ink)" }} />
            </div>
            <div className="wf-meta-line" style={{ marginTop: 6 }}>eta 1h 38m · 4.2 it/s · loss 0.241 · mAP@50 0.639</div>
          </div>
          {/* config grid */}
          <div style={{ padding: "14px 22px", borderBottom: "1px solid var(--line-2)" }}>
            <div className="wf-h2" style={{ marginBottom: 10 }}>config</div>
            <div className="wf-grid-4">
              {[
                ["model", "rf-detr/base"], ["weights", "coco"], ["classes", "4"], ["epochs", "100"],
                ["batch", "16"], ["lr", "1e-4"], ["optim", "adamw"], ["scheduler", "cosine"],
                ["img size", "640"], ["seed", "42"], ["device", "cuda:0"], ["data", "v3 · 4× aug"],
              ].map(([k, v]) => (
                <div key={k} style={{ border: "1px solid var(--line-2)", padding: "6px 10px" }}>
                  <div style={{ fontSize: 9, color: "var(--ink-3)", textTransform: "uppercase", fontFamily: "var(--font-mono)", letterSpacing: ".08em" }}>{k}</div>
                  <div style={{ fontSize: 12, fontFamily: "var(--font-mono)" }}>{v}</div>
                </div>
              ))}
            </div>
          </div>
          {/* charts */}
          <div style={{ padding: "14px 22px", borderBottom: "1px solid var(--line-2)" }}>
            <div className="wf-h2" style={{ marginBottom: 10 }}>metrics</div>
            <div className="wf-grid-3">
              <Panel title="loss"><LineChart style={{ height: 120 }} points={[[0,80],[20,55],[40,38],[60,30],[80,24],[100,22]]} /></Panel>
              <Panel title="mAP@50"><LineChart style={{ height: 120 }} points={[[0,90],[20,68],[40,52],[60,42],[80,36],[100,34]]} /></Panel>
              <Panel title="lr"><LineChart style={{ height: 120 }} points={[[0,10],[15,15],[40,40],[70,60],[100,90]]} /></Panel>
            </div>
          </div>
          {/* log */}
          <div style={{ padding: "14px 22px" }}>
            <div className="wf-h2" style={{ marginBottom: 10 }}>tail · runs/14/train.log</div>
            <pre style={{ margin: 0, padding: 12, background: "var(--paper-2)", border: "1px solid var(--line)", fontFamily: "var(--font-mono)", fontSize: 10, lineHeight: 1.55, color: "var(--ink-2)" }}>
{`[25/100] loss 0.268  mAP@50 0.621  4.1 it/s
[26/100] loss 0.255  mAP@50 0.628  4.2 it/s
[27/100] loss 0.241  mAP@50 0.639  4.2 it/s   ✓ best.pt`}
            </pre>
          </div>
        </div>
      </main>
    </Win>
  );
}

// ============ 8. MODEL REGISTRY / EVAL ============

const RUNS = [
  ["run 14", "rf-detr/base",  "running", "v3 · 4×",  "27/100", "0.639", "—"],
  ["run 13", "rf-detr/base",  "done",    "v3 · 2×",  "100/100","0.621", "tagged"],
  ["run 12", "yolov8/n",      "done",    "v2 · 4×",  "100/100","0.598", ""],
  ["run 11", "yolov8/s",      "done",    "v2 · 1×",  "80/100", "0.604", "tagged"],
  ["run 10", "rf-detr/base",  "failed",  "v1 · 1×",  "12/100", "—",     ""],
  ["run 09", "yolov8/n",      "done",    "v0 · 1×",  "100/100","0.518", ""],
  ["run 08", "yolov8/n",      "done",    "v0 · 1×",  "100/100","0.502", ""],
];

function Models_V1() {
  return (
    <Win title="Models · runs" path="7 runs · 2 tagged" active="models">
      <main className="wf-main">
        <Toolbar>
          <Btn ghost>all 7</Btn>
          <Btn ghost>tagged 2</Btn>
          <Btn ghost>failed 1</Btn>
          <div className="wf-divider" />
          <Btn ghost>sort: mAP ↓</Btn>
          <div className="wf-spacer" />
          <Btn>compare ×2</Btn>
          <Btn primary>new run</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.4fr 1fr", minHeight: 0 }}>
          <div style={{ borderRight: "1px solid var(--line)", overflow: "auto" }}>
            <div className="wf-list-row" style={{ background: "var(--paper-2)", fontWeight: 500, color: "var(--ink-2)" }}>
              <span style={{ width: 60 }}>run</span>
              <span style={{ width: 130 }}>model</span>
              <span style={{ width: 70 }}>state</span>
              <span style={{ width: 90 }}>data</span>
              <span style={{ width: 70 }}>epoch</span>
              <span style={{ width: 60 }}>mAP@50</span>
              <span style={{ flex: 1 }}>tag</span>
            </div>
            {RUNS.map((r, i) => (
              <div key={r[0]} className={`wf-list-row ${i === 0 ? "sel" : ""}`}>
                <span className="mono" style={{ width: 60 }}>{r[0]}</span>
                <span className="mono" style={{ width: 130 }}>{r[1]}</span>
                <span style={{ width: 70 }}>
                  <Chip dot solid={r[2] === "running"}>{r[2]}</Chip>
                </span>
                <span className="mono" style={{ width: 90, color: "var(--ink-3)" }}>{r[3]}</span>
                <span className="mono" style={{ width: 70 }}>{r[4]}</span>
                <span className="mono" style={{ width: 60, fontWeight: 600 }}>{r[5]}</span>
                <span style={{ flex: 1 }}>{r[6] && <Chip>{r[6]}</Chip>}</span>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", flexDirection: "column", overflow: "auto" }}>
            <div style={{ padding: "12px 14px", borderBottom: "1px solid var(--line)" }}>
              <div className="wf-h1">run 14 · rf-detr/base</div>
              <div className="wf-meta-line" style={{ marginTop: 4 }}>started 2026-05-11 · v3 dataset · running</div>
              <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
                <Btn sm>show in directory</Btn>
                <Btn sm>export weights</Btn>
                <Btn sm>promote</Btn>
                <Btn sm>delete</Btn>
              </div>
            </div>
            <div style={{ padding: 14, borderBottom: "1px solid var(--line-2)" }}>
              <div className="wf-h2" style={{ marginBottom: 8 }}>metrics</div>
              <div className="wf-grid-3">
                {[["mAP@50","0.639"],["mAP@50-95","0.418"],["precision","0.71"],["recall","0.66"],["f1","0.68"],["loss","0.241"]].map(([k, v]) => (
                  <div key={k} style={{ border: "1px solid var(--line-2)", padding: 8 }}>
                    <div style={{ fontSize: 9, color: "var(--ink-3)", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>{k}</div>
                    <div style={{ fontSize: 16, fontWeight: 600, fontFamily: "var(--font-mono)" }}>{v}</div>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ padding: 14 }}>
              <div className="wf-h2" style={{ marginBottom: 8 }}>per-class</div>
              <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "var(--paper-2)", textAlign: "left" }}>
                    <th style={{ padding: 6, fontWeight: 500 }}>class</th>
                    <th style={{ padding: 6, fontWeight: 500, fontFamily: "var(--font-mono)" }}>P</th>
                    <th style={{ padding: 6, fontWeight: 500, fontFamily: "var(--font-mono)" }}>R</th>
                    <th style={{ padding: 6, fontWeight: 500, fontFamily: "var(--font-mono)" }}>mAP@50</th>
                    <th style={{ padding: 6, fontWeight: 500, fontFamily: "var(--font-mono)" }}>support</th>
                  </tr>
                </thead>
                <tbody>
                  {[["cell",.74,.71,.72,338],["nucleus",.69,.66,.66,149],["debris",.62,.58,.55,45],["artifact",.40,.33,.30,6]].map((r, i) => (
                    <tr key={i} style={{ borderTop: "1px solid var(--line-2)" }}>
                      <td style={{ padding: 6 }}>{r[0]}</td>
                      <td style={{ padding: 6, fontFamily: "var(--font-mono)" }}>{r[1].toFixed(2)}</td>
                      <td style={{ padding: 6, fontFamily: "var(--font-mono)" }}>{r[2].toFixed(2)}</td>
                      <td style={{ padding: 6, fontFamily: "var(--font-mono)" }}>{r[3].toFixed(2)}</td>
                      <td style={{ padding: 6, fontFamily: "var(--font-mono)" }}>{r[4]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </Win>
  );
}

function Models_V2() {
  return (
    <Win title="Models — cards" path="7 runs" active="models">
      <main className="wf-main">
        <Toolbar>
          <Btn ghost>view: cards</Btn>
          <Btn ghost>view: table</Btn>
          <div className="wf-spacer" />
          <Input placeholder="filter…" style={{ width: 200 }} />
          <Btn primary>new run</Btn>
        </Toolbar>
        <div style={{ flex: 1, padding: 14, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, alignContent: "start", overflow: "auto" }}>
          {RUNS.map((r, i) => (
            <div key={r[0]} className="wf-card" style={{ flexDirection: "column", background: "var(--paper)" }}>
              <div style={{ display: "flex", alignItems: "center", padding: "8px 10px", borderBottom: "1px solid var(--line-2)" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 600 }}>{r[0]}</span>
                <span style={{ marginLeft: 8, fontSize: 11, color: "var(--ink-2)" }}>{r[1]}</span>
                <span style={{ marginLeft: "auto" }}><Chip dot solid={r[2] === "running"}>{r[2]}</Chip></span>
              </div>
              <div style={{ padding: 10, display: "flex", gap: 14, alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: 9, color: "var(--ink-3)", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>mAP@50</div>
                  <div style={{ fontSize: 26, fontWeight: 700, fontFamily: "var(--font-mono)" }}>{r[5]}</div>
                </div>
                <div style={{ flex: 1, height: 60 }}>
                  <LineChart style={{ height: "100%" }} points={[[0,80],[20,60+i*2],[40,45+i*2],[60,35+i],[80,30+i],[100,28+i]]} />
                </div>
              </div>
              <div style={{ padding: "6px 10px", borderTop: "1px solid var(--line-2)", display: "flex", alignItems: "center", gap: 6 }}>
                <span className="wf-meta-line">{r[3]} · {r[4]}</span>
                <div className="wf-spacer" />
                {r[6] && <Chip>{r[6]}</Chip>}
                <Btn sm ghost>open</Btn>
              </div>
            </div>
          ))}
        </div>
      </main>
    </Win>
  );
}

function Models_V3() {
  return (
    <Win title="Models · run 13 · evaluation" path="held-out test · 65 imgs" active="models">
      <main className="wf-main">
        <Toolbar>
          <Btn ghost>◀ run 12</Btn>
          <Btn>run 13</Btn>
          <Btn ghost>run 14 ▶</Btn>
          <div className="wf-divider" />
          <Chip solid dot>tagged · baseline</Chip>
          <div className="wf-spacer" />
          <Btn>export weights</Btn>
          <Btn>show in directory</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 0, minHeight: 0 }}>
          {/* Confusion matrix */}
          <div style={{ padding: 14, borderRight: "1px solid var(--line)", display: "flex", flexDirection: "column" }}>
            <div className="wf-h2" style={{ marginBottom: 10 }}>confusion matrix · 4 classes</div>
            <div style={{ display: "grid", gridTemplateColumns: "60px 1fr", gap: 6, flex: 1 }}>
              <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-around", padding: "6px 0", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-3)" }}>
                <span>cell</span><span>nucl.</span><span>debr.</span><span>artif.</span><span>bg</span>
              </div>
              <Matrix size={5} style={{ height: "100%" }} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "60px 1fr", gap: 6 }}>
              <span />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 1, padding: "4px 0", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-3)", textAlign: "center" }}>
                <span>cell</span><span>nucl.</span><span>debr.</span><span>artif.</span><span>bg</span>
              </div>
            </div>
            <div className="wf-meta-line" style={{ marginTop: 8 }}>rows = truth · cols = pred · values % of row</div>
          </div>
          {/* Per-class metrics + PR curve */}
          <div style={{ display: "flex", flexDirection: "column", overflow: "auto" }}>
            <div style={{ padding: 14, borderBottom: "1px solid var(--line-2)" }}>
              <div className="wf-h2" style={{ marginBottom: 10 }}>per-class metrics</div>
              <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "var(--paper-2)", textAlign: "left" }}>
                    <th style={{ padding: 6, fontWeight: 500 }}>class</th>
                    <th style={{ padding: 6, fontFamily: "var(--font-mono)" }}>P</th>
                    <th style={{ padding: 6, fontFamily: "var(--font-mono)" }}>R</th>
                    <th style={{ padding: 6, fontFamily: "var(--font-mono)" }}>F1</th>
                    <th style={{ padding: 6, fontFamily: "var(--font-mono)" }}>mAP@50</th>
                    <th style={{ padding: 6, fontFamily: "var(--font-mono)" }}>support</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["cell",     .74,.71,.72,.72,338],
                    ["nucleus",  .69,.66,.67,.66,149],
                    ["debris",   .62,.58,.60,.55, 45],
                    ["artifact", .40,.33,.36,.30,  6],
                  ].map((r, i) => (
                    <tr key={i} style={{ borderTop: "1px solid var(--line-2)" }}>
                      <td style={{ padding: 6 }}>{r[0]}</td>
                      <td style={{ padding: 6, fontFamily: "var(--font-mono)" }}>{r[1].toFixed(2)}</td>
                      <td style={{ padding: 6, fontFamily: "var(--font-mono)" }}>{r[2].toFixed(2)}</td>
                      <td style={{ padding: 6, fontFamily: "var(--font-mono)" }}>{r[3].toFixed(2)}</td>
                      <td style={{ padding: 6, fontFamily: "var(--font-mono)", fontWeight: 600 }}>{r[4].toFixed(2)}</td>
                      <td style={{ padding: 6, fontFamily: "var(--font-mono)", color: "var(--ink-3)" }}>{r[5]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ padding: 14, borderBottom: "1px solid var(--line-2)" }}>
              <div className="wf-h2" style={{ marginBottom: 10 }}>precision-recall · per class</div>
              <LineChart style={{ height: 140 }} points={[[0, 5], [20, 12], [40, 22], [60, 38], [78, 58], [90, 78], [100, 95]]} />
            </div>
            <div style={{ padding: 14 }}>
              <div className="wf-h2" style={{ marginBottom: 8 }}>worst predictions · click to open</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 6 }}>
                {Array.from({ length: 12 }).map((_, i) => (
                  <div key={i} style={{ position: "relative", aspectRatio: "4/3" }}>
                    <Ph label="" style={{ position: "absolute", inset: 0 }} />
                    <Bbox x="20%" y="22%" w="50%" h="50%" />
                    <Bbox x="32%" y="34%" w="46%" h="42%" dash />
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

// ============ 9. INTEGRATIONS (VLM / OCR / Detector) ============

const PROVIDERS = [
  { kind: "VLM", name: "qwen2-vl-7b",    state: "ready",  loc: "ollama · localhost" },
  { kind: "VLM", name: "llava-1.6",      state: "ready",  loc: "ollama · localhost" },
  { kind: "OCR", name: "tesseract 5.4",  state: "ready",  loc: "system path" },
  { kind: "OCR", name: "paddleocr",      state: "down",   loc: "python · venv" },
  { kind: "DET", name: "grounding-dino", state: "ready",  loc: "weights local" },
  { kind: "DET", name: "yolo-world",     state: "needs dl", loc: "weights remote" },
];

function Integ_V1() {
  return (
    <Win title="Integrations" path="VLM · OCR · Detectors" active="integ">
      <main className="wf-main">
        <div className="wf-tabs">
          <span className="tab active">All</span>
          <span className="tab">VLM</span>
          <span className="tab">OCR</span>
          <span className="tab">Detectors</span>
          <span className="tab">Loaders</span>
        </div>
        <Toolbar>
          <span className="wf-meta-line">used for: assisted labeling · OCR pre-pass · prompt-based seed boxes</span>
          <div className="wf-spacer" />
          <Btn>+ register</Btn>
        </Toolbar>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1.4fr", minHeight: 0 }}>
          <div style={{ borderRight: "1px solid var(--line)", overflow: "auto" }}>
            {PROVIDERS.map((p, i) => (
              <div key={p.name} className={`wf-list-row ${i === 0 ? "sel" : ""}`} style={{ padding: "10px 12px" }}>
                <Chip>{p.kind}</Chip>
                <div style={{ flex: 1, marginLeft: 4 }}>
                  <div style={{ fontSize: 12, fontWeight: 500 }}>{p.name}</div>
                  <div className="wf-meta-line">{p.loc}</div>
                </div>
                <Chip dot solid={p.state === "ready"}>{p.state}</Chip>
              </div>
            ))}
            <button className="wf-btn" style={{ borderStyle: "dashed", height: 32, width: "calc(100% - 20px)", margin: 10 }}>+ register provider</button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", overflow: "auto" }}>
            <div style={{ padding: 14, borderBottom: "1px solid var(--line-2)" }}>
              <div className="wf-h1">qwen2-vl-7b</div>
              <div className="wf-meta-line" style={{ marginTop: 4 }}>VLM · ollama@localhost:11434</div>
              <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
                <Chip dot solid>ready</Chip>
                <Chip>tokens 32k</Chip>
                <Chip>used 1 240×</Chip>
              </div>
            </div>
            <div style={{ padding: 14, borderBottom: "1px solid var(--line-2)" }}>
              <div className="wf-h2" style={{ marginBottom: 10 }}>config</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <Row k="endpoint" v="http://localhost:11434" />
                <Row k="model"    v="qwen2-vl:7b" />
                <Row k="timeout"  v="30s" />
                <Row k="temp"     v="0.2" />
                <Row k="role"     v="assisted-labeling, seed-boxes" />
              </div>
            </div>
            <div style={{ padding: 14, flex: 1 }}>
              <div className="wf-h2" style={{ marginBottom: 10 }}>playground</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <Ph label="drop image · or use 004.jpg" style={{ height: 180 }} />
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <Input placeholder="prompt: list bounding boxes of cells" />
                  <div style={{ flex: 1, border: "1px solid var(--line)", padding: 8, fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-2)", background: "var(--paper-2)", minHeight: 130 }}>
{`[
  {"class":"cell",   "bbox":[40,60,120,84]},
  {"class":"cell",   "bbox":[180,130,90,70]},
  {"class":"debris", "bbox":[260,40,64,50]}
]`}
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <Btn sm>run</Btn>
                    <Btn sm primary>import as seed boxes →</Btn>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </Win>
  );
}

function Integ_V2() {
  return (
    <Win title="Integrations — providers" path="6 registered" active="integ">
      <main className="wf-main">
        <Toolbar>
          <Btn ghost>VLM 2</Btn><Btn ghost>OCR 2</Btn><Btn ghost>DET 2</Btn>
          <div className="wf-spacer" />
          <Btn primary>+ register provider</Btn>
        </Toolbar>
        <div style={{ flex: 1, padding: 14, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, alignContent: "start", overflow: "auto" }}>
          {PROVIDERS.map((p) => (
            <div key={p.name} className="wf-card" style={{ flexDirection: "column" }}>
              <div style={{ display: "flex", alignItems: "center", padding: "8px 10px", borderBottom: "1px solid var(--line-2)" }}>
                <Chip>{p.kind}</Chip>
                <span style={{ marginLeft: 8, fontSize: 12, fontWeight: 500 }}>{p.name}</span>
                <span style={{ marginLeft: "auto" }}><Chip dot solid={p.state === "ready"}>{p.state}</Chip></span>
              </div>
              <div style={{ padding: 10, fontSize: 11, color: "var(--ink-2)" }}>
                <Row k="loc"  v={p.loc} />
                <Row k="role" v={p.kind === "OCR" ? "ocr-pass" : p.kind === "DET" ? "seed-boxes" : "label-assist"} />
                <Row k="used" v={`${Math.round(Math.random() * 1500)}× this month`} />
              </div>
              <div style={{ padding: 8, borderTop: "1px solid var(--line-2)", display: "flex", gap: 4 }}>
                <Btn sm>test</Btn>
                <Btn sm>config</Btn>
                <Btn sm ghost>remove</Btn>
                <div className="wf-spacer" />
                <Btn sm primary>use</Btn>
              </div>
            </div>
          ))}
          <div className="wf-card" style={{ flexDirection: "column", borderStyle: "dashed", alignItems: "center", justifyContent: "center", padding: 24, color: "var(--ink-3)" }}>
            <div style={{ fontSize: 28 }}>+</div>
            <div>register a new provider</div>
            <div className="wf-meta-line" style={{ marginTop: 4 }}>http endpoint · python entry · weights file</div>
          </div>
        </div>
      </main>
    </Win>
  );
}

function Integ_V3() {
  return (
    <Win title="Integrations — minimal" path="6 providers" active="integ">
      <main className="wf-main">
        <div style={{ padding: "20px 22px", borderBottom: "1px solid var(--line-2)" }}>
          <div className="wf-h1">External models</div>
          <div className="wf-meta-line" style={{ marginTop: 4 }}>used as helpers throughout the app: seed boxes from a detector, OCR pre-pass, VLM-assisted labeling. all local; no telemetry.</div>
        </div>
        <div style={{ flex: 1, padding: "0 22px", overflow: "auto" }}>
          {["VLM", "OCR", "Detectors"].map((cat) => (
            <div key={cat} style={{ padding: "18px 0", borderBottom: "1px solid var(--line-2)" }}>
              <div style={{ display: "flex", alignItems: "center", marginBottom: 10 }}>
                <div className="wf-h2">{cat}</div>
                <div className="wf-spacer" />
                <Btn sm>+ add</Btn>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                {PROVIDERS.filter(p => (cat === "VLM" ? p.kind === "VLM" : cat === "OCR" ? p.kind === "OCR" : p.kind === "DET")).map((p) => (
                  <div key={p.name} style={{ display: "flex", alignItems: "center", padding: "10px 0", borderTop: "1px solid var(--line-2)" }}>
                    <span style={{ fontSize: 13, fontFamily: "var(--font-mono)", width: 200 }}>{p.name}</span>
                    <span className="wf-meta-line" style={{ width: 220 }}>{p.loc}</span>
                    <Chip dot solid={p.state === "ready"}>{p.state}</Chip>
                    <div className="wf-spacer" />
                    <Btn sm ghost>test</Btn>
                    <Btn sm ghost>edit</Btn>
                    <Btn sm ghost>remove</Btn>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>
    </Win>
  );
}

Object.assign(window, {
  Train_V1, Train_V2, Train_V3,
  Models_V1, Models_V2, Models_V3,
  Integ_V1, Integ_V2, Integ_V3,
});
