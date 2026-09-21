import uuid
from datetime import datetime

import streamlit as st
from supabase import create_client


# ============================================================
# SETTINGS
# ============================================================

PETROL_PRICE = 2.05


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


supabase = get_supabase()


# ============================================================
# PERSISTENT CLIENT ID
# ============================================================

def get_client_id():
    existing_id = st.query_params.get("device_id")

    if existing_id:
        try:
            uuid.UUID(existing_id)
            return existing_id
        except ValueError:
            pass

    new_id = str(uuid.uuid4())

    st.query_params["device_id"] = new_id

    return new_id


CLIENT_ID = get_client_id()


# ============================================================
# CONSUMPTION
# ============================================================

def get_km_per_litre(total_km):
    """
    10-13 km/L.
    More total KM = higher fuel consumption.
    """

    if total_km <= 20:
        return 15

    elif total_km <= 50:
        return 14

    elif total_km <= 100:
        return 13

    else:
        return 12


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_active_session():
    response = (
        supabase
        .table("fuel_sessions")
        .select("*")
        .eq("client_id", CLIENT_ID)
        .eq("status", "active")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def get_closed_sessions():
    response = (
        supabase
        .table("fuel_sessions")
        .select("*")
        .eq("client_id", CLIENT_ID)
        .eq("status", "closed")
        .order("started_at", desc=True)
        .execute()
    )

    return response.data or []


def get_session_trips(session_id):
    response = (
        supabase
        .table("fuel_trips")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def create_session(starting_litres):

    starting_rm = (
        starting_litres * PETROL_PRICE
    )

    response = (
        supabase
        .table("fuel_sessions")
        .insert(
            {
                "client_id": CLIENT_ID,
                "status": "active",
                "starting_litres": starting_litres,
                "starting_rm": starting_rm,
                "total_km": 0,
                "fuel_left_litres": starting_litres,
                "last_km_per_litre": 13,
            }
        )
        .execute()
    )

    return response.data[0]


def add_trip(
    session,
    km_used,
):
    old_total_km = float(
        session["total_km"]
    )

    old_fuel_left = float(
        session["fuel_left_litres"]
    )

    new_total_km = (
        old_total_km + km_used
    )

    # Rate based on cumulative KM.
    km_per_litre = get_km_per_litre(
        new_total_km
    )

    petrol_used = (
        km_used / km_per_litre
    )

    petrol_used = min(
        petrol_used,
        old_fuel_left,
    )

    new_fuel_left = max(
        old_fuel_left - petrol_used,
        0,
    )

    # --------------------------------------------------------
    # Update session first
    # --------------------------------------------------------

    supabase \
        .table("fuel_sessions") \
        .update(
            {
                "total_km": new_total_km,
                "fuel_left_litres": new_fuel_left,
                "last_km_per_litre": km_per_litre,
            }
        ) \
        .eq("id", session["id"]) \
        .execute()

    # --------------------------------------------------------
    # Store individual trip
    # --------------------------------------------------------

    try:

        supabase \
            .table("fuel_trips") \
            .insert(
                {
                    "session_id": session["id"],
                    "client_id": CLIENT_ID,
                    "km": km_used,
                    "km_per_litre": km_per_litre,
                    "petrol_used_litres": petrol_used,
                    "fuel_remaining_litres": new_fuel_left,
                }
            ) \
            .execute()

    except Exception:

        # Try to restore old session state
        supabase \
            .table("fuel_sessions") \
            .update(
                {
                    "total_km": old_total_km,
                    "fuel_left_litres": old_fuel_left,
                }
            ) \
            .eq("id", session["id"]) \
            .execute()

        raise


def close_session(session):

    (
        supabase
        .table("fuel_sessions")
        .update(
            {
                "status": "closed",
                "closed_at": datetime.utcnow().isoformat(),
            }
        )
        .eq("id", session["id"])
        .execute()
    )


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Petrol Calculator",
    page_icon="⛽",
    layout="centered",
)


# ============================================================
# TITLE
# ============================================================

st.title("⛽ Petrol Calculator")

st.caption(
    "Your fuel sessions are saved automatically."
)


# ============================================================
# GET CURRENT SESSION
# ============================================================

try:

    active_session = get_active_session()

except Exception as error:

    st.error(
        "Could not connect to Supabase."
    )

    st.code(str(error))

    st.stop()


# ============================================================
# NO ACTIVE SESSION
# ============================================================

if not active_session:

    st.subheader("Start a new session")

    input_type = st.radio(
        "Enter starting petrol as",
        ["Litres", "RM"],
        horizontal=True,
    )

    if input_type == "Litres":

        starting_litres = st.number_input(
            "Starting litres",
            min_value=0.0,
            value=30.0,
            step=0.5,
        )

    else:

        starting_rm = st.number_input(
            "Starting RM",
            min_value=0.0,
            value=60.0,
            step=1.0,
        )

        starting_litres = (
            starting_rm / PETROL_PRICE
        )

        st.caption(
            f"RM {starting_rm:.2f} "
            f"÷ RM {PETROL_PRICE:.2f}/L "
            f"= {starting_litres:.2f} L"
        )


    if st.button(
        "Start Session",
        type="primary",
        use_container_width=True,
    ):

        if starting_litres <= 0:

            st.error(
                "Please enter a petrol amount."
            )

        else:

            try:

                create_session(
                    starting_litres
                )

                st.success(
                    "Session saved."
                )

                st.rerun()

            except Exception as error:

                st.error(
                    "Could not save the session."
                )

                st.code(str(error))


# ============================================================
# ACTIVE SESSION
# ============================================================

else:

    session_id = active_session["id"]

    starting_litres = float(
        active_session["starting_litres"]
    )

    total_km = float(
        active_session["total_km"]
    )

    fuel_left = float(
        active_session["fuel_left_litres"]
    )

    current_rate = int(
        active_session["last_km_per_litre"]
    )


    # --------------------------------------------------------
    # FUEL FIGURE
    # --------------------------------------------------------

    st.subheader("Fuel remaining")

    if starting_litres > 0:

        fuel_percent = (
            fuel_left /
            starting_litres
        ) * 100

    else:

        fuel_percent = 0


    fuel_percent = max(
        0,
        min(fuel_percent, 100),
    )


    st.progress(
        fuel_percent / 100,
        text=f"{fuel_percent:.0f}% remaining",
    )


    st.metric(
        "Petrol left",
        f"{fuel_left:.2f} L",
    )


    # Current estimated range
    km_left = (
        fuel_left *
        current_rate
    )


    st.write(
        f"Estimated KM left: "
        f"**{km_left:.0f} km**"
    )

    st.write(
        f"Estimated value left: "
        f"**RM {fuel_left * PETROL_PRICE:.2f}**"
    )


    # --------------------------------------------------------
    # ADD KM
    # --------------------------------------------------------

    st.subheader("Add KM")

    st.caption(
        "Enter the KM used since your last entry."
    )

    with st.form("trip_form"):

        km_used = st.number_input(
            "KM used",
            min_value=0.1,
            value=10.0,
            step=1.0,
        )

        submitted = st.form_submit_button(
            "Add KM",
            type="primary",
            use_container_width=True,
        )


    if submitted:

        try:

            add_trip(
                active_session,
                km_used,
            )

            st.success(
                f"{km_used:.0f} KM saved."
            )

            st.rerun()

        except Exception as error:

            st.error(
                "Could not save the KM entry."
            )

            st.code(str(error))


    # --------------------------------------------------------
    # CURRENT SESSION SUMMARY
    # --------------------------------------------------------

    st.subheader("Current session")

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "Total KM",
            f"{total_km:.0f}",
        )

    with c2:

        st.metric(
            "Rate",
            f"{current_rate} km/L",
        )


    # --------------------------------------------------------
    # TRIP HISTORY
    # --------------------------------------------------------

    trips = get_session_trips(
        session_id
    )


    if trips:

        st.subheader("KM history")

        for number, trip in enumerate(
            trips,
            start=1,
        ):

            trip_km = float(
                trip["km"]
            )

            trip_fuel = float(
                trip["petrol_used_litres"]
            )

            remaining = float(
                trip["fuel_remaining_litres"]
            )

            rate = int(
                trip["km_per_litre"]
            )

            st.write(
                f"**{trip_km:.0f} KM** "
                f"→ {trip_fuel:.2f} L used "
                f"→ {remaining:.2f} L left "
                f"({rate} km/L)"
            )


    # --------------------------------------------------------
    # SAVE / RESET
    # --------------------------------------------------------

    st.divider()

    st.subheader("Finish session")

    st.caption(
        "This closes the current cycle and keeps it in history."
    )


    if st.button(
        "Save & Start New Session",
        use_container_width=True,
    ):

        try:

            close_session(
                active_session
            )

            st.success(
                "Session saved to history."
            )

            st.rerun()

        except Exception as error:

            st.error(
                "Could not close the session."
            )

            st.code(str(error))


