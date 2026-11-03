# Task Tracker

A simple, dependency-free task tracker. This first version is the clean baseline: no intentional bugs have been added. The API and browser UI share an in-memory store, so tasks reset when the app restarts.

## Run with Docker

```powershell
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000). Check [http://localhost:8000/health](http://localhost:8000/health) for a health response. To stop the container, press `Ctrl+C`.

Alternatively, build and run the image directly:

```powershell
docker build -t task-tracker .
docker run --rm -p 8000:8000 task-tracker
```

## Run locally and test

Requires Python 3.10 or newer; no third-party packages are needed.

```powershell
python app.py
python -m unittest discover -s tests -v
```

## API

- `GET /health` — process health check
- `GET /api/tasks` — list tasks
- `POST /api/tasks` — create a task with `{"title":"..."}` (1–200 characters)
- `PATCH /api/tasks/{id}` — update `title` and/or boolean `done`
- `DELETE /api/tasks/{id}` — delete a task

## Version workflow

- **V1 (current):** keep this working task tracker as the clean baseline.
- **V2 (later, when requested):** introduce one intentional bug in its own commit; don't add bugs to V1.
- **V3 and onward:** continue with the next agreed exercise as a separate version/commit, recording how to reproduce and resolve it.

The project [Buggy App Lab skill](.github/skills/buggy-app-lab/SKILL.md) is a guide for those future exercises. For now, just run and use the clean app.
