"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

const CLASSES = [
  "Normal",
  "Wound",
  "Diabetic",
  "Pressure",
  "Surgical",
  "Venous",
  "Other / Unknown"
];

type ReviewItem = {
  id: string;
  predicted_class: string;
  confidence_score: number;
  wound_type: string | null;
  wound_type_confidence: number | null;
  created_at: string;
  wound_images: { original_filename: string | null } | null;
};

export default function ReviewPage() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [message, setMessage] = useState("Loading...");
  const [selected, setSelected] = useState<Record<string, string>>({});

  async function load() {
    const { data: auth } = await supabase.auth.getUser();
    if (!auth.user) {
      setMessage("Please sign in with a reviewer/researcher account.");
      return;
    }

    const { data: profile } = await supabase
      .from("profiles")
      .select("role")
      .eq("id", auth.user.id)
      .single();

    if (!profile || !["reviewer", "researcher", "admin"].includes(profile.role)) {
      setMessage("This page requires reviewer, researcher or admin access.");
      return;
    }

    const { data, error } = await supabase
      .from("predictions")
      .select("id,predicted_class,confidence_score,wound_type,wound_type_confidence,created_at,wound_images(original_filename)")
      .order("created_at", { ascending: false })
      .limit(50);

    if (error) {
      setMessage(error.message);
      return;
    }

    setItems((data ?? []) as unknown as ReviewItem[]);
    setMessage("");
  }

  function getAiClass(item: ReviewItem) {
    return item.wound_type ?? item.predicted_class;
  }

  function getAiConfidence(item: ReviewItem) {
    return item.wound_type_confidence ?? item.confidence_score;
  }

  useEffect(() => { load(); }, []);

  async function submitReview(item: ReviewItem) {
    const { data: auth } = await supabase.auth.getUser();
    const reviewer = auth.user;
    const aiClass = getAiClass(item);
    const verifiedClass = selected[item.id] ?? aiClass;
    if (!reviewer) return;

    const { error } = await supabase.from("expert_reviews").upsert({
      prediction_id: item.id,
      reviewer_id: reviewer.id,
      verified_class: verifiedClass,
      is_prediction_correct: verifiedClass === aiClass
    }, { onConflict: "prediction_id,reviewer_id" });

    if (error) {
      alert(error.message);
    } else {
      alert("Review saved.");
    }
  }

  return (
    <section className="card">
      <p className="small">EXPERT WORKFLOW</p>
      <h1>Prediction review</h1>
      <p className="muted">
        This workflow records human verification separately from AI output so research metrics can distinguish model prediction from expert labels.
      </p>

      {message && <p>{message}</p>}

      {!message && (
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr><th>Image</th><th>AI prediction</th><th>Confidence</th><th>Verified class</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.wound_images?.original_filename ?? "Image"}</td>
                  <td>{getAiClass(item)}</td>
                  <td>{Math.round(getAiConfidence(item) * 100)}%</td>
                  <td>
                    <select
                      value={selected[item.id] ?? getAiClass(item)}
                      onChange={(e) => setSelected((old) => ({ ...old, [item.id]: e.target.value }))}
                    >
                      {CLASSES.map((c) => <option key={c}>{c}</option>)}
                    </select>
                  </td>
                  <td><button className="button primary" onClick={() => submitReview(item)}>Save review</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
