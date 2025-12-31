import streamlit as st
import random
import time
import math
import pandas as pd

# -------------------------
# Page setup
# -------------------------
st.set_page_config(page_title="Queue M/M/c", layout="wide")

def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

st.title("🏦 Queueing System – M/M/c")

# Parameters
st.sidebar.header("⚙️ Parameters")

lambda_rate = st.sidebar.slider("Arrival rate λ", 0.1, 3.0, 1.0, 0.1)
mu_rate = st.sidebar.slider("Service rate μ", 0.2, 4.0, 1.5, 0.1)
c = st.sidebar.selectbox("Number of servers (c)", [1, 2, 3])
T_MAX = st.sidebar.slider("Simulation time", 20, 500, 100)
animation_delay = st.sidebar.slider("Animation speed (s)", 0.1, 1.5, 0.5, 0.05)

# Session state
if "running" not in st.session_state:
    st.session_state.running = False
if "paused" not in st.session_state:
    st.session_state.paused = False
if "time" not in st.session_state:
    st.session_state.time = 0.0
if "queue" not in st.session_state:
    st.session_state.queue = 0
if "busy" not in st.session_state:
    st.session_state.busy = 0
if "arrivals" not in st.session_state:
    st.session_state.arrivals = 0
if "served" not in st.session_state:
    st.session_state.served = 0
if "queue_time" not in st.session_state:
    st.session_state.queue_time = 0.0
if "busy_time" not in st.session_state:
    st.session_state.busy_time = 0.0
if "queue_history" not in st.session_state:
    st.session_state.queue_history = []
if "time_history" not in st.session_state:
    st.session_state.time_history = []

# Controls
col1, col2 = st.sidebar.columns(2)

if col1.button("▶️ Start" if not st.session_state.running else "⏸️ Stop"):
    st.session_state.running = not st.session_state.running
    st.session_state.last_update = time.time()

if col2.button("🔄 Reset"):
    st.session_state.running = False
    st.session_state.paused = False
    st.session_state.time = 0.0
    st.session_state.queue = 0
    st.session_state.busy = 0
    st.session_state.arrivals = 0
    st.session_state.served = 0
    st.session_state.queue_time = 0.0
    st.session_state.busy_time = 0.0
    st.session_state.queue_history = []
    st.session_state.time_history = []

# One CTMC event
def simulation_step():
    t = st.session_state.time
    q = st.session_state.queue
    b = st.session_state.busy
    
    # Rates
    arrival_rate = lambda_rate
    service_rate = min(b, c) * mu_rate  # At most c servers can work
    total_rate = arrival_rate + service_rate
    
    if total_rate == 0:
        return
    
    dt = random.expovariate(total_rate)
    next_time = min(t + dt, T_MAX)
    
    # Update time-weighted averages
    st.session_state.queue_time += q * (next_time - t)
    st.session_state.busy_time += b * (next_time - t)
    st.session_state.time = next_time
    
    # Record for plotting
    st.session_state.queue_history.append(q)
    st.session_state.time_history.append(next_time)
    
    # Determine event type
    if random.random() < arrival_rate / total_rate:
        # ARRIVAL
        st.session_state.arrivals += 1
        if b < c:
            st.session_state.busy += 1  # Go directly to server
        else:
            st.session_state.queue += 1  # Join queue
    else:
        # SERVICE COMPLETION
        st.session_state.served += 1
        if q > 0:
            # Queue not empty, customer from queue goes to server
            st.session_state.queue -= 1
            # busy count remains the same
        else:
            # Queue empty, server becomes idle
            st.session_state.busy = max(0, b - 1)

# Run simulation step if running and not paused
if st.session_state.running and not st.session_state.paused and st.session_state.time < T_MAX:
    simulation_step()

# Display live animation
st.subheader("🎞️ Live Animation")

