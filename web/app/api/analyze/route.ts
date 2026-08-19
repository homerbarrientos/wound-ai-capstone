import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const MAX_IMAGE_BYTES = 8 * 1024 * 1024;
const ALLOWED_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
    }

    const token = authHeader.slice("Bearer ".length);
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
    const supabaseAnon = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!;
    const aiUrl = process.env.AI_SERVICE_URL ?? "http://localhost:8000";

    const supabase = createClient(supabaseUrl, supabaseAnon, {
      global: { headers: { Authorization: `Bearer ${token}` } }
    });

    const { data: userData, error: userError } = await supabase.auth.getUser(token);
    if (userError || !userData.user) {
      return NextResponse.json({ error: "Invalid session." }, { status: 401 });
    }

    const form = await request.formData();
    const image = form.get("image");

    if (!(image instanceof File)) {
      return NextResponse.json({ error: "Image is required." }, { status: 400 });
    }
    if (!ALLOWED_TYPES.has(image.type)) {
      return NextResponse.json({ error: "Only JPG, PNG and WEBP images are accepted." }, { status: 415 });
    }
    if (image.size > MAX_IMAGE_BYTES) {
      return NextResponse.json({ error: "Image must be 8 MB or smaller." }, { status: 413 });
    }

    const safeExtension = image.type === "image/png" ? "png" : image.type === "image/webp" ? "webp" : "jpg";
    const imageId = crypto.randomUUID();
    const storagePath = `${userData.user.id}/${imageId}.${safeExtension}`;
    const bytes = await image.arrayBuffer();

    const { error: uploadError } = await supabase.storage
      .from("wound-images")
      .upload(storagePath, bytes, { contentType: image.type, upsert: false });

    if (uploadError) {
      return NextResponse.json({ error: `Storage upload failed: ${uploadError.message}` }, { status: 500 });
    }

    const { data: imageRow, error: imageInsertError } = await supabase
      .from("wound_images")
      .insert({
        id: imageId,
        user_id: userData.user.id,
        storage_path: storagePath,
        original_filename: image.name,
        mime_type: image.type,
        file_size_bytes: image.size
      })
      .select("id")
      .single();

    if (imageInsertError) {
      await supabase.storage.from("wound-images").remove([storagePath]);
      return NextResponse.json({ error: imageInsertError.message }, { status: 500 });
    }

    const aiForm = new FormData();
    aiForm.append("image", new Blob([bytes], { type: image.type }), image.name);

    const aiResponse = await fetch(`${aiUrl}/v1/predict`, {
      method: "POST",
      body: aiForm,
      cache: "no-store"
    });

    if (!aiResponse.ok) {
      return NextResponse.json({ error: "AI service failed to analyze the image." }, { status: 502 });
    }

    const ai = await aiResponse.json();

    let gradcamStoragePath: string | null = null;

    if (ai.gradcam_image_base64) {
      const gradcamBytes = Buffer.from(
        ai.gradcam_image_base64,
        "base64"
      );

      gradcamStoragePath = `${userData.user.id}/${imageId}-gradcam.jpg`;

      const { error: gradcamUploadError } = await supabase.storage
        .from("wound-images")
        .upload(
          gradcamStoragePath,
          gradcamBytes,
          {
            contentType: "image/jpeg",
            upsert: false
          }
        );

      if (gradcamUploadError) {
        return NextResponse.json(
          {
            error: `Grad-CAM upload failed: ${gradcamUploadError.message}`
          },
          { status: 500 }
        );
      }
    }

    const { data: model } = await supabase
      .from("model_versions")
      .select("id")
      .eq("name", ai.model_name)
      .eq("version", ai.model_version)
      .maybeSingle();

    const modelId = model?.id ?? null;

    let woundTypeModelId: string | null = null;

    if (ai.wound_type_model_name && ai.wound_type_model_version) {
      const { data: woundTypeModel } = await supabase
        .from("model_versions")
        .select("id")
        .eq("name", ai.wound_type_model_name)
        .eq("version", ai.wound_type_model_version)
        .maybeSingle();

      woundTypeModelId = woundTypeModel?.id ?? null;
    }

    if (!modelId) {
      return NextResponse.json(
        { error: `Model version ${ai.model_name} ${ai.model_version} is not registered in research metadata.` },
        { status: 500 }
      );
    }

    const { data: prediction, error: predictionError } = await supabase
      .from("predictions")
      .insert({
        wound_image_id: imageRow.id,
        model_version_id: modelId,
        predicted_class: ai.predicted_class,
        confidence_score: ai.confidence,
        is_uncertain: ai.is_uncertain,

        wound_type: ai.wound_type ?? null,
        wound_type_confidence: ai.wound_type_confidence ?? null,
        wound_type_uncertain: ai.wound_type_uncertain ?? null,
        wound_type_model_version_id: woundTypeModelId,
        gradcam_storage_path: gradcamStoragePath
      })
      .select("id")
      .single();

    if (predictionError) {
      return NextResponse.json({ error: predictionError.message }, { status: 500 });
    }

    const scoreRows = ai.scores.map((s: { category: string; probability: number }) => ({
      prediction_id: prediction.id,
      category: s.category,
      probability: s.probability
    }));

    const { error: scoresError } = await supabase.from("prediction_scores").insert(scoreRows);
    if (scoresError) {
      return NextResponse.json({ error: scoresError.message }, { status: 500 });
    }

    if (
      Array.isArray(ai.wound_type_scores) &&
      ai.wound_type_scores.length > 0
    ) {
      const woundTypeScoreRows = ai.wound_type_scores.map(
        (s: { category: string; probability: number }) => ({
          prediction_id: prediction.id,
          category: s.category,
          probability: s.probability
        })
      );

      const { error: woundTypeScoresError } = await supabase
        .from("wound_type_scores")
        .insert(woundTypeScoreRows);

      if (woundTypeScoresError) {
        return NextResponse.json(
          { error: woundTypeScoresError.message },
          { status: 500 }
        );
      }
    }

    return NextResponse.json({
      predictionId: prediction.id,
      category: ai.predicted_class,
      confidence: ai.confidence,
      uncertain: ai.is_uncertain,
      scores: ai.scores,
      modelName: ai.model_name,
      modelVersion: ai.model_version,

      woundType: ai.wound_type ?? null,
      woundTypeConfidence: ai.wound_type_confidence ?? null,
      woundTypeUncertain: ai.wound_type_uncertain ?? null,
      woundTypeScores: ai.wound_type_scores ?? [],
      woundTypeModelName: ai.wound_type_model_name ?? null,
      woundTypeModelVersion: ai.wound_type_model_version ?? null
    });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: "Unexpected server error." }, { status: 500 });
  }
}
