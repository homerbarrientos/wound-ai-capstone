"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { AnalysisResult } from "@/lib/types";

export default function AnalyzePage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return;
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [file]);

  function selectFile(e: ChangeEvent<HTMLInputElement>) {
    setResult(null);
    setError("");
    setFile(e.target.files?.[0] ?? null);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();

    if (!file) return;

    setBusy(true);
    setError("");
    setResult(null);

    const { data: auth } = await supabase.auth.getSession();
    const token = auth.session?.access_token;

    if (!token) {
      setBusy(false);
      setError("Please sign in before analyzing an image.");
      return;
    }

    const body = new FormData();
    body.append("image", file);

    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`
      },
      body
    });

    const payload = await response.json();

    setBusy(false);

    if (!response.ok) {
      setError(payload.error ?? "Analysis failed.");
      return;
    }

    setResult(payload);
  }

  return (
    <div className="grid two">
      <section className="card">
        <h1>Analyze wound image</h1>

        <p className="muted">
          Upload a JPG, PNG or WEBP image for research wound screening using
          the trained EfficientNet-B0 model.
        </p>

        <form className="form" onSubmit={submit}>
          <label className="dropzone">
            <span>Select wound image</span>

            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              required
              onChange={selectFile}
            />
          </label>

          {file && (
            <p className="small muted">
              Selected: {file.name} •{" "}
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          )}

          {error && <div className="error">{error}</div>}

          <button
            className="button primary"
            disabled={!file || busy}
          >
            {busy ? "Analyzing..." : "Run AI analysis"}
          </button>
        </form>
      </section>

      <section className="card">
        <h2>Result</h2>

        {result && previewUrl && (
          <div style={{ marginBottom: 20 }}>
            <p className="small">UPLOADED IMAGE</p>

            <img
              src={previewUrl}
              alt="Uploaded wound preview"
              style={{
                width: "100%",
                maxHeight: "320px",
                objectFit: "contain",
                borderRadius: "12px",
                border: "1px solid #d8e0e5"
              }}
            />
          </div>
        )}

        {!result && (
          <p className="muted">
            No analysis yet.
          </p>
        )}

        {result && (
          <>
            <div className="result">
              <p className="small">
                POSSIBLE CLASSIFICATION
              </p>

              <div className="kpi">
                {result.uncertain
                  ? "Uncertain"
                  : result.category}
              </div>

              <p>
                Confidence:{" "}
                <strong>
                  {Math.round(result.confidence * 100)}%
                </strong>
              </p>

              <p className="small">
                Model: {result.modelName} •{" "}
                {result.modelVersion}
              </p>
            </div>

            <h3 style={{ marginTop: 24 }}>
              Class probabilities
            </h3>

            {result.scores.map((score) => (
              <div
                className="score"
                key={score.category}
              >
                <div className="scoreline">
                  <span>{score.category}</span>

                  <strong>
                    {Math.round(
                      score.probability * 100
                    )}
                    %
                  </strong>
                </div>

                <div className="bar">
                  <span
                    style={{
                      width: `${score.probability * 100}%`
                    }}
                  />
                </div>
              </div>
            ))}

            {result.woundType && (
              <>
                <div
                  className="result"
                  style={{ marginTop: 24 }}
                >
                  <p className="small">
                    POSSIBLE WOUND TYPE
                  </p>

                  <div className="kpi">
                    {result.woundTypeUncertain
                      ? "Uncertain"
                      : result.woundType}
                  </div>

                  <p>
                    Confidence:{" "}
                    <strong>
                      {Math.round(
                        (result.woundTypeConfidence ?? 0) *
                          100
                      )}
                      %
                    </strong>
                  </p>

                  <p className="small">
                    Model:{" "}
                    {result.woundTypeModelName} •{" "}
                    {result.woundTypeModelVersion}
                  </p>
                </div>

                <h3 style={{ marginTop: 24 }}>
                  Wound type probabilities
                </h3>

                {(result.woundTypeScores ?? []).map(
                  (score) => (
                    <div
                      className="score"
                      key={score.category}
                    >
                      <div className="scoreline">
                        <span>
                          {score.category}
                        </span>

                        <strong>
                          {Math.round(
                            score.probability * 100
                          )}
                          %
                        </strong>
                      </div>

                      <div className="bar">
                        <span
                          style={{
                            width: `${score.probability * 100}%`
                          }}
                        />
                      </div>
                    </div>
                  )
                )}
              </>
            )}

            <div
              className="warning"
              style={{ marginTop: 20 }}
            >
              Research/decision-support result only.
              This is not a medical diagnosis.
            </div>
          </>
        )}
      </section>
    </div>
  );
}