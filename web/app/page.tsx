import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <p className="small">MASTER'S CAPSTONE • COMPUTER VISION • EXPLAINABLE AI</p>
        <h1>Wound image classification as decision support, not diagnosis.</h1>
        <p>
          A research platform for comparing deep-learning models, recording confidence,
          supporting expert review, and studying explainability for wound-image classification.
        </p>
        <div className="navlinks">
          <Link className="button primary" href="/analyze">Start analysis</Link>
          <Link className="button" href="/research">View research dashboard</Link>
        </div>
      </section>

      <section className="grid">
        <article className="card">
          <h3>Classification</h3>
          <p className="muted">Abrasion, laceration, burn, puncture, surgical wound, and unknown.</p>
        </article>
        <article className="card">
          <h3>Explainability</h3>
          <p className="muted">Grad-CAM is planned to show the image regions influencing model output.</p>
        </article>
        <article className="card">
          <h3>Research Evaluation</h3>
          <p className="muted">Compare accuracy, precision, recall, macro F1 and inference performance.</p>
        </article>
      </section>

      <p className="warning" style={{ marginTop: 24 }}>
        This system is for academic research and decision-support only. It must not be used as a substitute for professional medical assessment.
      </p>
    </>
  );
}
