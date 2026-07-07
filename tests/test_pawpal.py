"""Quick tests for PawPal+ core behaviors.

Covers the basics (task completion, adding tasks) plus the "smarter
scheduling" features: sorting by time, filtering, recurring tasks, and
conflict detection. Each test targets one behavior and includes a happy
path plus at least one edge case.
"""

from datetime import date, time, timedelta

from pawpal_system import (
    HIGH,
    LOW,
    MEDIUM,
    Owner,
    Pet,
    Scheduler,
    Task,
)


# --- Basics (from the starter) ----------------------------------------------

def test_task_completion():
    """Marking a task complete should flip its status from False to True."""
    task = Task("Morning walk", duration_min=30)
    assert task.completed is False

    task.mark_done()

    assert task.completed is True


def test_adding_task_increases_count():
    """Adding a task to a Pet should increase that pet's task count by one."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", duration_min=10))

    assert len(pet.tasks) == 1


# --- Sorting correctness -----------------------------------------------------

def test_sort_by_time_orders_chronologically():
    """sort_by_time() returns fixed-time tasks earliest-first."""
    early = Task("Meds", 5, fixed_time=time(7, 30))
    mid = Task("Walk", 30, fixed_time=time(9, 0))
    late = Task("Dinner", 10, fixed_time=time(18, 0))

    # Hand the tasks in out of order on purpose.
    ordered = Scheduler.sort_by_time([late, early, mid])

    assert [t.description for t in ordered] == ["Meds", "Walk", "Dinner"]


def test_sort_by_time_puts_floating_tasks_last():
    """Tasks without a fixed_time should sort after all timed tasks."""
    floating = Task("Grooming", 40)  # no fixed_time
    timed = Task("Feeding", 10, fixed_time=time(8, 0))

    ordered = Scheduler.sort_by_time([floating, timed])

    assert ordered[0].description == "Feeding"
    assert ordered[1].description == "Grooming"


def test_sort_by_time_empty_list():
    """Edge case: sorting an empty list returns an empty list, no crash."""
    assert Scheduler.sort_by_time([]) == []


# --- Filtering ---------------------------------------------------------------

def _owner_with_two_pets():
    """Build a small owner/pets/tasks fixture used by several tests."""
    owner = Owner("Sam", available_minutes=120)
    biscuit = owner.add_pet(Pet("Biscuit", "Dog"))
    mango = owner.add_pet(Pet("Mango", "Cat"))

    biscuit.add_task(Task("Walk", 30, category="walk"))
    biscuit.add_task(Task("Meds", 5, category="med", completed=True))
    mango.add_task(Task("Feeding", 10, category="feed"))
    return owner, biscuit, mango


def test_filter_by_pet_name_is_case_insensitive():
    """filter_tasks() should return only the named pet's tasks."""
    owner, _biscuit, _mango = _owner_with_two_pets()

    results = Scheduler.filter_tasks(owner, pet_name="biscuit")

    assert len(results) == 2
    assert all(pet.name == "Biscuit" for pet, _task in results)


def test_filter_by_completion_status():
    """filter_tasks(completed=False) should exclude done tasks."""
    owner, _biscuit, _mango = _owner_with_two_pets()

    pending = Scheduler.filter_tasks(owner, completed=False)

    assert len(pending) == 2  # the completed "Meds" task is excluded
    assert all(not task.completed for _pet, task in pending)


# --- Recurrence logic --------------------------------------------------------

def test_completing_daily_task_creates_next_day_instance():
    """Marking a daily task complete should queue a fresh task for +1 day."""
    pet = Pet("Biscuit", "Dog")
    task = pet.add_task(
        Task("Morning walk", 30, frequency="daily", due_date=date(2026, 7, 7))
    )
    scheduler = Scheduler()

    follow_up = scheduler.complete_task(pet, task)

    # Original is done; a new instance now exists on the pet.
    assert task.completed is True
    assert len(pet.tasks) == 2
    assert follow_up is not None
    assert follow_up.completed is False
    assert follow_up.due_date == date(2026, 7, 8)


def test_completing_weekly_task_advances_seven_days():
    """A weekly task's next occurrence should be 7 days out."""
    pet = Pet("Mango", "Cat")
    task = pet.add_task(
        Task("Nail trim", 15, frequency="weekly", due_date=date(2026, 7, 7))
    )

    follow_up = Scheduler().complete_task(pet, task)

    assert follow_up.due_date == date(2026, 7, 7) + timedelta(days=7)


def test_recurrence_handles_month_rollover():
    """Edge case: +1 day across a month boundary rolls the month correctly."""
    task = Task("Feeding", 10, frequency="daily", due_date=date(2026, 7, 31))

    follow_up = task.next_occurrence()

    assert follow_up.due_date == date(2026, 8, 1)


def test_one_off_task_has_no_next_occurrence():
    """A non-recurring task should not spawn a follow-up when completed."""
    pet = Pet("Biscuit", "Dog")
    task = pet.add_task(Task("Vet visit", 60, frequency="once"))

    follow_up = Scheduler().complete_task(pet, task)

    assert follow_up is None
    assert len(pet.tasks) == 1  # nothing new was added


# --- Conflict detection ------------------------------------------------------

def test_detect_conflicts_flags_same_time_across_pets():
    """Two pets with a task at the exact same fixed time should be flagged."""
    owner = Owner("Sam", available_minutes=120)
    biscuit = owner.add_pet(Pet("Biscuit", "Dog"))
    mango = owner.add_pet(Pet("Mango", "Cat"))
    biscuit.add_task(Task("Meds", 5, fixed_time=time(9, 0)))
    mango.add_task(Task("Feeding", 10, fixed_time=time(9, 0)))

    warnings = Scheduler.detect_conflicts(owner)

    assert len(warnings) == 1
    assert "09:00" in warnings[0]


def test_detect_conflicts_flags_same_pet_double_booked():
    """A single pet with two tasks at the same time should be flagged."""
    owner = Owner("Sam", available_minutes=120)
    biscuit = owner.add_pet(Pet("Biscuit", "Dog"))
    biscuit.add_task(Task("Walk", 30, fixed_time=time(8, 0)))
    biscuit.add_task(Task("Meds", 5, fixed_time=time(8, 0)))

    warnings = Scheduler.detect_conflicts(owner)

    assert len(warnings) == 1
    assert "Biscuit" in warnings[0]


def test_no_conflicts_returns_empty_list():
    """Distinct times (and a pet with no tasks) should yield no warnings."""
    owner = Owner("Sam", available_minutes=120)
    biscuit = owner.add_pet(Pet("Biscuit", "Dog"))
    owner.add_pet(Pet("Mango", "Cat"))  # a pet with no tasks at all
    biscuit.add_task(Task("Walk", 30, fixed_time=time(8, 0)))
    biscuit.add_task(Task("Dinner", 10, fixed_time=time(18, 0)))

    assert Scheduler.detect_conflicts(owner) == []


def test_completed_tasks_are_ignored_for_conflicts():
    """A done task at the same time should not raise a conflict warning."""
    owner = Owner("Sam", available_minutes=120)
    biscuit = owner.add_pet(Pet("Biscuit", "Dog"))
    biscuit.add_task(Task("Walk", 30, fixed_time=time(8, 0), completed=True))
    biscuit.add_task(Task("Meds", 5, fixed_time=time(8, 0)))

    assert Scheduler.detect_conflicts(owner) == []
