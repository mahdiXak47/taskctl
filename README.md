# taskctl

A minimal, fast task manager that lives in your terminal. Track what you are working on, set deadlines, add comments, and review your history — all without leaving the shell.

---

## Installation

**Requirements:** Python 3.10+

```bash
git clone <repo-url>
cd taskctl
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Then make it available system-wide:

```bash
sudo ln -sf "$(pwd)/.venv/bin/taskctl" /usr/local/bin/taskctl
```

Verify:

```bash
taskctl --help
```

All data is stored in `~/.taskctl/taskctl.db` (SQLite).

---

## Task statuses

| Status | Meaning |
|---|---|
| `not_started` | Task created but not yet started |
| `in_progress` | Task is actively being worked on |
| `breached_deadline` | ETA has passed but task is not done |
| `done_intime` | Completed before or at the deadline |
| `done_but_breached` | Completed after the deadline |

---

## Commands

### `taskctl create` — Create a new task

Launches an interactive prompt for any field you do not supply via flags.

<details>
<summary>Arguments</summary>

| Flag | Short | Description |
|---|---|---|
| `--title` | `-t` | Task title |
| `--description` | `-d` | Short description |
| `--eta` | `-e` | Estimated time to finish (e.g. `30m`, `2h`, `3d`) |
| `--start` | `-s` | Start the task immediately after creating it |

**ETA units:** `m` = minutes, `h` = hours, `d` = days. Range: `5m` to `7d`.

</details>

<details>
<summary>Examples</summary>

Fully interactive:
```bash
taskctl create
```

With all flags (no prompts):
```bash
taskctl create -t "Write report" -d "Q1 sales report" -e 2h -s
```

Create and start immediately:
```bash
taskctl create -t "Fix login bug" -e 45m --start
```

</details>

---

### `taskctl list` — List tasks

Shows tasks created within a time window. Defaults to today.

<details>
<summary>Arguments</summary>

| Flag | Short | Description |
|---|---|---|
| `--duration` | `-d` | How far back to look (e.g. `7d`, `24h`). Default: today only |
| `--status` | `-s` | Filter by status (see status table above) |
| `--verbose` | `-v` | Add an **Event** column showing the last action on each task |

</details>

<details>
<summary>Examples</summary>

List today's tasks:
```bash
taskctl list
```

List tasks from the past week:
```bash
taskctl list -d 7d
```

Show only in-progress tasks from the past 2 days:
```bash
taskctl list -d 2d -s in_progress
```

Show last event per task:
```bash
taskctl list -v
```

Combine all flags:
```bash
taskctl list -d 7d -s done_intime -v
```

</details>

---

### `taskctl start <task_id>` — Start a task

Moves a `not_started` task into `in_progress` and begins the ETA countdown.

<details>
<summary>Arguments</summary>

| Argument | Description |
|---|---|
| `task_id` | The 8-character ID shown when the task was created |

</details>

<details>
<summary>Examples</summary>

```bash
taskctl start 53270e98
```

**If the task is already started:**
```
what was you doing until now? the task is already started at today 09:15
```

**If the task ID does not exist:**
```
what task do you mean?
i do not find any task with id 53270e98
```

</details>

---

### `taskctl done <task_id>` — Mark a task as done

Closes the task. The resulting status depends on whether you finished before or after the deadline.

<details>
<summary>Arguments</summary>

| Argument | Description |
|---|---|
| `task_id` | The 8-character task ID |

</details>

<details>
<summary>Examples</summary>

```bash
taskctl done 53270e98
```

Finished on time:
```
Great, you have done the task in the estimated time!
```

Finished late:
```
Not bad, you done the task after all. Estimate better next time or work harder!
```

</details>

---

### `taskctl describe <task_id>` — Show full task details

Displays the task name, current status, time remaining, and the last 5 comments.

<details>
<summary>Arguments</summary>

| Argument / Flag | Short | Description |
|---|---|---|
| `task_id` | | The 8-character task ID |
| `--verbose` | `-v` | Show **all** comments instead of just the last 5 |

</details>

<details>
<summary>Examples</summary>

```bash
taskctl describe 53270e98
```

```
Write report [in_progress]
Time remaining: 1h 42m

  [today 09:20] added intro section
  [32 minutes ago] finished charts
```

Show all comments:
```bash
taskctl describe 53270e98 -v
```

</details>

---

### `taskctl comment <task_id> -m <message>` — Add a comment to a task

Attaches a timestamped note to any task. Visible in `taskctl describe`.

<details>
<summary>Arguments</summary>

| Argument / Flag | Short | Required | Description |
|---|---|---|---|
| `task_id` | | yes | The 8-character task ID |
| `--message` | `-m` | yes | The comment text |

</details>

<details>
<summary>Examples</summary>

```bash
taskctl comment 53270e98 -m "Blocked on design review"
taskctl comment 53270e98 -m "Unblocked, resuming now"
```

</details>

---

### `taskctl delete <task_id>` — Delete a task

Permanently removes a task and all its comments and events from the database.

> If the task is currently `in_progress`, you will be asked to confirm before deletion.

<details>
<summary>Arguments</summary>

| Argument | Description |
|---|---|
| `task_id` | The 8-character task ID |

</details>

<details>
<summary>Examples</summary>

```bash
taskctl delete 53270e98
```

If in progress:
```
Task 'Write report' is currently in progress.
Are you sure you want to delete it? (y/N):
```

</details>

---

### `taskctl serve` — Start the web UI

Launches a local FastAPI server at `http://localhost:8000` that serves the web interface.

<details>
<summary>Examples</summary>

```bash
taskctl serve
```

```
Starting taskctl web server at http://localhost:8000
```

The server requires a registered account. Use the web UI to register and log in.

</details>

---

## Time format reference

Timestamps are displayed in a human-friendly format:

| When the event happened | Display |
|---|---|
| Less than 60 minutes ago | `3 minutes ago` |
| 1 to 12 hours ago | `2 hours ago` |
| Earlier today (more than 12h ago) | `today 08:30` |
| Yesterday | `yesterday 14:15` |
| Due today (future) | `today 23:59` |
| Due tomorrow (future) | `tomorrow 10:00` |
| Older / further | `2026/04/10-09:00` |

---

## Data storage

Everything is stored in a single SQLite database at `~/.taskctl/taskctl.db`.

| Table | Contents |
|---|---|
| `tasks` | All task records |
| `comments` | Comments attached to tasks |
| `events` | Audit log of every action (create, start, done, comment, delete) |
| `users` | Registered accounts (used by the web UI) |
