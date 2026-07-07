"""Quick tests for PawPal+ core behaviors."""

from pawpal_system import Pet, Task


def test_task_completion():
    """Marking a task complete should flip its status from False to True."""
    task = Task("Morning walk", duration_min=30)
    assert task.completed is False

    task.mark_done()  # assignment calls this mark_complete()

    assert task.completed is True


def test_adding_task_increases_count():
    """Adding a task to a Pet should increase that pet's task count by one."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", duration_min=10))

    assert len(pet.tasks) == 1
