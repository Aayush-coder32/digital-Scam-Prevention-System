# AI-Powered Digital Scam Prevention System

**Detect Digital Scams Before They Harm You.** DSPS is a privacy-minded web application for reviewing suspicious messages, links, and payment QR content. It returns explainable indicators and safe next steps. It is not a guarantee, and a low-risk result does not establish safety.

## Current implementation

- React/Vite responsive dashboard with SMS, URL, QR, WhatsApp, and impersonation review pages.
- Express API with validation, Helmet, narrow credentialed CORS, rate limiting, Argon2 password hashing, short-lived HttpOnly access cookies, and per-user scan ownership for history.
- FastAPI analysis service with explainable baseline rules, URL structure inspection without fetching, UPI URI parsing, and bounded QR image decode.
- MongoDB-backed account and scan history when configured; scan submission remains available without an account, and is not persisted unless signed in with connected MongoDB.
- Reproducible optional text model training workflow. The runtime does not claim the trained model is active.

Authentication/scan-history APIs require MongoDB. Password reset, refresh-token rotation, email verification, admin workflows, PDF exports, and OCR are not implemented yet. The first release intentionally omits external threat reputation lookups and does not fetch URLs. Do not deploy as a complete production service until these gaps are closed and reviewed.

## Run locally

Prerequisites: Node.js 20+, Python 3.12+, and MongoDB 7 (optional for anonymous analysis; required for accounts/history).

1. Copy `server/.env.example` to `server/.env`, set two independent random JWT secrets and a MongoDB URI. Copy `client/.env.example` to `client/.env` if the API is not on localhost:5000.
2. Start AI service: `cd ai-service`, create/activate a virtual environment, `pip install -r requirements.txt`, then `uvicorn app.main:app --reload --port 8000`.
3. In another terminal from repository root, run `npm install`, then `npm run dev`.
4. Open `http://localhost:5173`. For local MongoDB, use `docker compose up mongo` or an existing MongoDB instance.

If the API reports `EADDRINUSE` on port 5000 after a restart, stop the previous Node API process or set another port in `server/.env` (for example, `PORT=5001`) and update the client's API base URL accordingly.

Or run API/database/AI with Docker Compose (`docker compose up --build`) and run the Vite client in a separate terminal. Set `JWT_ACCESS_SECRET` in your shell for anything beyond a throwaway local session.

## API

- `GET /api/health`, `GET /api/ready`
- `POST /api/auth/register`, `/login`, `/logout`; `GET /api/auth/me`
- `POST /api/scans/{sms|url|qr|whatsapp|impersonation}` JSON: `{ "text": "..." }` or `{ "url": "..." }`
- `GET /api/scans?page=1&limit=20`, `GET /api/scans/:id`, `DELETE /api/scans/:id`, `DELETE /api/scans`
- `GET /api/reports/summary`
- AI service `GET /health`, `POST /analyze/{type}`, and `POST /analyze/qr-image` multipart field `file` (PNG/JPEG/WebP, max 5 MB).

Scan output includes `scan_id`, `scan_type`, score, risk level, detection method, indicators, explanation, actions, uncertainty/confidence, model version, provider status, and timestamp. Heuristic scores are not calibrated fraud probabilities. Provider availability is explicit.

## Training

Read [training documentation](ai-service/training/README.md). Provide lawful, labeled data; preserve its provenance. Do not present sample or train/test metrics as real-world validated performance.

## Deployment notes

- **GitHub:** initialize/commit the monorepo; inspect `git diff` and scan for credentials before pushing. `.env` files and model artifacts are ignored.
- **MongoDB Atlas:** create a least-privilege database user, restrict network access to the deployment where feasible, and set `MONGODB_URI` in Render.
- **Render:** deploy `server/` using Node, build `npm install`, start `npm start`; deploy `ai-service/` as Python/Docker, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `AI_SERVICE_URL` to the private AI service URL, `CLIENT_ORIGIN` to the Vercel origin, and strong independent JWT secrets. Render's shell expansion in start commands may vary by service type; verify health endpoints.
- **Vercel:** set root to `client`, build `npm run build`, output `dist`, and set `VITE_API_BASE_URL` to the backend `/api` URL. Set `COOKIE_SECURE=true` in production and use HTTPS. Configure allowed origin exactly.
- Free hosting can sleep, cold-start, limit memory and ephemeral disk, and may not preserve generated model files. Use external persistent storage for model artifacts if needed.

## Security and privacy limitations

DSPS never opens suspicious URLs or starts a payment. No UPI PIN, OTP, CVV, or bank password should be submitted. The QR endpoint decodes images in memory and does not retain them. Current dashboard upload UI accepts pasted QR payloads; use the AI image endpoint directly until the image flow is connected. Do not send private messages to external providers without clear consent. Review retention requirements and add deletion schedules before production use.

## Checklist

- [x] Responsive dashboard and five scanner routes
- [x] Node API and FastAPI baseline analysis
- [x] Auth foundations and user-isolated scan history
- [x] URL and UPI analysis; bounded QR image decoding endpoint
- [x] Training interface and deployment configuration
- [ ] Refresh-token rotation, password reset, email verification
- [ ] OCR and QR upload flow in the browser
- [ ] Admin controls, false-positive reporting, PDF exports
- [ ] Automated unit/integration/security tests and production review
- [ ] Configure deployed services and credentials