with st.container():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)

    st.markdown("### Queue")
    st.markdown("".join("🧍" for _ in range(st.session_state.queue)) or "—")

    st.markdown("### Servers")
    server_html = ""
    for i in range(c):
        cls = "busy" if i < st.session_state.busy else "free"
        server_html += f"<span class='server {cls}'>💼</span>"
    st.markdown(server_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Display metrics
colA, colB, colC = st.columns(3)
colA.metric("⏱ Time", f"{st.session_state.time:.2f}")
colB.metric("📥 Arrivals", st.session_state.arrivals)
colC.metric("✅ Served", st.session_state.served)

# Plot queue length over time using st.line_chart
if st.session_state.queue_history:
    st.subheader("📈 Queue Length Over Time")
    df = pd.DataFrame({
        "Time": st.session_state.time_history,
        "Queue Length": st.session_state.queue_history
    })
    df = df.set_index("Time")
    st.line_chart(df)

# Final statistics and Little’s Law
if st.session_state.time > 0:
    # Simulated metrics
    Wq_sim = st.session_state.queue_time / max(st.session_state.served, 1)  # Time in queue
    W_sim = Wq_sim + (1/mu_rate)  # Time in system = time in queue + service time
    utilization = st.session_state.busy_time / (c * st.session_state.time)
    served_pct = st.session_state.served / max(st.session_state.arrivals, 1)
    L_sim = sum(st.session_state.queue_history) / len(st.session_state.queue_history) if st.session_state.queue_history else 0
    L_little = lambda_rate * W_sim  # Use W_sim (time in system) for Little's Law
    
    st.subheader("📊 Simulated Results")
    st.write(f"Average time in system (W): **{W_sim:.3f}**")
    st.write(f"Average time in queue (Wq): **{Wq_sim:.3f}**")
    st.write(f"Server utilization (ρ): **{utilization:.3f}**")
    st.write(f"Percentage served: **{served_pct:.3f}**")
    st.write(f"Average queue length (Lq): **{L_sim:.3f}**")
    st.write(f"Little's Law L = λ * W: **{L_little:.3f}**")
    st.write(f"Difference: **{abs(L_sim - L_little):.3f}**")
    
    # Calculate theoretical values based on system type
    if c == 1 and lambda_rate < mu_rate:
        st.subheader("📐 Theoretical M/M/1")
        rho_theoretical = lambda_rate / mu_rate
        W_theoretical = 1 / (mu_rate - lambda_rate)  # Time in system
        Wq_theoretical = lambda_rate / (mu_rate * (mu_rate - lambda_rate))  # Time in queue
        Lq_theoretical = rho_theoretical**2 / (1 - rho_theoretical)
        
        st.write(f"Theoretical time in system (W): **{W_theoretical:.3f}**")
        st.write(f"Theoretical time in queue (Wq): **{Wq_theoretical:.3f}**")
        st.write(f"Theoretical utilization ρ: **{rho_theoretical:.3f}**")
        st.write(f"Theoretical queue length (Lq): **{Lq_theoretical:.3f}**")
        
    elif c > 1 and (lambda_rate / (c * mu_rate)) < 1:
        st.subheader(f"📐 Theoretical M/M/{c}")
        rho_theoretical = lambda_rate / (c * mu_rate)
        sum_term = sum((c * rho_theoretical)**k / math.factorial(k) for k in range(c))
        p0 = 1 / (sum_term + (c * rho_theoretical)**c / (math.factorial(c) * (1 - rho_theoretical)))
        
        Lq_theoretical = ((c * rho_theoretical)**c * rho_theoretical) / (math.factorial(c) * (1 - rho_theoretical)**2) * p0
        Wq_theoretical = Lq_theoretical / lambda_rate  # Time in queue
        W_theoretical = Wq_theoretical + 1 / mu_rate  # Time in system
        
        st.write(f"Theoretical time in system (W): **{W_theoretical:.3f}**")
        st.write(f"Theoretical time in queue (Wq): **{Wq_theoretical:.3f}**")
        st.write(f"Theoretical utilization ρ: **{rho_theoretical:.3f}**")
        st.write(f"Theoretical queue length (Lq): **{Lq_theoretical:.3f}**")
    
    # Create comparison table if theoretical values are calculated
    if ('rho_theoretical' in locals() or 'rho_theoretical' in globals()):
        comparison_data = {
            "Metric": ["Utilization (ρ)", 
                      "Avg time in system (W)", 
                      "Avg time in queue (Wq)", 
                      "Avg queue length (Lq)"],
            "Simulated": [utilization, W_sim, Wq_sim, L_sim],
            "Theoretical": [rho_theoretical, W_theoretical, Wq_theoretical, Lq_theoretical],
            "Difference": [abs(utilization - rho_theoretical), 
                          abs(W_sim - W_theoretical),
                          abs(Wq_sim - Wq_theoretical),
                          abs(L_sim - Lq_theoretical)]
        }
        
        st.subheader("📊 Theoretical vs. Simulated Comparison")
        df_comparison = pd.DataFrame(comparison_data)
        st.table(df_comparison)

# Auto animation loop
if st.session_state.running and st.session_state.time < T_MAX:
    time.sleep(animation_delay)
    st.session_state.step_pending = True
    st.rerun()
