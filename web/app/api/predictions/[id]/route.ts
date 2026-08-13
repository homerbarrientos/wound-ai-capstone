import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await context.params;

    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const anonKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

    if (!url || !anonKey) {
      return NextResponse.json(
        { error: "Missing Supabase environment variables." },
        { status: 500 }
      );
    }

    // Forward the logged-in user's access token.
    const authHeader = request.headers.get("authorization");

    if (!authHeader) {
      return NextResponse.json(
        { error: "Authentication required." },
        { status: 401 }
      );
    }

    const supabase = createClient(url, anonKey, {
      global: {
        headers: {
          Authorization: authHeader,
        },
      },
    });

    // Get the prediction and its associated image.
    // RLS should ensure that the user can only access their own record.
    const { data: prediction, error: predictionError } = await supabase
      .from("predictions")
      .select(`
        id,
        wound_image_id,
        wound_images (
          id,
          storage_path
        )
      `)
      .eq("id", id)
      .single();

    if (predictionError || !prediction) {
      return NextResponse.json(
        { error: predictionError?.message ?? "Prediction not found." },
        { status: 404 }
      );
    }

    // Remove class probability records first.
    const { error: scoresError } = await supabase
      .from("prediction_scores")
      .delete()
      .eq("prediction_id", id);

    if (scoresError) {
      throw scoresError;
    }

    // Remove prediction.
    const { error: deletePredictionError } = await supabase
      .from("predictions")
      .delete()
      .eq("id", id);

    if (deletePredictionError) {
      throw deletePredictionError;
    }

    const image = Array.isArray(prediction.wound_images)
      ? prediction.wound_images[0]
      : prediction.wound_images;

    if (image?.storage_path) {
      const { error: storageError } = await supabase.storage
        .from("wound-images")
        .remove([image.storage_path]);

      if (storageError) {
        throw storageError;
      }
    }

    if (prediction.wound_image_id) {
      const { error: imageError } = await supabase
        .from("wound_images")
        .delete()
        .eq("id", prediction.wound_image_id);

      if (imageError) {
        throw imageError;
      }
    }

    return NextResponse.json({
      success: true,
    });
  } catch (error) {
    console.error("Delete analysis error:", error);

    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Unable to delete analysis.",
      },
      { status: 500 }
    );
  }
}