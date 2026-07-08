# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design centered on four classes, chosen to separate the data about the pet-care situation from the logic that reasons about it.

Owner
- represents the pet owner and, importantly, the constraints the scheduler has to respect available_minutes and a preferences dictionary
- its methods (has_time_for(), allows()) answer whether a given task fits the owner's time and preferences

Pet
— holds basic info (name, species, breed) and owns the list of care tasks
- responsible for managing its own tasks via add_task() and describing itself with summary()

Task
— represents one care activity with duration_min, priority, category, and an optional fixed_time (for things like meds that must happen at a set time)
- responsible for describing itself (label()) and reporting whether it's time-locked (is_fixed())

Scheduler
— the "brains" of the system
- it reads the owner's constraints and the list of tasks and produces the daily plan (build_plan()) plus an explanation of its choices (explain_plan())

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, my design changed while implementing. One change I made was that I gave a "has a" relationship between a Pet and a Task instead of between a Owner and Task. I did this because Tasks logically belong to a pet (a walk is Biscuit's walk).

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler weighs three constraints: the owner's daily time budget (`available_minutes`), each task's priority (high/medium/low) and duration, and the owner's preferences (a `no_earlier_than` time and any `excluded_categories`). It also respects whether a task is time-locked: tasks with a `fixed_time` (like meds or a vet appointment) must happen at their set clock time, while "floating" tasks can be slotted wherever there's room. In `build_plan()`, I place fixed-time tasks first so they're never bumped, then fill the leftover minutes with floating tasks in priority order (highest priority first, shorter tasks breaking ties), and anything that no longer fits is recorded as "skipped" with a reason instead of silently dropped.

I decided the time budget mattered most because it's the hard limit a real pet owner can't exceed — no amount of good intentions creates more minutes in the day. Fixed times came next, since a medication at 8:00 is non-negotiable in a way a walk isn't, followed by priority and preferences to decide how to spend whatever time remains.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

My scheduler's conflict detection only flags tasks that start at the *exact same* fixed time — it does a simple pairwise scan comparing `fixed_time == fixed_time` and returns a warning string rather than crashing. The tradeoff is that it ignores task *durations*, so it misses overlaps: a 30-minute walk starting at 9:00 and a feeding at 9:15 don't collide by start time, but they clearly overlap in real life, and my code stays silent. I chose exact-match detection because it is lightweight, easy to reason about, and never raises, which fit the scope of this phase and keeps the warning output simple for a pet owner to read. If I extended it, I'd compare time intervals (start plus `duration_min`) instead of just start times to catch true overlaps, at the cost of more complex logic.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used an AI assistant throughout the build: sketching the class structure (Task/Pet/Owner/Scheduler) before writing code, generating first-pass implementations of methods like `build_plan()` and `detect_conflicts()`, and wiring the Streamlit UI to the backend. 

The most useful prompts were narrow and behavioral rather than open-ended ones. For example, "fixed-time tasks should never be dropped in favor of a floating task, even if the floating task has higher priority" got a much better result than "write a scheduler." 

In addition, asking the AI to explain why it structured something a certain way (e.g. why `build_plan()` and `explain_plan()` are split into two methods) was useful for catching design smells early.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One moment I didn't accept the suggestion as-is: an early version of `Owner.__init__` used `preferences: dict = {}` as the default argument. The empty dict would be shared across every `Owner` created without explicit preferences, so changing one owner's preferences could silently leak into another owner. 

I asked for it to be rewritten to default to `None` and build a fresh dict inside the constructor instead (`self.preferences = preferences if preferences is not None else {}`).

I verified the fix by creating two `Owner` objects with no preferences passed in, changing one owner's preferences, and confirming the other owner's preferences stayed empty.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

1. Conflict detection: two tasks (same pet, and different pets) sharing the same `fixed_time` produce the expected warning strings, and no warning fires when times differ.
2. Schedule building under a tight time budget: confirmed fixed-time tasks are placed even if it means floating tasks get skipped, and that skipped tasks show up with a reason ("not enough time left in the day").
3. Priority ordering among floating tasks: verified that when two tasks tie on priority, the shorter one is scheduled first.
4. Recurring task rollover: completing a "daily" task creates a follow-up due the next day; completing a one-off task returns `None` and doesn't create anything.
5. Owner preferences (`no_earlier_than`, `excluded_categories`): confirmed disallowed tasks are filtered out and appear in the "skipped" list with the right reason.


**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm fairly confident in the core scheduling logic (fixed-time placement, priority ordering, time-budget accounting) since it's deterministic and I traced through it by hand against the `__main__` demo. I'm less confident about edge cases around dates and the Streamlit session state. If I had more time I'd test:
- What happens when `available_minutes` is 0 or negative.
- A recurring task whose `next_occurrence()` is generated but never completed again — does it pile up duplicates over multiple days?
- Two floating tasks with identical priority *and* identical duration (is the sort still stable/predictable?).
- Whether the Streamlit `session_state` owner object survives correctly across a full page refresh (not just a rerun).

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I think in general, I'm really happy that I was able to basically build an app

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd redesign how "today" is handled. Right now tasks don't really track which day they're due in a way the UI surfaces, and the recurring-task system stores a raw `due_date` that the frontend never displays. Given another iteration, I'd surface upcoming (not just today's) tasks, and let the user see a task's due date directly in the table.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important thing I learned is that AI-generated code tends to be locally correct but can hide global assumptions. Naming the invariant I actually cared about (e.g. "fixed tasks are never bumped") got much better results than describing the algorithm I imagined.