# ============================================================
# HISTORY
# ============================================================

st.divider()

st.subheader("Previous sessions")

try:

    history = get_closed_sessions()

except Exception as error:

    history = []

    st.error(
        "Could not load history."
    )

    st.code(str(error))


if not history:

    st.caption(
        "No completed sessions yet."
    )

else:

    for session in history:

        date = session["started_at"]

        starting_litres = float(
            session["starting_litres"]
        )

        starting_rm = float(
            session["starting_rm"]
        )

        total_km = float(
            session["total_km"]
        )

        fuel_left = float(
            session["fuel_left_litres"]
        )

        fuel_used = (
            starting_litres -
            fuel_left
        )

        with st.expander(
            f"{date[:10]} • "
            f"{total_km:.0f} km • "
            f"{fuel_used:.2f} L used"
        ):

            st.write(
                f"Starting petrol: "
                f"**{starting_litres:.2f} L**"
            )

            st.write(
                f"Starting value: "
                f"**RM {starting_rm:.2f}**"
            )

            st.write(
                f"Total KM: "
                f"**{total_km:.0f} km**"
            )

            st.write(
                f"Estimated petrol used: "
                f"**{fuel_used:.2f} L**"
            )

            st.write(
                f"Petrol remaining at reset: "
                f"**{fuel_left:.2f} L**"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Petrol price: RM 2.05/L"
)

st.caption(
    "Consumption estimate: 13 → 10 km/L "
    "as total distance increases."
)