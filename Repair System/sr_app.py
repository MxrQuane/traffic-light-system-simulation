import streamlit as st
import random
import numpy as np
import time

# Page setup
st.set_page_config(
    page_title="Repair System – Birth–Death Process",
    layout="wide"
)

def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

st.title("🔧 Birth–Death Process – Machine Repair System")

# Parameters
N = 3  # number of machines

st.sidebar.header("⚙️ System Parameters")

animation_delay = st.sidebar.slider(
    "Animation speed (seconds per event)",
    0.2, 1.5, 0.6, 0.1
)

lambda_rate = st.sidebar.slider(
    "Failure rate λ  (per machine / hour)", 0.05, 1.0, 0.2, 0.05
)
mu_rate = st.sidebar.slider(
    "Repair rate μ (per team / hour)", 0.1, 1.0, 0.5, 0.05
)
teams = st.sidebar.selectbox("Maintenance teams", [1, 2])
T_MAX = st.sidebar.slider("Simulation horizon (hours)", 10, 500, 100)

def compute_Q_matrix(N, lambda_rate, mu_rate, teams):
    Q = np.zeros((N+1, N+1))
    for i in range(N+1):
        # Birth rates (failures)
        if i < N:
            Q[i, i+1] = (N - i) * lambda_rate
        # Death rates (repairs)
        if i > 0:
            Q[i, i-1] = min(i, teams) * mu_rate
        # Diagonal elements
        Q[i, i] = -np.sum(Q[i, :])
    return Q

if st.sidebar.checkbox("Show generator matrix Q"):
    Q = compute_Q_matrix(N, lambda_rate, mu_rate, teams)
    st.subheader("Generator Matrix Q")
    st.dataframe(Q, use_container_width=True)

# Session state init
if "running" not in st.session_state:
    st.session_state.running = False

if "time" not in st.session_state:
    st.session_state.time = 0.0

if "state" not in st.session_state:
    st.session_state.state = 0  # failed machines

if "history" not in st.session_state:
    st.session_state.history = []

if "time_in_state" not in st.session_state:
    st.session_state.time_in_state = np.zeros(N + 1)

if "step_pending" not in st.session_state:
    st.session_state.step_pending = False

# Controls
col1, col2 = st.sidebar.columns(2)

if col1.button("▶️ Start" if not st.session_state.running else "⏸️ Stop"):
    st.session_state.running = not st.session_state.running
    st.session_state.last_update = time.time()

if col2.button("🔄 Reset"):
    st.session_state.running = False
    st.session_state.time = 0.0
    st.session_state.state = 0
    st.session_state.history = [(0.0, 0)]
    st.session_state.time_in_state = np.zeros(N + 1)

# Simulation step (CTMC)
def simulation_step():
    state = st.session_state.state

    birth_rate = (N - state) * lambda_rate if state < N else 0
    death_rate = min(state, teams) * mu_rate if state > 0 else 0
    total_rate = birth_rate + death_rate

    if total_rate == 0:
        return

    dt = random.expovariate(total_rate)
    next_time = min(st.session_state.time + dt, T_MAX)

    st.session_state.time_in_state[state] += next_time - st.session_state.time
    st.session_state.time = next_time

    if st.session_state.time >= T_MAX:
        st.session_state.running = False
        return

    if random.random() < birth_rate / total_rate:
        st.session_state.state += 1
    else:
        st.session_state.state -= 1

    st.session_state.history.append(
        (st.session_state.time, st.session_state.state)
    )

# Run simulation safely
if st.session_state.running and st.session_state.step_pending:
    simulation_step()
    st.session_state.step_pending = False

# Display metrics
colA, colB, colC = st.columns(3)

with colA:
    st.markdown(
        f"<div class='metric-box'>"
        f"<h3>⏱ Time</h3>"
        f"<h2>{st.session_state.time:.2f} h</h2>"
        f"</div>",
        unsafe_allow_html=True
    )

