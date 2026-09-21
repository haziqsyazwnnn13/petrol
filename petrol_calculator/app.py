import streamlit as st
from datetime import datetime


# ============================================================
# SETTINGS
# ============================================================

PETROL_PRICE = 2.05


# ============================================================
# FUEL CONSUMPTION
# ============================================================

def get_km_per_litre(km):
    """
    More KM = higher fuel consumption.
    Range: 13 km/L down to 10 km/L.
    """

    if km <= 20:
        return 13
    elif km <= 50:
        return 12
    elif km <= 100:
        return 11
    else:
        return 10


# ============================================================
# SESSION STATE
# ============================================================

if "active_session" not in st.session_state:
    st.session_state.active_session = False

if "starting_litres" not in st.session_state:
    st.session_state.starting_litres = 0.0

if "starting_rm" not in st.session_state:
    st.session_state.starting_rm = 0.0

if "total_km" not in st.session_state:
    st.session_state.total_km = 0.0

if "fuel_left" not in st.session_state:
    st.session_state.fuel_left = 0.0

if "last_efficiency" not in st.session_state:
    st.session_state.last_efficiency = 16

if "trip_entries" not in st.session_state:
    st.session_state.trip_entries = []

if "history" not in st.session_state:
    st.session_state.history = []


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

st.write(
    "Track your petrol across each driving session."
)


# ============================================================
# START NEW SESSION
# ============================================================

if not st.session_state.active_session:

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

        starting_litres = starting_rm / PETROL_PRICE

        st.caption(
            f"RM {starting_rm:.2f} ÷ RM {PETROL_PRICE:.2f}/L "
            f"= {starting_litres:.2f} L"
        )

    if st.button(
        "Start Session",
        type="primary",
        use_container_width=True,
    ):

        st.session_state.active_session = True
        st.session_state.starting_litres = starting_litres
        st.session_state.starting_rm = (
            starting_litres * PETROL_PRICE
        )

        st.session_state.total_km = 0.0
        st.session_state.fuel_left = starting_litres
        st.session_state.last_efficiency = 16
        st.session_state.trip_entries = []

        st.rerun()


# ============================================================
# ACTIVE SESSION
# ============================================================

