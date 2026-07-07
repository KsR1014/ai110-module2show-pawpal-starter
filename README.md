# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Today's Schedule for Sam
Pets: Biscuit (Golden Retriever), Mango (Tabby)
========================================
Daily plan:
  08:00 — Biscuit: Heart meds (5 min) [high] (fixed)
  08:00 — Biscuit: Morning walk (30 min) [high] (priority-ordered)
  08:30 — Mango: Litter change (15 min) [medium] (priority-ordered)
  08:45 — Biscuit: Grooming (40 min) [low] (priority-ordered)
  09:00 — Mango: Feeding (10 min) [high] (fixed)

Used 100 of 120 available minutes.

## 🧪 Testing PawPal+

Run the full automated test suite from the project root:

```bash
python -m pytest
```

**What the tests cover.** The suite in `tests/test_pawpal.py` has 15 tests spanning the core behaviors and their edge cases:

- Basics: marking a task complete and adding a task to a pet.
- Sorting (`Scheduler.sort_by_time`): tasks come back in chronological order, floating (no fixed-time) tasks sort last, and an empty list is handled safely.
- Filtering (`Scheduler.filter_tasks`): filter by pet name (case-insensitive) and by completion status.
- Recurrence (`Scheduler.complete_task` / `Task.next_occurrence`): completing a daily task creates a fresh instance due +1 day, weekly advances +7 days, month rollovers (Jul 31 → Aug 1) are correct, and one-off tasks spawn nothing.
- Conflict detection (`Scheduler.detect_conflicts`): flags two pets at the same time and a single pet double-booked, returns an empty list when times are distinct (including a pet with no tasks), and ignores already-completed tasks.

Successful test run:

```
========================== test session starts ===========================
platform darwin -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/kushalrajam/AI110 Class Work/ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 15 items                                                       

tests/test_pawpal.py ...............                               [100%]

=========================== 15 passed in 0.02s =========================== 
```

**Confidence Level: ⭐️⭐️⭐️⭐️☆ (4/5)**

All 15 tests pass and they cover every "smarter scheduling" feature along with its main edge cases (empty inputs, same-time conflicts, completed-task handling, and date rollovers), so I'm confident the core logic is reliable. I held back the fifth star because the tests don't yet cover overlapping-duration conflicts (only exact time matches), owner-preference filtering, or the full `build_plan` time-budget path under stress — those are the areas I'd test next to reach 5/5.

## 📐 Smarter Scheduling

Beyond building a basic daily plan, PawPal+ adds four "smarter scheduling" behaviors. Each is implemented as a method on the `Scheduler` class in `pawpal_system.py` (recurring tasks also use a helper on `Task`).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time()` | Orders tasks chronologically; floating tasks fall last |
| Filtering | `Scheduler.filter_tasks()` | Filter by pet name and/or completion status |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns on tasks sharing the same fixed time |
| Recurring tasks | `Scheduler.complete_task()`, `Task.next_occurrence()` | Auto-creates the next daily/weekly instance |

### Sorting behavior — `Scheduler.sort_by_time()`

Returns a list of tasks ordered by their fixed clock time, earliest first. It uses `sorted()` with a lambda key built as a tuple, `(t.fixed_time is None, t.fixed_time or time(0, 0))`, so time-locked tasks sort chronologically while floating tasks (which have no `fixed_time` and can't be compared to a real time) are pushed to the end instead of raising an error.

### Filtering behavior — `Scheduler.filter_tasks()`

Returns `(pet, task)` pairs filtered by **pet name**, **completion status**, or both. Each filter is optional (`None` means "don't filter on it"), so `filter_tasks(owner, pet_name="Biscuit", completed=False)` returns just Biscuit's outstanding tasks. Pet-name matching is case-insensitive.

### Conflict detection logic — `Scheduler.detect_conflicts()`

A lightweight pairwise scan over pending, fixed-time tasks. When two tasks share the same `fixed_time`, it appends a human-readable warning string (distinguishing a single pet with two clashing tasks from two different pets clashing). It **returns a list of warnings** rather than raising, so an empty list simply means "no conflicts" and the program never crashes. Tradeoff: it matches exact start times only and does not yet detect duration overlaps.

### Recurring task logic — `Scheduler.complete_task()` + `Task.next_occurrence()`

Completing a task goes through `Scheduler.complete_task(pet, task)`, which marks the task done and then asks `Task.next_occurrence()` for a follow-up. For a `"daily"` or `"weekly"` task, `next_occurrence()` returns a fresh, uncompleted copy whose `due_date` is advanced with `timedelta(days=1)` or `timedelta(days=7)` (so month/year rollovers are handled correctly); the new instance is automatically attached to the pet. One-off tasks return `None` and nothing is added.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
