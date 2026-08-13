"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

type Row = {
  id: string;
  predicted_class: string;
  confidence_score: number;
  is_uncertain: boolean;
  created_at: string;
  model_versions: { name: string; version: string } | null;
};

export default function HistoryPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [message, setMessage] = useState("Loading...");

  useEffect(() => {
    async function load() {
      const { data: auth } = await supabase.auth.getUser();
      if (!auth.user) {
        setMessage("Please sign in to view history.");
        return;
      }

      const { data, error } = await supabase
        .from("predictions")
        .select("id,predicted_class,confidence_score,is_uncertain,created_at,model_versions(name,version)")
        .order("created_at", { ascending: false });

      if (error) {
        setMessage(error.message);
        return;
      }

      setRows((data ?? []) as unknown as Row[]);
      setMessage("");
    }
    load();
  }, []);

  return (
    <section className="card">
      <h1>Prediction history</h1>
      <p className="muted">RLS limits normal users to predictions associated with their own images.</p>

      {message && <p>{message}</p>}

      {!message && rows.length === 0 && <p>No predictions found.</p>}

      {rows.length > 0 && (
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr><th>Date</th><th>Result</th><th>Confidence</th><th>Model</th></tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{new Date(row.created_at).toLocaleString()}</td>
                  <td>{row.is_uncertain ? "Uncertain" : row.predicted_class}</td>
                  <td>{Math.round(row.confidence_score * 100)}%</td>
                  <td>{row.model_versions ? `${row.model_versions.name} ${row.model_versions.version}` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
