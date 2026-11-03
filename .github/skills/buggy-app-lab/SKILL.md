---
name: buggy-app-lab
description: "Use when adding, diagnosing, fixing, or rolling back intentionally introduced bugs in the Docker task-tracker lab. Keep each bug isolated to a commit and record its symptom, cause, and verified resolution."
---

# Buggy App Lab

Use this workflow for deliberate bug-injection exercises in this repository. The app is a small task tracker with a JSON API and an in-memory store; its data resets when the process restarts.

## Baseline and Docker

- Start the baseline with `docker compose up --build`; open `http://localhost:8000`.
- Check `http://localhost:8000/health` for `{"status":"ok"}`.
- Run the regression suite with `python -m unittest discover -s tests -v`.
- Confirm the baseline tests pass before introducing a fault. Keep the clean baseline commit available so a bad exercise can be reverted safely.

## Introducing a bug

1. Agree on a user-visible symptom or failing test before changing code.
2. Introduce one focused fault per commit. Vary the fault between exercises instead of repeating the same parameter change.
3. Keep the intended symptom reproducible, and avoid changing the Docker setup unless the exercise is specifically about container configuration.
4. Record the commit, changed behavior, reproduction steps, and expected behavior in the exercise notes or commit message. Do not include the fix in the bug-introduction commit.
5. Rebuild/restart the container after code changes: `docker compose up --build`. Run tests to capture the failure and distinguish it from environment or startup issues.

## Diagnosing and resolving

1. Reproduce the reported symptom in the container and run the relevant tests.
2. Compare the failing commit with the last known-good commit. Inspect recent changes and configuration before assuming the cause.
3. Identify the smallest root-cause change; verify whether the fault is in application logic, an input/parameter value, environment configuration, or container wiring.
4. Fix and test the behavior. Prefer correcting the responsible parameter/configuration when that is the cause; otherwise repair the code. Do not mask errors with fallback behavior.
5. If the change is not recoverable or the exercise is to practice rollback, revert only the offending commit with `git revert <commit>` (or restore the affected change from the known-good revision in a new commit). Do not rewrite shared history.
6. Rebuild and rerun the tests plus the original reproduction. Record the root cause, the exact resolution (including any changed parameter or rollback reference), and the verification result.

## Common exercise patterns

| Fault area | Example symptom | Typical resolution |
|---|---|---|
| Request validation | Valid task title or completion update is rejected | Correct the validation condition or accepted field/value; add a regression test |
| API behavior | Create, update, list, or delete returns an unexpected status or payload | Restore the endpoint contract and test the full task lifecycle |
| State handling | Tasks disappear or updates affect the wrong task | Correct ID/state handling; add a test covering multiple tasks |
| UI/API integration | Form submission, completion toggle, or delete action does not work | Align the request method, URL, headers, and JSON shape with the API |
| Runtime configuration | App listens on the wrong port or fails to start in the container | Correct the `PORT` value, bind address, or matching Docker port mapping |
| Container packaging | Page/assets or app module are missing in the image | Correct the Docker `COPY` path or build context, then rebuild the image |

These are exercise ideas, not a diagnosis. Confirm the observed failure before choosing a fix. Change configuration only when evidence points to configuration, and use rollback when reverting is the intended safe recovery.
