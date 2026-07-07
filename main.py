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

    # 3. Add at least three tasks, with different times/durations, to the pets.
    biscuit.add_task(Task("Heart meds", 5, priority=HIGH, category="med", fixed_time=time(8, 0)))
    biscuit.add_task(Task("Morning walk", 30, priority=HIGH, category="walk"))
    biscuit.add_task(Task("Grooming", 40, priority=LOW, category="grooming"))

    mango.add_task(Task("Feeding", 10, priority=HIGH, category="feed", fixed_time=time(9, 0)))
    mango.add_task(Task("Litter change", 15, priority=MEDIUM, category="clean"))

    # 4. Build and print today's schedule.
    scheduler = Scheduler()
    plan = scheduler.build_plan(owner, day_start=time(8, 0))

    print("=" * 40)
    print(f"Today's Schedule for {owner.name}")
    print(f"Pets: {', '.join(pet.summary() for pet in owner.pets)}")
    print("=" * 40)
    print(scheduler.explain_plan(plan))


if __name__ == "__main__":
    main()
