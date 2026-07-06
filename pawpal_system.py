"""PawPal+ core system — class skeletons.

Generated from diagrams/uml.mmd. This is a *skeleton* only: attributes are set up
in the constructors, but the methods contain no scheduling logic yet.

Workflow:
  1. Fill in each method where marked with TODO.
  2. Add tests for the scheduling behaviors.
  3. Wire these classes into the Streamlit UI in app.py.
"""

from datetime import time


class Task:
    """A single pet care activity (walk, feeding, meds, enrichment, etc.)."""

    def __init__(
        self,
        name: str,
        duration_min: int,
        priority: int,
        category: str,
        fixed_time: time | None = None,
    ) -> None:
        self.name = name
        self.duration_min = duration_min
        self.priority = priority          # e.g. 1 = high, 2 = medium, 3 = low
        self.category = category          # e.g. "walk", "feed", "med"
        self.fixed_time = fixed_time      # None if the task can float

    def is_fixed(self) -> bool:
        """Return True if this task must happen at a specific time."""
        # TODO: return whether fixed_time is set
        raise NotImplementedError

    def label(self) -> str:
        """Return a human-readable one-line description of this task."""
        # TODO: build a string like "Morning walk (30 min) [priority: 1]"
        raise NotImplementedError


class Pet:
    """A pet that has a set of care tasks."""

    def __init__(self, name: str, species: str, breed: str) -> None:
        self.name = name
        self.species = species
        self.breed = breed
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        # TODO: append task to self.tasks
        raise NotImplementedError

    def summary(self) -> str:
        """Return a short description of the pet (e.g. 'Biscuit (Golden Retriever)')."""
        # TODO: build and return the summary string
        raise NotImplementedError


class Owner:
    """The pet owner, including their available time and preferences."""

    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferences: dict | None = None,
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences if preferences is not None else {}

    def has_time_for(self, task: Task) -> bool:
        """Return True if the owner has enough remaining time for the task."""
        # TODO: compare task.duration_min against available time
        raise NotImplementedError

    def allows(self, task: Task) -> bool:
        """Return True if the task is permitted by the owner's preferences."""
        # TODO: check task against self.preferences (e.g. no walks before 8am)
        raise NotImplementedError


class Scheduler:
    """Builds a daily plan from an owner's constraints and a pet's tasks."""

    def __init__(self, constraints: dict | None = None) -> None:
        self.constraints = constraints if constraints is not None else {}

    def build_plan(self, owner: Owner, tasks: list[Task]) -> list[Task]:
        """Choose and order tasks for the day based on constraints and priorities.

        Returns the ordered list of tasks that made it into the plan.
        """
        # TODO: select/order tasks (e.g. greedy by priority, respecting owner's time)
        raise NotImplementedError

    def explain_plan(self, owner: Owner, tasks: list[Task]) -> str:
        """Return a human-readable explanation of why the plan looks the way it does."""
        # TODO: describe which tasks were chosen/skipped and why
        raise NotImplementedError
