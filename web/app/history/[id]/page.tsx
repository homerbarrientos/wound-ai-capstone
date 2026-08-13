"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

type Score = { category: string; probability: number };

type PredictionDetail = {
  id: string;
  predicted_class: string;
  confidence_score: number;
  is_uncertain: boolean;
  created_at: string;
  model_versions: { name: string; version: string; status: string } | null;
  wound_images: {
    original_filename: string | null;
    storage_path: string;
    mime_type: string;
    file_size_bytes: number;
  } | null;
};

export default function HistoryDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [prediction, setPrediction] = useState<PredictionDetail | null>(null);
  const [scores, setScores] = useState<Score[]>([]);
  const [imageUrl, setImageUrl] = useState("");
  const [message, setMessage] = useState("Loading analysis...");

  useEffect(() => {
    async function load() {
      const { data: auth } = await supabase.auth.getUser();
      if (!auth.user) {
        setMessage("Please sign in to view this analysis.");
        return;
      }

      const { data, error } = await supabase
        .from("predictions")
        .select(`
          id,predicted_class,confidence_score,is_uncertain,created_at,
          model_versions(name,version,status),
          wound_images(original_filename,storage_path,mime_type,file_size_bytes)
        `)
        .eq("id", params.id)
        .single();

      if (error) {
        setMessage(error.message);
        return;
      }

      const detail = data as unknown as PredictionDetail;
      setPrediction(detail);

      const { data: scoreData, error: scoreError } = await supabase
        .from("prediction_scores")
        .select("category,probability")
        .eq("prediction_id", params.id)
        .order("probability", { ascending: false });

      if (scoreError) {
        setMessage(scoreError.message);
        return;
      }

      setScores((scoreData ?? []) as Score[]);

      if (detail.wound_images?.storage_path) {
        const { data: signed } = await supabase.storage
          .from("wound-images")
          .createSignedUrl(detail.wound_images.storage_path, 600);
        setImageUrl(signed?.signedUrl ?? "");
      }

      setMessage("");
    }
    if (params.id) load();
  }, [params.id]);

  if (message) return <section className="card"><Link href="/history" className="back-link">← Back to history</Link><p>{message}</p></section>;
  if (!prediction) return <section className="card"><p>Analysis not found.</p></section>;
  
  async function deleteAnalysis() {
    const confirmed = window.confirm(
      "Delete this analysis permanently? The prediction, probability scores, database image record, and uploaded image will be removed."
    );

    if (!confirmed) {
      return;
    }

    setDeleting(true);
    setDeleteError("");

    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        throw new Error("Please sign in before deleting an analysis.");
      }

      const response = await fetch(`/api/predictions/${params.id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error ?? "Unable to delete analysis.");
      }

      router.push("/history");
      router.refresh();
    } catch (error) {
      setDeleteError(
        error instanceof Error
          ? error.message
          : "Unable to delete analysis."
      );
    } finally {
      setDeleting(false);
    }
  }
  return (
    <>
      <div className="detail-heading">
        <div>
          <Link href="/history" className="back-link">← Back to history</Link>
          <p className="small history-eyebrow">ANALYSIS RECORD</p>
          <h1>{prediction.is_uncertain ? "Uncertain result" : prediction.predicted_class}</h1>
          <p className="muted">{new Date(prediction.created_at).toLocaleString()}</p>
        </div>
        <span className={prediction.is_uncertain ? "status uncertain" : "status confident"}>
          {prediction.is_uncertain ? "Expert review recommended" : "Model classified"}
        </span>
      </div>

      <div className="detail-grid">
        <section className="card">
          <h2>Uploaded image</h2>
          <div className="detail-image">
            {imageUrl ? <img src={imageUrl} alt={prediction.wound_images?.original_filename ?? "Uploaded image"} /> : <div className="history-image-placeholder">Preview unavailable</div>}
          </div>
          <div className="detail-metadata">
            <div><span className="small muted">FILE</span><strong>{prediction.wound_images?.original_filename ?? "—"}</strong></div>
            <div><span className="small muted">TYPE</span><strong>{prediction.wound_images?.mime_type ?? "—"}</strong></div>
            <div><span className="small muted">SIZE</span><strong>{prediction.wound_images ? `${(prediction.wound_images.file_size_bytes / 1024 / 1024).toFixed(2)} MB` : "—"}</strong></div>
          </div>
        </section>

        <section className="card">
          <p className="small history-eyebrow">AI OUTPUT</p>
          <h2>Possible classification</h2>
          <div className="detail-result">
            <div><span className="small muted">RESULT</span><div className="detail-result-name">{prediction.is_uncertain ? "Uncertain" : prediction.predicted_class}</div></div>
            <div><span className="small muted">CONFIDENCE</span><div className="detail-confidence">{(prediction.confidence_score * 100).toFixed(1)}%</div></div>
          </div>
          <div className="bar detail-main-bar"><span style={{ width: `${prediction.confidence_score * 100}%` }} /></div>
          <div className="detail-model"><span className="small muted">MODEL VERSION</span><strong>{prediction.model_versions ? `${prediction.model_versions.name} • ${prediction.model_versions.version}` : "—"}</strong></div>
          <div className="warning">Research/decision-support result only. This is not a medical diagnosis.</div>
          {deleteError && (
          <div className="error" style={{ marginTop: "16px" }}>
            {deleteError}
          </div>
)}

<button
  type="button"
  className="button delete-button"
  onClick={deleteAnalysis}
  disabled={deleting}
>
  {deleting ? "Deleting..." : "Delete Analysis"}
</button>
        </section>
      </div>

      <section className="card detail-scores">
        <div className="detail-section-title"><div><p className="small history-eyebrow">MODEL DISTRIBUTION</p><h2>Class probabilities</h2></div><span className="small muted">{scores.length} classes</span></div>
        {scores.map((score, index) => (
          <div className="detail-score-row" key={score.category}>
            <div className="detail-score-rank">{index + 1}</div>
            <div className="detail-score-main">
              <div className="scoreline"><span>{score.category}</span><strong>{(score.probability * 100).toFixed(1)}%</strong></div>
              <div className="bar"><span style={{ width: `${score.probability * 100}%` }} /></div>
            </div>
          </div>
        ))}
      </section>

      <section className="card phase-placeholder">
        <p className="small history-eyebrow">EXPLAINABILITY</p>
        <h2>Grad-CAM visualization</h2>
        <p className="muted">Reserved for the Explainable AI phase.</p>
      </section>
    </>
  );
}
