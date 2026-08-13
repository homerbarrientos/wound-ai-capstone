const demoModels = [
  { name: "EfficientNet-B0", accuracy: "—", precision: "—", recall: "—", f1: "—" },
  { name: "ResNet", accuracy: "—", precision: "—", recall: "—", f1: "—" },
  { name: "MobileNet", accuracy: "—", precision: "—", recall: "—", f1: "—" }
];

export default function ResearchPage() {
  return (
    <>
      <section className="card">
        <p className="small">RESEARCH DASHBOARD</p>
        <h1>Model comparison</h1>
        <p className="muted">
          Values remain blank until experiments are completed. Do not publish fabricated performance metrics.
        </p>
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr><th>Model</th><th>Accuracy</th><th>Macro Precision</th><th>Macro Recall</th><th>Macro F1</th></tr>
            </thead>
            <tbody>
              {demoModels.map((m) => (
                <tr key={m.name}>
                  <td><strong>{m.name}</strong></td>
                  <td>{m.accuracy}</td>
                  <td>{m.precision}</td>
                  <td>{m.recall}</td>
                  <td>{m.f1}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid" style={{ marginTop: 18 }}>
        <div className="card"><p className="small">PRIMARY METRIC</p><div className="kpi">Macro F1</div><p className="muted">Useful when wound classes are imbalanced.</p></div>
        <div className="card"><p className="small">EXPLAINABILITY</p><div className="kpi">Grad-CAM</div><p className="muted">Planned heatmap visualization.</p></div>
        <div className="card"><p className="small">UNCERTAINTY</p><div className="kpi">Abstain</div><p className="muted">Low-confidence outputs should be marked uncertain.</p></div>
      </section>
    </>
  );
}
