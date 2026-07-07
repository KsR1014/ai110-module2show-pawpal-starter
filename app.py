import streamlit as st
from datetime import time

# --- Step 1: Establish the connection ---------------------------------------
# Bring the specific classes we need from our backend into the Streamlit app.
from pawpal_system import Owner, Pet, Task, Scheduler, HIGH, MEDIUM, LOW

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan your pets' daily care around the time you actually have.")

# Map the friendly UI labels to the integer priorities the backend uses.
PRIORITY_LABELS = {"high": HIGH, "medium": MEDIUM, "low": LOW}


# --- Step 2: Manage the application "memory" --------------------------------
# Streamlit reruns this whole script on every interaction. Without session_state
# the Owner would be re-created (empty) every rerun, losing all pets and tasks.
# So we create the Owner ONCE and keep the same object in the session "vault".
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=120)

# Grab the persisted owner. Mutating this object (adding pets/tasks) sticks,
# because it's the same object stored in session_state across reruns.
owner: Owner = st.session_state.owner


# --- Owner settings ----------------------------------------------------------
st.subheader("👤 Owner")
col_a, col_b = st.columns(2)
with col_a:
    owner.name = st.text_input("Owner name", value=owner.name)
with col_b:
    owner.available_minutes = st.number_input(
        "Time available today (minutes)",
        min_value=0,
        max_value=1440,
        value=owner.available_minutes,
        step=15,
    )

st.divider()


# --- Step 3: Wiring UI actions to logic -------------------------------------
# Add a pet. On submit we call Owner.add_pet(), which appends to owner.pets.
# Because the owner lives in session_state, the new pet persists; the script
# reruns after the button click and the pet list below shows the change.
st.subheader("🐶 Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    p_name = st.text_input("Pet name")
    p_species = st.selectbox("Species", ["dog", "cat", "other"])
    p_breed = st.text_input("Breed (optional)")
    add_pet_clicked = st.form_submit_button("Add pet")

if add_pet_clicked:
    if p_name.strip():
        owner.add_pet(Pet(p_name.strip(), p_species, p_breed.strip()))
        st.success(f"Added {p_name.strip()}!")
    else:
        st.error("Please enter a pet name.")


# --- Add a task to a pet -----------------------------------------------------
st.subheader("📋 Add a Task")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        # Choose which pet the task belongs to (tasks live on the pet).
        pet_names = [pet.name for pet in owner.pets]
        chosen_pet_name = st.selectbox("For which pet?", pet_names)

        t_desc = st.text_input("Task", value="Morning walk")
        c1, c2 = st.columns(2)
        with c1:
            t_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with c2:
            t_priority = st.selectbox("Priority", ["high", "medium", "low"])

        t_category = st.text_input("Category", value="general")

        # A task can optionally be pinned to a specific clock time.
        use_fixed = st.checkbox("This task happens at a fixed time")
        t_fixed_time = st.time_input("Fixed time", value=time(8, 0)) if use_fixed else None

        add_task_clicked = st.form_submit_button("Add task")

    if add_task_clicked:
        # Find the selected pet object, then call Pet.add_task() on it.
        pet = next(p for p in owner.pets if p.name == chosen_pet_name)
        pet.add_task(
            Task(
                description=t_desc.strip() or "Untitled task",
                duration_min=int(t_duration),
                priority=PRIORITY_LABELS[t_priority],
                category=t_category.strip() or "general",
                fixed_time=t_fixed_time,
            )
        )
        st.success(f"Added '{t_desc.strip()}' for {pet.name}.")


# --- Current pets & tasks ----------------------------------------------------
st.divider()
st.subheader("🗂️ Current Pets & Tasks")
if not owner.pets:
    st.info("No pets yet.")
else:
    for pet in owner.pets:
        st.markdown(f"**{pet.summary()}** — {len(pet.tasks)} task(s)")
        if pet.tasks:
            st.table(
                [
                    {
                        "task": t.description,
                        "duration (min)": t.duration_min,
                        "priority": {HIGH: "high", MEDIUM: "medium", LOW: "low"}[t.priority],
                        "fixed time": t.fixed_time.strftime("%H:%M") if t.is_fixed() else "—",
                        "done": "✅" if t.completed else "",
                    }
                    for t in pet.tasks
                ]
            )


# --- Build the schedule ------------------------------------------------------
st.divider()
st.subheader("📅 Today's Schedule")
if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler()
    plan = scheduler.build_plan(owner, day_start=time(8, 0))

    scheduled = plan["scheduled"]
    if scheduled:
        st.table(
            [
                {
                    "time": item["start"].strftime("%H:%M"),
                    "pet": item["pet"],
                    "task": item["task"].description,
                    "duration (min)": item["task"].duration_min,
                }
                for item in scheduled
            ]
        )
    else:
        st.info("Nothing could be scheduled with the current time budget.")

    # Show the plan's own explanation (why tasks were chosen / skipped).
    st.markdown("**Why this plan?**")
    st.code(scheduler.explain_plan(plan), language="text")
