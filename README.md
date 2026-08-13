# WoundAI Capstone

Master's-level capstone scaffold for an **Explainable AI-based wound image classification decision-support system**.

## Architecture

- **Next.js 16 / React / TypeScript** — web application
- **Supabase** — Auth, PostgreSQL, Storage, Row Level Security
- **FastAPI** — AI inference microservice
- **PyTorch / Torchvision** — model implementation
- **EfficientNet-B0** — initial model architecture
- **Grad-CAM** — planned explainability layer
- **Vercel** — recommended Next.js deployment
- **Container host** — recommended FastAPI/PyTorch deployment

> Research/decision-support only. The application must not be presented as a medical diagnostic tool.

## MVP user flow

1. Create an account / sign in.
2. Upload a wound image.
3. Image is stored in a private Supabase bucket.
4. The Next.js app sends the image to the AI service.
5. The AI service returns a mock classification until a trained model is provided.
6. Prediction and class probabilities are saved in Supabase.
7. User sees category, confidence, alternatives and disclaimer.
8. Reviewer can later verify/correct the result.
9. Research dashboard can compare model metrics.

## Project structure

```text
wound-ai-capstone/
├── web/                    Next.js application
├── ai-service/             FastAPI + PyTorch-ready inference service
├── supabase/
│   └── migrations/         PostgreSQL schema + RLS
├── docs/
│   ├── architecture.md
│   └── research-plan.md
└── README.md
```

## 1. Create Supabase project

Create a Supabase project, then execute:

```text
supabase/migrations/001_initial_schema.sql
```

Create a private storage bucket named:

```text
wound-images
```

The SQL migration also contains storage policies that expect that bucket.

## 2. Configure web app

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

Set:

```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
AI_SERVICE_URL=http://localhost:8000
```

Open `http://localhost:3000`.

## 3. Start AI service

```bash
cd ai-service
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://localhost:8000/docs
```

## Mock mode

The AI service runs in `mock` mode by default. It returns deterministic-looking class probabilities so the full application can be tested before a trained model is ready.

To enable a trained model later:

```env
MODEL_MODE=torch
MODEL_PATH=./models/wound-efficientnet-b0.pt
```

You will still need to provide the trained weights produced by the research training pipeline.

## Initial wound classes

- Abrasion
- Laceration
- Burn
- Puncture
- Surgical Wound
- Other / Unknown

These are provisional research classes and should be finalized with the research adviser/domain expert before dataset annotation.

## Capstone safety boundary

Do not label the result as a diagnosis. Recommended UI language:

> Possible classification based on the research model. This result is for decision-support/research only and is not a medical diagnosis.

## Next research milestones

1. Finalize operational definitions of classes.
2. Obtain ethically sourced, consented/licensed wound-image data.
3. Establish expert annotation protocol.
4. Split data by patient/source to reduce leakage.
5. Train EfficientNet-B0 baseline.
6. Compare ResNet and MobileNet variants.
7. Add Grad-CAM.
8. Evaluate accuracy, macro precision, macro recall, macro F1, per-class metrics and confusion matrix.
9. Calibrate confidence / define abstention threshold.
10. Conduct expert usability/validation study if approved.
