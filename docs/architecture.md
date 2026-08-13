# System Architecture

## Context

WoundAI is an academic decision-support platform. It accepts wound photographs, obtains a classification from a research model, stores the result, and supports expert validation.

## Logical architecture

```text
Browser
  |
  | HTTPS
  v
Next.js / Vercel
  | \
  |  \-- Supabase Auth
  |  \-- Supabase PostgreSQL
  |  \-- Supabase private Storage
  |
  \---- FastAPI AI Service
            |
            \-- PyTorch / EfficientNet-B0
            \-- Future Grad-CAM
```

## Separation of concerns

### Next.js
- presentation;
- session-aware user workflows;
- input validation;
- orchestration between storage, database and AI service.

### Supabase
- identity;
- relational persistence;
- private file storage;
- row-level authorization.

### AI microservice
- image decoding;
- preprocessing;
- model inference;
- probability output;
- future explainability.

## Security design

- private image bucket;
- user-specific storage path;
- RLS for tables;
- no service-role key in browser code;
- 8 MB file limit;
- MIME allow-list;
- no public wound-image URLs in MVP;
- research role separated from participant role.

## Production hardening still required

Before real human-subject use:
- institutional ethics/privacy review;
- explicit informed consent and retention policy;
- encryption/key-management review;
- malware/content validation where appropriate;
- data deletion workflow;
- audit-event completeness;
- stricter reviewer/admin role management;
- signed AI-service authentication;
- rate limits;
- vulnerability scanning;
- disaster recovery;
- threat modeling;
- jurisdiction-specific health/privacy compliance review.
