import streamlit as st
import time
import random

st.set_page_config(page_title="Traffic Light Intersection", layout="wide")

# call the css file
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("styles.css")

# Initialize session state
if 'phase' not in st.session_state:
    st.session_state.phase = 0
if 'running' not in st.session_state:
    st.session_state.running = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if 'timer' not in st.session_state:
    st.session_state.timer = 0
if 'duration' not in st.session_state:
    st.session_state.duration = 5
if 'cars' not in st.session_state:
    st.session_state.cars = []
if 'car_spawn_counter' not in st.session_state:
    st.session_state.car_spawn_counter = 0
if 'next_car_id' not in st.session_state:
    st.session_state.next_car_id = 0

# Car class
class Car:
    def __init__(self, direction, car_id):
        self.direction = direction  # 'ns', 'sn', 'ew', 'we'
        self.id = car_id
        self.emoji = random.choice(['🚗', '🚕', '🚙', '🚌'])
        
        # Starting positions
        if direction == 'ns':  # North to South
            self.x = 260
            self.y = -30
        elif direction == 'sn':  # South to North
            self.x = 315
            self.y = 630
        elif direction == 'ew':  # East to West
            self.x = 630
            self.y = 250
        elif direction == 'we':  # West to East
            self.x = -30
            self.y = 315

    def is_blocking(self, other_car, safe_distance):
        """Helper function to determine if another car is blocking."""
        if self.direction in ['ns', 'sn']:
            vertical_check = (other_car.direction == self.direction and
                            abs(other_car.y - self.y) < safe_distance and
                            ((self.direction == 'ns' and other_car.y > self.y) or
                            (self.direction == 'sn' and other_car.y < self.y)))
            intersection_check = (other_car.direction in ['we', 'ew'] and
                                self.is_in_intersection() and
                                abs(other_car.x - self.x) < safe_distance and
                                abs(other_car.y - self.y) < safe_distance)
            return vertical_check or intersection_check

        if self.direction in ['ew', 'we']:
            horizontal_check = (other_car.direction == self.direction and
                                abs(other_car.x - self.x) < safe_distance and
                                ((self.direction == 'ew' and other_car.x < self.x) or
                                (self.direction == 'we' and other_car.x > self.x)))
            intersection_check = (other_car.direction in ['ns', 'sn'] and
                                self.is_in_intersection() and
                                abs(other_car.x - self.x) < safe_distance and
                                abs(other_car.y - self.y) < safe_distance)
            return horizontal_check or intersection_check

        return False

    def is_in_intersection(self):
        """Helper function to check if the car is in the intersection area."""
        if self.direction in ['ns', 'sn']:
            return 200 < self.y < 250 if self.direction == 'ns' else 350 < self.y < 400
        if self.direction in ['ew', 'we']:
            return 350 < self.x < 400 if self.direction == 'ew' else 200 < self.x < 250
        return False
    
    def update(self, can_move, cars_ahead):
        speed = 10
        safe_distance = 40  # Minimum distance between cars

        # Check if there's a car too close ahead
        car_blocking = any(self.is_blocking(other_car, safe_distance) for other_car in cars_ahead if other_car.id != self.id)

        # Don't move if car ahead is too close or if red light at intersection
        if car_blocking:
            return

        if self.direction == 'ns' and (not can_move and self.is_in_intersection()):
            return
        if self.direction == 'sn' and (not can_move and self.is_in_intersection()):
            return
        if self.direction == 'ew' and (not can_move and self.is_in_intersection()):
            return
        if self.direction == 'we' and (not can_move and self.is_in_intersection()):
            return

        # Update position based on direction
        if self.direction == 'ns':
            self.y += speed
        elif self.direction == 'sn':
            self.y -= speed
        elif self.direction == 'ew':
            self.x -= speed
        elif self.direction == 'we':
            self.x += speed
        
    def is_off_screen(self):
        return self.x < -50 or self.x > 650 or self.y < -50 or self.y > 650
    
    def get_html(self):
        rotation = -90
        if self.direction == 'ew':
            rotation = 0
        elif self.direction == 'we':
            rotation = 180
        elif self.direction == 'sn':
            rotation = 90
        
        # Use car ID for stable z-index that doesn't change when other cars despawn
        # Each direction gets a base layer, then add the unique car ID
        if self.direction == 'ns':
            z_index = 1000000 + self.id
        elif self.direction == 'sn':
            z_index = 2000000 + self.id
        elif self.direction == 'ew':
            z_index = 3000000 + self.id
        else:  # 'we'
            z_index = 4000000 + self.id
        
        return f'<div class="car" style="left: {self.x}px; top: {self.y}px; transform: rotate({rotation}deg); z-index: {z_index};">{self.emoji}</div>'

# Sidebar controls
st.sidebar.title("🚦 Traffic Light Controls")
green_min = st.sidebar.slider("Green Light Min (seconds)", 1, 10, 3)
green_max = st.sidebar.slider("Green Light Max (seconds)", 1, 15, 6)
car_spawn_rate = st.sidebar.slider("Car Spawn Rate", 1, 10, 5)

