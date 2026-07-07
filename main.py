"""PawPal+ demo script.

Builds a small owner/pets/tasks setup and prints today's schedule to the
terminal. Run with:  python main.py
"""

from datetime import time

from pawpal_system import HIGH, MEDIUM, LOW, Owner, Pet, Scheduler, Task


def main() -> None:
    # 1. Create an owner with a daily time budget and one preference.
    owner = Owner("Sam", available_minutes=120, preferences={"no_earlier_than": time(7, 0)})

    # 2. Create at least two pets and register them with the owner.
    biscuit = owner.add_pet(Pet("Biscuit", "Dog", "Golden Retriever"))
    mango = owner.add_pet(Pet("Mango", "Cat", "Tabby"))

    # 3. Add tasks OUT OF ORDER on purpose, so sorting has something to fix.
    #    Note the two 9:00 tasks below — that's a deliberate scheduling clash.
    biscuit.add_task(Task("Grooming", 40, priority=LOW, category="grooming"))
    biscuit.add_task(Task("Heart meds", 5, priority=HIGH, category="med", fixed_time=time(9, 0)))
    biscuit.add_task(Task("Morning walk", 30, priority=HIGH, category="walk", fixed_time=time(7, 30)))

    mango.add_task(Task("Feeding", 10, priority=HIGH, category="feed", fixed_time=time(9, 0)))
    mango.add_task(Task("Litter change", 15, priority=MEDIUM, category="clean"))

    scheduler = Scheduler()

    # 4. SORTING: pull every task and order it by clock time (floats go last).
    print("=" * 40)
    print("All tasks, sorted by time")
    print("=" * 40)
    all_tasks = [task for _pet, task in owner.all_tasks()]
    for task in scheduler.sort_by_time(all_tasks):
        when = task.fixed_time.strftime("%H:%M") if task.is_fixed() else "  —  "
        print(f"  {when}  {task.label()}")

    # 5. FILTERING: show just Biscuit's outstanding (not-yet-done) tasks.
    print("\n" + "=" * 40)
    print("Filter: Biscuit's pending tasks")
    print("=" * 40)
    for pet, task in scheduler.filter_tasks(owner, pet_name="Biscuit", completed=False):
        print(f"  {pet.name}: {task.label()}")

    # 6. CONFLICT DETECTION: two 9:00 tasks should raise a warning, not a crash.
    print("\n" + "=" * 40)
    print("Conflict check")
    print("=" * 40)
    conflicts = scheduler.detect_conflicts(owner)
    if conflicts:
        for warning in conflicts:
            print(warning)
    else:
        print("  No scheduling conflicts. 🎉")

    # 7. RECURRING TASKS: completing a daily task auto-creates the next one.
    print("\n" + "=" * 40)
    print("Recurring: complete the daily walk")
    print("=" * 40)
    walk = biscuit.tasks[2]  # the "Morning walk" added above
    before = len(biscuit.tasks)
    follow_up = scheduler.complete_task(biscuit, walk)
    after = len(biscuit.tasks)
    print(f"  Tasks before: {before}, after completing: {after}")
    if follow_up is not None:
        print(f"  Auto-created next '{follow_up.description}' due {follow_up.due_date}.")

    # 8. Build and print today's schedule.
    plan = scheduler.build_plan(owner, day_start=time(8, 0))
    print("\n" + "=" * 40)
    print(f"Today's Schedule for {owner.name}")
    print(f"Pets: {', '.join(pet.summary() for pet in owner.pets)}")
    print("=" * 40)
    print(scheduler.explain_plan(plan))


if __name__ == "__main__":
    main()
