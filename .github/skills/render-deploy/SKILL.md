---
name: render-deploy
description: 'Deploy a Python web app to Render from GitHub. Use when publishing a local Flask or similar app, creating or updating its GitHub repository, configuring Render build and start commands, adding health checks, troubleshooting failed deploys, or obtaining a live Render URL.'
argument-hint: '[app path, GitHub repository, or deployment issue]'
user-invocable: true
disable-model-invocation: false
---

# GitHub to Render Deployment

## What This Skill Produces

A verified GitHub-backed Render web service with:

- source committed to the intended GitHub repository;
- dependencies installed by Render;
- a production WSGI start command;
- a health endpoint configured when the app provides one;
- a live URL tested after deployment.

Never expose or request passwords, personal access tokens, or API keys in chat. Use the user's authenticated GitHub and Render sessions, GitHub CLI prompts, or the provider's browser UI.

## When to Use

Use this skill for requests containing terms such as `GitHub`, `push`, `publish`, `Render`, `deploy`, `live link`, `production URL`, `Flask`, `gunicorn`, or `health check`.

## Procedure

### 1. Inspect the app and repository

1. Identify the application entry point and framework.
2. Find the dependency file (`requirements.txt`, `pyproject.toml`, or equivalent).
3. Find an existing production start command, health route, and port handling.
4. Run the app's narrowest available smoke check locally. For Flask, prefer importing the app and requesting `/health` with its test client.
5. Check Git status, current branch, remotes, and ignored files. Preserve unrelated user changes.
6. If the folder is not a Git repository, ask whether to initialize it here or use an existing repository path.

For this repository, the expected local facts are:

- entry point: `app.py`, exposing `app`;
- dependencies: `requirements.txt`;
- frontend: files in the project root, served by Flask;
- health endpoint: `GET /health`;
- Render start command: `gunicorn app:app`.

### 2. Make the deployment contract production-ready

1. Ensure the production server is declared in the dependency file. For this Flask app, add `gunicorn` alongside Flask if it is absent.
2. Keep development-only behavior such as `debug=True` inside the `__main__` block; Render must import the WSGI object through Gunicorn.
3. Ensure the server binds through Gunicorn's default Render port behavior. Do not hard-code a second server process or rely on the Flask development server.
4. Confirm the app does not require local files outside the repository and does not contain secrets.
5. Add or preserve a lightweight health route. A successful response should be deterministic and should not depend on a browser session.
6. Avoid unrelated refactors.

### 3. Create or connect the GitHub repository

1. If no remote exists, clarify the desired repository name and visibility before creating one.
2. Initialize Git only after confirming the intended project root.
3. Add a focused `.gitignore` covering Python caches, virtual environments, local environment files, editor metadata, and generated logs.
4. Review `git diff` and `git status`; do not commit secrets or unrelated files.
5. Create a descriptive initial commit, or a focused deployment commit when history already exists.
6. Add the user's GitHub remote and push the intended branch. Verify the remote URL and pushed branch.
7. If GitHub authentication is unavailable, stop at the exact command or browser action requiring the user's authenticated session and report it clearly.

### 4. Configure Render

Create a Render **Web Service** connected to the pushed GitHub repository.

Use these defaults unless the project explicitly requires different values:

- Environment: `Python 3`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Health check path: `/health`

Set environment variables only when the application requires them. Do not place secrets in Git, `requirements.txt`, source files, or skill output.

If the repository has a `render.yaml`, prefer keeping the service configuration there and avoid duplicating conflicting dashboard settings. If Render asks for a branch, use the branch that was pushed and verified.

### 5. Verify deployment

1. Wait for the Render build and deploy to finish.
2. Open the assigned `onrender.com` URL.
3. Request `<live-url>/health` and verify an HTTP 200 response with the expected JSON status.
4. Exercise one real conversion through `POST /transliterate` using a small known input.
5. Confirm the root page loads and that browser requests target same-origin API paths unless a separate API URL is intentional.
6. If deployment fails, classify the failure before changing code:
   - dependency/build failure;
   - import or start-command failure;
   - missing environment variable;
   - health-check failure;
   - runtime request failure.
7. Inspect the relevant Render log, make the smallest local fix, commit and push it, then redeploy and repeat the same check.

### 6. Report the result

Provide:

- GitHub repository URL;
- Render service URL;
- branch deployed;
- build and start commands;
- health-check result;
- any remaining limitation or manual action.

Do not claim success without a verified live URL and a successful health request. If authentication or provider access blocks completion, report what was completed and the one concrete action the user must perform.

## Completion Checklist

- [ ] Correct project root and entry point confirmed.
- [ ] Production server dependency declared.
- [ ] Secrets and generated files excluded.
- [ ] Git commit reviewed and pushed to the intended GitHub branch.
- [ ] Render Web Service uses the intended repository and branch.
- [ ] Build command succeeds.
- [ ] Start command succeeds.
- [ ] `/health` returns HTTP 200 in production.
- [ ] Root page and one real API request work through the live URL.
- [ ] URLs and any remaining manual step reported accurately.
