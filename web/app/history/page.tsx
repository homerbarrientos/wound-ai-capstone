"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { supabase } from "@/lib/supabase";

type HistoryRow = {
  id: string;
  predicted_class: string;
  confidence_score: number;
  is_uncertain: boolean;
  created_at: string;
  wound_type: string | null;
  wound_type_confidence: number | null;
  model_versions: {
    name: string;
    version: string;
  } | null;
  wound_type_model_versions: {
  name: string;
  version: string;
  } | null;
  wound_images: {
    original_filename: string | null;
    storage_path: string;
  } | null;
};
type ViewRow = HistoryRow & {
  thumbnailUrl?: string;
};
/*
 * When wound-type classification exists, display its confidence.
 * Otherwise, display the binary Wound/Normal confidence.
 */
function getDisplayConfidence(row: HistoryRow): number {
  if (
    row.wound_type &&
    row.wound_type_confidence !== null
  ) {
    return row.wound_type_confidence;
  }

  return row.confidence_score;
}
/*
 * When wound-type classification exists, display its label.
 * Otherwise, display the binary Wound/Normal label.
 */
function getDisplayClass(row: HistoryRow): string {
  return row.wound_type ?? row.predicted_class;
}
function getDisplayModel(row: HistoryRow): string {
  const model =
    row.wound_type && row.wound_type_model_versions
      ? row.wound_type_model_versions
      : row.model_versions;

  return model
    ? `${model.name} • ${model.version}`
    : "Model unavailable";
}

