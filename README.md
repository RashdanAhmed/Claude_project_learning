# GRC Task Desk

A day-to-day task list for governance, risk and compliance work.

Live page: https://claude.ai/artifact/He8zB2nNySD9ZLbnuKL2Xo (private to the owner until shared)

Source: [`grc-task-desk.html`](grc-task-desk.html), a single-file page published as a claude.ai Artifact. Tasks are kept in the artifact's database, so the list persists across devices when you open the page signed in.

## What it does

- **Triage strip**: overdue, due today, next 7 days, waiting on others, and check-ins done this week.
- **Views**: Focus (overdue, due today and in progress), Next 7 days, All open, Waiting, Recurring, Done.
- **Filters** by GRC area (RSK, CMP, AUD, POL, TPR, IAM, INC, TRN, BCM, GOV) and by framework, plus search across titles, notes, control references and owners.
- **Recurring tasks** (daily, weekly, monthly, quarterly, annual): ticking one logs the cycle and moves it to the next due date.
- **Routine library**: 26 standard GRC check-ins mapped to ISO/IEC 27001:2022, SOC 2, NIST CSF 2.0, PCI DSS v4.0 and GDPR references, added with one click.
- **Task fields**: area, priority, due date, cadence, framework, control reference, status, owner or stakeholder, evidence location and notes.

## Run it on your own machine

Use [`grc-task-desk-standalone.html`](grc-task-desk-standalone.html). It is one self-contained file with nothing to install.

1. Download `grc-task-desk-standalone.html` (on GitHub, open the file and click **Download raw file**).
2. Double-click it to open it in your browser. Bookmark it so you can come back to it.

Tasks are saved in that browser's local storage. Keep in mind:

- They stay on that computer, in that browser. The claude.ai page and the local copy don't share tasks.
- Clearing your browser's site data deletes them.
- If the page says **Not saved in this browser**, your browser is blocking storage for files opened from disk. Serve the folder with a local web server instead, then open http://localhost:8000/grc-task-desk-standalone.html:

  ```sh
  python3 -m http.server 8000
  ```

  Storage is tied to the address, so tasks saved at `file://…` don't appear at `localhost:8000`, and the reverse.

The page loads its fonts from Google Fonts. Offline, it falls back to your system fonts and works the same.

### Editing the page

`grc-task-desk.html` is the source published to claude.ai, which adds the `<html>`, `<head>` and `<body>` tags at publish time. After editing it, rebuild the standalone copy:

```sh
./build-standalone.sh
```