with colB:
    st.markdown(
        f"<div class='metric-box state-{st.session_state.state}'>"
        f"<h3>❌ Failed machines</h3>"
        f"<h2>{st.session_state.state}</h2>"
        f"</div>",
        unsafe_allow_html=True
    )

with colC:
    st.markdown(
        f"<div class='metric-box'>"
        f"<h3>✅ Working machines</h3>"
        f"<h2>{N - st.session_state.state}</h2>"
        f"</div>",
        unsafe_allow_html=True
    )

# Animation: Repair system
st.subheader("🛠️ Live System Animation")

with st.container():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)

    # Machines
    st.markdown("### Machines")
    machine_html = ""
    for i in range(N):
        if i < st.session_state.state:
            machine_html += "<span class='machine failed'>🔴</span>"
        else:
            machine_html += "<span class='machine'>🟢</span>"

    st.markdown(machine_html, unsafe_allow_html=True)

    # Repair teams
    st.markdown("### Repair Teams")
    team_html = ""
    busy_teams = min(st.session_state.state, teams)

    for _ in range(busy_teams):
        team_html += "<span class='repair-team'>👨‍🔧</span>"
    for _ in range(teams - busy_teams):
        team_html += "<span class='repair-team' style='opacity:0.3'>👨‍🔧</span>"

    st.markdown(team_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Trajectory plot
if len(st.session_state.history) > 1:
    times, states = zip(*st.session_state.history)
    st.subheader("📈 Trajectory of Failed Machines")
    st.line_chart(
        {"Failed machines": states},
        height=300
    )

# Monte Carlo statistics
if st.session_state.time > 0:
    pi_est = st.session_state.time_in_state / st.session_state.time
    availability = sum((N - i) * pi_est[i] for i in range(N + 1)) / N
    
    mean_failed = sum(i * pi_est[i] for i in range(N + 1))
    rho = (mean_failed * lambda_rate) / (teams * mu_rate)

    st.subheader("📊 Estimated Steady-State Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.success(f"**ρ (Facteur de charge):** {rho:.4f}")

    with col2:
        st.success(f"**Mean failed machines:** {mean_failed:.2f}")

    with col3:
        st.success(f"**Availability:** {availability:.4f}")

    with col4:
        st.write("**State probabilities:**")
        for i, p in enumerate(pi_est):
            st.write(f"P(X = {i}) = {p:.4f}")


def theoretical_steady_state(N, lambda_rate, mu_rate, teams):
    pi = np.zeros(N + 1)

    # pi[0] = 1 before normalization
    pi[0] = 1.0

    for i in range(1, N + 1):
        birth = (N - i + 1) * lambda_rate
        death = min(i, teams) * mu_rate
        pi[i] = pi[i - 1] * birth / death

    # Normalize
    pi = pi / np.sum(pi)

    # Availability (same definition as simulation)
    availability = sum((N - i) * pi[i] for i in range(N + 1)) / N

    return pi, availability

# Display comparison
st.subheader("📐 Theoretical")
pi_theory, avail_theory = theoretical_steady_state(N, lambda_rate, mu_rate, teams)
mean_failed_theory = sum(i * pi_theory[i] for i in range(N + 1))
rho_theory = (mean_failed_theory * lambda_rate) / (teams * mu_rate)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info(f"**ρ (Facteur de charge):** {rho_theory:.4f}")
with col2:
    st.info(f"**Mean failed machines:** {mean_failed_theory:.2f}")
with col3:
    st.info(f"Availability: {avail_theory:.4f}")
with col4:
    st.write("**Theoretical steady-state:**")
    for i, p in enumerate(pi_theory):
        st.write(f"π({i}) = {p:.4f}")

if st.session_state.running and st.session_state.time < T_MAX:
    time.sleep(animation_delay)
    st.session_state.step_pending = True
    st.rerun()