export default function HistoryPage() {
  const [rows, setRows] = useState<ViewRow[]>([]);
  const [message, setMessage] = useState("Loading...");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    async function load() {
      const { data: auth, error: authError } =
        await supabase.auth.getUser();

      if (authError || !auth.user) {
        setMessage(
          "Please sign in to view your analysis history."
        );
        return;
      }

      const { data, error } = await supabase
        .from("predictions")
        .select(`
          id,
          predicted_class,
          confidence_score,
          is_uncertain,
          created_at,
          wound_type,
          wound_type_confidence,
          wound_type_model_versions:model_versions!predictions_wound_type_model_version_id_fkey(
            name,
            version
          ),
          wound_images(
            original_filename,
            storage_path
          )
        `)
        .order("created_at", { ascending: false });

      if (error) {
        setMessage(error.message);
        return;
      }

      const baseRows =
        (data ?? []) as unknown as HistoryRow[];

      const withThumbnails = await Promise.all(
        baseRows.map(async (row) => {
          const path = row.wound_images?.storage_path;

          if (!path) {
            return row;
          }

          const { data: signed } = await supabase.storage
            .from("wound-images")
            .createSignedUrl(path, 600);

          return {
            ...row,
            thumbnailUrl: signed?.signedUrl,
          };
        })
      );

      setRows(withThumbnails);
      setMessage("");
    }

    load();
  }, []);

  /*
   * Filter options now use the displayed classification.
   * Example: Diabetic, Pressure, Surgical, Venous.
   */
  const classes = useMemo(() => {
    return Array.from(
      new Set(rows.map((row) => getDisplayClass(row)))
    ).sort();
  }, [rows]);

  const visibleRows = useMemo(() => {
    const term = search.trim().toLowerCase();

    return rows.filter((row) => {
      const filename =
        row.wound_images?.original_filename ?? "";

      const model = row.model_versions
        ? `${row.model_versions.name} ${row.model_versions.version}`
        : "";

      const displayClass = getDisplayClass(row);

      const matchesSearch =
        !term ||
        displayClass.toLowerCase().includes(term) ||
        row.predicted_class.toLowerCase().includes(term) ||
        filename.toLowerCase().includes(term) ||
        model.toLowerCase().includes(term);

      const matchesFilter =
        filter === "all" ||
        (filter === "uncertain" && row.is_uncertain) ||
        (filter === "confident" && !row.is_uncertain) ||
        displayClass === filter;

      return matchesSearch && matchesFilter;
    });
  }, [rows, search, filter]);

  const uncertainCount = rows.filter(
    (row) => row.is_uncertain
  ).length;

  /*
   * Average uses wound-type confidence when available.
   * Otherwise, it falls back to binary confidence.
   */
  const averageConfidence = rows.length
    ? rows.reduce(
        (sum, row) =>
          sum + getDisplayConfidence(row),
        0
      ) / rows.length
    : 0;

  return (
    <>
      <section className="history-header">
        <div>
          <p className="small history-eyebrow">
            RESEARCH RECORDS
          </p>

          <h1>Analysis history</h1>

          <p className="muted">
            Review previous image analyses, model versions,
            and confidence scores.
          </p>
        </div>

        <Link
          href="/analyze"
          className="button primary"
        >
          New analysis
        </Link>
      </section>

      <section className="history-stats">
        <article className="card">
          <p className="small muted">
            TOTAL ANALYSES
          </p>

          <div className="kpi">
            {rows.length}
          </div>
        </article>

        <article className="card">
          <p className="small muted">
            UNCERTAIN RESULTS
          </p>

          <div className="kpi">
            {uncertainCount}
          </div>
        </article>

        <article className="card">
          <p className="small muted">
            AVG. CONFIDENCE
          </p>

          <div className="kpi">
            {rows.length
              ? `${Math.round(
                  averageConfidence * 100
                )}%`
              : "—"}
          </div>
        </article>
      </section>

      <section className="card history-controls">
        <input
          placeholder="Search by result, filename, or model..."
          value={search}
          onChange={(event) =>
            setSearch(event.target.value)
          }
        />

        <select
          value={filter}
          onChange={(event) =>
            setFilter(event.target.value)
          }
        >
          <option value="all">
            All results
          </option>

          <option value="confident">
            Confident only
          </option>

          <option value="uncertain">
            Uncertain only
          </option>

          {classes.map((className) => (
            <option
              key={className}
              value={className}
            >
              {className}
            </option>
          ))}
        </select>
      </section>

      {message && (
        <section className="card">
          {message}
        </section>
      )}

      <section className="history-grid">
        {visibleRows.map((row) => {
          const displayClass =
            getDisplayClass(row);

          const displayConfidence =
            getDisplayConfidence(row);

          return (
            <article
              className="history-card"
              key={row.id}
            >
              <div className="history-image">
                {row.thumbnailUrl ? (
                  <img
                    src={row.thumbnailUrl}
                    alt={
                      row.wound_images
                        ?.original_filename ??
                      "Uploaded analysis"
                    }
                  />
                ) : (
                  <div className="history-image-placeholder">
                    No preview
                  </div>
                )}
              </div>

              <div className="history-card-body">
                <div className="history-card-topline">
                  <span
                    className={
                      row.is_uncertain
                        ? "status uncertain"
                        : "status confident"
                    }
                  >
                    {row.is_uncertain
                      ? "Uncertain"
                      : "Classified"}
                  </span>

                  <span className="small muted">
                    {new Date(
                      row.created_at
                    ).toLocaleDateString()}
                  </span>
                </div>

                <h2>
                  {row.is_uncertain
                    ? "Uncertain result"
                    : displayClass}
                </h2>

                <p className="muted history-filename">
                  {row.wound_images
                    ?.original_filename ??
                    "Uploaded image"}
                </p>

                <div className="history-confidence">
                  <div className="scoreline">
                    <span>Confidence</span>

                    <strong>
                      {(
                        displayConfidence * 100
                      ).toFixed(1)}
                      %
                    </strong>
                  </div>

                  <div className="bar">
                    <span
                      style={{
                        width: `${
                          displayConfidence * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>

                {/* <p className="small muted">
                  {row.model_versions
                    ? `${row.model_versions.name} • ${row.model_versions.version}`
                    : "Model unavailable"}
                </p> */}
                <p className="small muted">
                {getDisplayModel(row)}
              </p>

                <Link
                  className="button history-view"
                  href={`/history/${row.id}`}
                >
                  View details
                </Link>
              </div>
            </article>
          );
        })}
      </section>
    </>
  );
}