if st.sidebar.button("▶️ Start" if not st.session_state.running else "⏸️ Stop"):
    st.session_state.running = not st.session_state.running
    st.session_state.last_update = time.time()

if st.sidebar.button("🔄 Reset"):
    st.session_state.phase = 0
    st.session_state.running = False
    st.session_state.timer = 0
    st.session_state.duration = random.randint(green_min, green_max)
    st.session_state.cars = []
    st.session_state.car_spawn_counter = 0
    st.session_state.next_car_id = 0

# Display current status
phase_names = ["🟢 North-South Green", "🟢 East-West Green"]
st.sidebar.markdown(f"**Current Phase:** {phase_names[st.session_state.phase]}")
st.sidebar.markdown(f"**Timer:** {st.session_state.timer}s / {st.session_state.duration}s")
st.sidebar.markdown(f"**Cars on road:** {len(st.session_state.cars)}")

# Update logic
if st.session_state.running:
    current_time = time.time()
    if current_time - st.session_state.last_update >= 1:
        st.session_state.timer += 1
        st.session_state.last_update = current_time
        
        if st.session_state.timer >= st.session_state.duration:
            st.session_state.phase = (st.session_state.phase + 1) % 2
            st.session_state.timer = 0
            st.session_state.duration = random.randint(green_min, green_max)
        
        # Spawn new cars
        st.session_state.car_spawn_counter += 1
        if st.session_state.car_spawn_counter >= (11 - car_spawn_rate):
            directions = ['ns', 'sn', 'ew', 'we']
            new_car = Car(random.choice(directions), st.session_state.next_car_id)
            st.session_state.cars.append(new_car)
            st.session_state.next_car_id += 1
            st.session_state.car_spawn_counter = 0
        
        st.rerun()

# Function to get light state
def get_light_state(direction):
    if st.session_state.phase == 0:  # North-South green
        if direction == 'ns': return 'green'
        if direction == 'ew': return 'red'
        if direction == 'ns_ped': return 'red'
        if direction == 'ew_ped': return 'green'
    elif st.session_state.phase == 1:  # East-West green
        if direction == 'ns': return 'red'
        if direction == 'ew': return 'green'
        if direction == 'ns_ped': return 'green'
        if direction == 'ew_ped': return 'red'
    return 'red'

def traffic_light_with_ped(state, ped_state=None):
    red_class = "red-on" if state == "red" else "red-off"
    yellow_class = "yellow-on" if state == "yellow" else "yellow-off"
    green_class = "green-on" if state == "green" else "green-off"
    
    traffic_html = f"""
    <div class="traffic-light-with-ped">
        <div class="traffic-light">
            <div class="light {red_class}"></div>
            <div class="light {yellow_class}"></div>
            <div class="light {green_class}"></div>
        </div>
        <div class="ped-light">
            <div class="ped-signal {'ped-red-on' if ped_state == 'red' else 'ped-red-off'}">🚶</div>
            <div class="ped-signal {'ped-green-on' if ped_state == 'green' else 'ped-green-off'}">🚶</div>
        </div>
    </div>
    """
    return traffic_html

# Update cars
ns_can_move = get_light_state('ns') == 'green'
ew_can_move = get_light_state('ew') == 'green'

for car in st.session_state.cars:
    can_move = ns_can_move if car.direction in ['ns', 'sn'] else ew_can_move
    car.update(can_move, st.session_state.cars)

# Remove off-screen cars
# st.session_state.cars = [car for car in st.session_state.cars if not car.is_off_screen()]

# Main title
st.title("🚦 Crossroad Traffic Light Simulation")

# Create intersection HTML
cars_html = ''.join([car.get_html() for car in st.session_state.cars])

intersection_html = f"""
<div class="intersection-container">
    <div class="road-horizontal"></div>
    <div class="road-vertical"></div>
    <div class="road-line-h"></div>
    <div class="road-line-v"></div>
    <div class="intersection-center"></div>
    
    <div class="traffic-light-pos-ns">
        {traffic_light_with_ped(get_light_state('ns'), get_light_state('ns_ped'))}
    </div>
    
    <div class="traffic-light-pos-ew">
        {traffic_light_with_ped(get_light_state('ew'), get_light_state('ew_ped'))}
    </div>
    
    {cars_html}
</div>
"""

st.markdown(f'<div class="intersection-container"><div class="road-horizontal"></div><div class="road-vertical"></div><div class="road-line-h"></div><div class="road-line-v"></div><div class="intersection-center"></div><div class="traffic-light-pos-ns">{traffic_light_with_ped(get_light_state('ns'), get_light_state('ns_ped'))}</div><div class="traffic-light-pos-ew">{traffic_light_with_ped(get_light_state('ew'), get_light_state('ew_ped'))}</div>{cars_html}</div>', unsafe_allow_html=True)

# Auto-refresh when running
if st.session_state.running:
    time.sleep(0.1)
    st.rerun()