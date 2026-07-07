"""PawPal+ core system.

Four classes, mirroring diagrams/uml.mmd:

  Task      - a single care activity (description, time, frequency, done status)
  Pet       - pet details plus its own list of tasks
  Owner     - manages multiple pets and exposes all their tasks
  Scheduler - the "brain": retrieves, organizes, and orders tasks across pets

Design decisions (these fix the bottlenecks found during review):
  * Tasks belong to a Pet; the Owner aggregates them across pets via all_tasks().
  * The plan carries real clock times, not just an order.
  * Remaining time is tracked as tasks are placed, so the day can't be overbooked.
  * build_plan() computes the plan once; explain_plan() only formats it.
  * Fixed-time tasks are placed first and are never dropped for a floating task.
"""

from __future__ import annotations

from datetime import time


# Priority is an int so tasks sort naturally: 1 = high, 2 = medium, 3 = low.
HIGH, MEDIUM, LOW = 1, 2, 3
_PRIORITY_NAME = {HIGH: "high", MEDIUM: "medium", LOW: "low"}


def _to_minutes(t: time) -> int:
    """Convert a clock time to minutes since midnight."""
    return t.hour * 60 + t.minute


def _to_time(minutes: int) -> time:
    """Convert minutes since midnight back to a clock time (clamped to 23:59)."""
    minutes = max(0, min(minutes, 23 * 60 + 59))
    return time(minutes // 60, minutes % 60)


class Task:
    """A single pet care activity (walk, feeding, meds, enrichment, etc.)."""

    def __init__(
        self,
        description: str,
        duration_min: int,
        priority: int = MEDIUM,
        category: str = "general",
        frequency: str = "daily",
        fixed_time: time | None = None,
        completed: bool = False,
    ) -> None:
        """Create a care task with its duration, priority, and scheduling info."""
        self.description = description
        self.duration_min = duration_min
        self.priority = priority          # 1 = high, 2 = medium, 3 = low
        self.category = category          # e.g. "walk", "feed", "med"
        self.frequency = frequency        # e.g. "daily", "weekly"
        self.fixed_time = fixed_time      # None if the task can float
        self.completed = completed

    def is_fixed(self) -> bool:
        """Return True if this task must happen at a specific clock time."""
        return self.fixed_time is not None

    def mark_done(self) -> None:
        """Mark this task complete so the scheduler skips it."""
        self.completed = True

    def reset(self) -> None:
        """Mark this task incomplete again (e.g. at the start of a new day)."""
        self.completed = False

    def label(self) -> str:
        """One-line description, e.g. 'Morning walk (30 min) [high]'."""
        priority = _PRIORITY_NAME.get(self.priority, str(self.priority))
        return f"{self.description} ({self.duration_min} min) [{priority}]"

    def __repr__(self) -> str:
        """Developer-friendly representation of the task."""
        return f"Task({self.description!r}, {self.duration_min}min, p{self.priority})"


class Pet:
    """A pet and the set of care tasks that belong to it."""

    def __init__(self, name: str, species: str, breed: str = "") -> None:
        """Create a pet with its details and an empty task list."""
        self.name = name
        self.species = species
        self.breed = breed
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> Task:
        """Attach a care task to this pet and return it."""
        self.tasks.append(task)
        return task

    def pending_tasks(self) -> list[Task]:
        """Tasks that still need doing today (not yet completed)."""
        return [t for t in self.tasks if not t.completed]

    def summary(self) -> str:
        """Short description, e.g. 'Biscuit (Golden Retriever)'."""
        detail = self.breed or self.species
        return f"{self.name} ({detail})"

    def __repr__(self) -> str:
        """Developer-friendly representation of the pet."""
        return f"Pet({self.name!r}, {self.species!r}, tasks={len(self.tasks)})"


class Owner:
    """The pet owner: manages multiple pets and their combined task list."""

    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferences: dict | None = None,
    ) -> None:
        """Create an owner with a daily time budget, preferences, and no pets yet."""
        self.name = name
        self.available_minutes = available_minutes
        # preferences default to {} (avoids the mutable-default-argument bug).
        self.preferences = preferences if preferences is not None else {}
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> Pet:
        """Register a pet with this owner and return it."""
        self.pets.append(pet)
        return pet

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Every task across every pet, paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Every not-yet-completed task across all pets, paired with its pet."""
        return [(pet, task) for pet, task in self.all_tasks() if not task.completed]

    def allows(self, task: Task) -> bool:
        """Return True if the owner's preferences permit this task.

        Supported preference keys (all optional):
          * "no_earlier_than": time  - fixed tasks must not start before this.
          * "excluded_categories": set/list[str] - categories to skip entirely.
        """
        excluded = self.preferences.get("excluded_categories", ())
        if task.category in excluded:
            return False

        earliest = self.preferences.get("no_earlier_than")
        if earliest is not None and task.is_fixed() and task.fixed_time < earliest:
            return False

        return True

    def __repr__(self) -> str:
        """Developer-friendly representation of the owner."""
        return f"Owner({self.name!r}, {self.available_minutes}min, pets={len(self.pets)})"


class Scheduler:
    """Builds a daily plan from an owner's constraints and their pets' tasks."""

    def __init__(self, constraints: dict | None = None) -> None:
        """Create a scheduler with optional global constraints."""
        self.constraints = constraints if constraints is not None else {}

    def build_plan(self, owner: Owner, day_start: time = time(8, 0)) -> dict:
        """Choose, order, and time-stamp tasks for the day.

        Strategy:
          1. Consider only pending tasks the owner's preferences allow.
          2. Place FIXED-time tasks first (sorted by their time) so they are
             never bumped by a floating task.
          3. Fill remaining time with FLOATING tasks in priority order
             (highest priority first, shorter tasks breaking ties).
          4. Stop adding tasks once the owner's available minutes run out;
             everything that doesn't fit is recorded as skipped, with a reason.

        Returns a dict:
          {
            "scheduled": [ {"start": time, "pet": str, "task": Task}, ... ],
            "skipped":   [ {"pet": str, "task": Task, "reason": str}, ... ],
            "used_minutes": int,
            "available_minutes": int,
          }
        The scheduled list is ordered by start time.
        """
        remaining = owner.available_minutes
        scheduled: list[dict] = []
        skipped: list[dict] = []

        candidates = owner.pending_tasks()

        # Drop anything the owner's preferences disallow, up front.
        allowed: list[tuple[Pet, Task]] = []
        for pet, task in candidates:
            if owner.allows(task):
                allowed.append((pet, task))
            else:
                skipped.append(
                    {"pet": pet.name, "task": task, "reason": "not allowed by owner preferences"}
                )

        fixed = [(p, t) for p, t in allowed if t.is_fixed()]
        floating = [(p, t) for p, t in allowed if not t.is_fixed()]

        # 1) Fixed tasks: earliest first, anchored at their own clock time.
        fixed.sort(key=lambda pt: pt[1].fixed_time)
        for pet, task in fixed:
            if task.duration_min <= remaining:
                scheduled.append({"start": task.fixed_time, "pet": pet.name, "task": task})
                remaining -= task.duration_min
            else:
                skipped.append(
                    {"pet": pet.name, "task": task, "reason": "not enough time left in the day"}
                )

        # 2) Floating tasks: highest priority first, shorter tasks break ties.
        floating.sort(key=lambda pt: (pt[1].priority, pt[1].duration_min))

        # Lay floating tasks back-to-back starting at day_start.
        cursor = _to_minutes(day_start)
        for pet, task in floating:
            if task.duration_min <= remaining:
                scheduled.append({"start": _to_time(cursor), "pet": pet.name, "task": task})
                cursor += task.duration_min
                remaining -= task.duration_min
            else:
                skipped.append(
                    {"pet": pet.name, "task": task, "reason": "not enough time left in the day"}
                )

        scheduled.sort(key=lambda item: item["start"])

        return {
            "scheduled": scheduled,
            "skipped": skipped,
            "used_minutes": owner.available_minutes - remaining,
            "available_minutes": owner.available_minutes,
        }

    def explain_plan(self, plan: dict) -> str:
        """Turn a plan (from build_plan) into a human-readable explanation.

        This only formats the plan it is given, so the explanation can never
        disagree with the schedule that was actually built.
        """
        lines: list[str] = []
        scheduled = plan["scheduled"]
        skipped = plan["skipped"]

        if not scheduled:
            lines.append("No tasks could be scheduled today.")
        else:
            lines.append("Daily plan:")
            for item in scheduled:
                task: Task = item["task"]
                start: time = item["start"]
                anchor = "fixed" if task.is_fixed() else "priority-ordered"
                lines.append(
                    f"  {start.strftime('%H:%M')} — {item['pet']}: {task.label()} ({anchor})"
                )

        lines.append("")
        lines.append(
            f"Used {plan['used_minutes']} of {plan['available_minutes']} available minutes."
        )

        if skipped:
            lines.append("")
            lines.append("Skipped:")
            for item in skipped:
                task = item["task"]
                lines.append(f"  {item['pet']}: {task.label()} — {item['reason']}")

        return "\n".join(lines)


if __name__ == "__main__":
    # Quick demo so you can see the output shape without the Streamlit UI.
    owner = Owner("Sam", available_minutes=90, preferences={"no_earlier_than": time(7, 0)})
    biscuit = owner.add_pet(Pet("Biscuit", "Dog", "Golden Retriever"))

    biscuit.add_task(Task("Morning walk", 30, priority=HIGH, category="walk"))
    biscuit.add_task(Task("Feeding", 10, priority=HIGH, category="feed", fixed_time=time(9, 0)))
    biscuit.add_task(Task("Heart meds", 5, priority=HIGH, category="med", fixed_time=time(8, 0)))
    biscuit.add_task(Task("Enrichment puzzle", 20, priority=MEDIUM, category="enrichment"))
    biscuit.add_task(Task("Grooming", 40, priority=LOW, category="grooming"))

    scheduler = Scheduler()
    plan = scheduler.build_plan(owner)
    print(scheduler.explain_plan(plan))