else:

    # --------------------------------------------------------
    # CURRENT FUEL
    # --------------------------------------------------------

    st.subheader("Current fuel")

    starting_litres = st.session_state.starting_litres
    fuel_left = st.session_state.fuel_left

    if starting_litres > 0:

        fuel_percent = (
            fuel_left / starting_litres
        ) * 100

    else:

        fuel_percent = 0

    fuel_percent = max(
        0,
        min(fuel_percent, 100),
    )

    # Colour is handled by Streamlit itself
    st.progress(
        fuel_percent / 100,
        text=f"{fuel_percent:.0f}% fuel remaining",
    )

    st.metric(
        "Petrol left",
        f"{fuel_left:.2f} L",
    )

    st.write(
        f"Approx. value left: "
        f"**RM {fuel_left * PETROL_PRICE:.2f}**"
    )


    # --------------------------------------------------------
    # ADD KM
    # --------------------------------------------------------

    st.subheader("Enter KM used")

    st.write(
        "You can enter KM after each trip. "
        "The app will update the petrol remaining."
    )

    km_used = st.number_input(
        "KM for this trip",
        min_value=0.0,
        value=10.0,
        step=1.0,
    )

    if st.button(
        "Add KM",
        type="primary",
        use_container_width=True,
    ):

        if km_used <= 0:

            st.error(
                "Please enter KM greater than 0."
            )

        elif fuel_left <= 0:

            st.error(
                "There is no estimated petrol remaining."
            )

        else:

            # Determine consumption for this trip
            efficiency = get_km_per_litre(
                km_used
            )

            # Petrol consumed
            petrol_used = (
                km_used / efficiency
            )

            # Prevent going below zero
            petrol_used = min(
                petrol_used,
                fuel_left,
            )

            # Update session
            st.session_state.fuel_left = (
                fuel_left - petrol_used
            )

            st.session_state.total_km += km_used

            st.session_state.last_efficiency = (
                efficiency
            )

            # Save this trip entry
            st.session_state.trip_entries.append(
                {
                    "time": datetime.now().strftime(
                        "%H:%M"
                    ),
                    "km": km_used,
                    "efficiency": efficiency,
                    "fuel": petrol_used,
                    "remaining": st.session_state.fuel_left,
                }
            )

            st.rerun()


    # --------------------------------------------------------
    # CURRENT ESTIMATE
    # --------------------------------------------------------

    st.subheader("Current estimate")

    current_efficiency = (
        st.session_state.last_efficiency
    )

    current_fuel_left = (
        st.session_state.fuel_left
    )

    current_km_left = (
        current_fuel_left
        * current_efficiency
    )

    current_rm_left = (
        current_fuel_left
        * PETROL_PRICE
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "KM used",
            f"{st.session_state.total_km:.0f}",
        )

    with col2:

        st.metric(
            "KM left",
            f"{current_km_left:.0f}",
        )

    col3, col4 = st.columns(2)

    with col3:

        st.metric(
            "Fuel left",
            f"{current_fuel_left:.2f} L",
        )

    with col4:

        st.metric(
            "Value left",
            f"RM {current_rm_left:.2f}",
        )

    st.caption(
        f"Current estimate uses "
        f"{current_efficiency} km/L."
    )


    # --------------------------------------------------------
    # TRIP HISTORY INSIDE CURRENT SESSION
    # --------------------------------------------------------

    if st.session_state.trip_entries:

        st.subheader("This session")

        for index, trip in enumerate(
            reversed(st.session_state.trip_entries),
            start=1,
        ):

            st.write(
                f"**Trip {len(st.session_state.trip_entries) - index + 1}** "
                f"• {trip['time']}"
            )

            st.write(
                f"{trip['km']:.0f} km "
                f"→ {trip['fuel']:.2f} L used "
                f"→ {trip['remaining']:.2f} L remaining"
            )

            st.divider()


    # --------------------------------------------------------
    # SAVE & RESET
    # --------------------------------------------------------

    st.subheader("Finish this session")

    st.write(
        "Save this cycle to history and start again "
        "with a new petrol amount."
    )

    if st.button(
        "Save & Reset",
        use_container_width=True,
    ):

        # Save current session
        session_record = {
            "date": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            ),
            "starting_litres": (
                st.session_state.starting_litres
            ),
            "starting_rm": (
                st.session_state.starting_rm
            ),
            "total_km": (
                st.session_state.total_km
            ),
            "fuel_used": (
                st.session_state.starting_litres
                - st.session_state.fuel_left
            ),
            "fuel_left": (
                st.session_state.fuel_left
            ),
        }

        st.session_state.history.append(
            session_record
        )

        # Reset active session
        st.session_state.active_session = False
        st.session_state.starting_litres = 0.0
        st.session_state.starting_rm = 0.0
        st.session_state.total_km = 0.0
        st.session_state.fuel_left = 0.0
        st.session_state.last_efficiency = 16
        st.session_state.trip_entries = []

        st.rerun()


# ============================================================
# SESSION HISTORY
# ============================================================

st.divider()

st.subheader("History")

if not st.session_state.history:

    st.write(
        "No previous sessions yet."
    )

else:

    # Show newest first
    for index, session in enumerate(
        reversed(st.session_state.history),
        start=1,
    ):

        with st.expander(
            f"Session {len(st.session_state.history) - index + 1} "
            f"— {session['date']}"
        ):

            st.write(
                f"Starting petrol: "
                f"**{session['starting_litres']:.2f} L**"
            )

            st.write(
                f"Starting value: "
                f"**RM {session['starting_rm']:.2f}**"
            )

            st.write(
                f"Total KM: "
                f"**{session['total_km']:.0f} km**"
            )

            st.write(
                f"Estimated petrol used: "
                f"**{session['fuel_used']:.2f} L**"
            )

            st.write(
                f"Petrol remaining at reset: "
                f"**{session['fuel_left']:.2f} L**"
            )


# ============================================================
# FORMULA
# ============================================================

st.divider()

st.caption(
    "Petrol price: RM 2.05/L"
)

st.caption(
    "Consumption: 16 km/L for short trips, "
    "decreasing to 12 km/L for longer trips."
)