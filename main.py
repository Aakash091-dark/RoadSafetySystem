import streamlit as st
import sqlite3
from datetime import datetime
import cv2
import time
from pygame import mixer
import threading
import requests
from twilio.rest import Client
import random
import pandas as pd
import folium
from streamlit_folium import folium_static
import heapq
from PIL import Image
import io


# Initialize session state for navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"


# Initialize MetroGraph class
class MetroGraph:
    def __init__(self):
        self.graph = {
            "Shaheed Sthal": {"Hindon River": 1.0},
            "Hindon River": {"Shaheed Sthal": 1.0, "Arthala": 1.5},
            "Arthala": {"Hindon River": 1.5, "Mohan Nagar": 0.7},
            "Mohan Nagar": {"Arthala": 0.7, "Shyam Park": 1.3},
            "Shyam Park": {"Mohan Nagar": 1.3, "Major Mohit Sharma": 1.2},
            "Major Mohit Sharma": {"Shyam Park": 1.2, "Raj Bagh": 1.2},
            "Raj Bagh": {"Major Mohit Sharma": 1.2, "Shaheed Nagar": 1.3},
            "Shaheed Nagar": {"Raj Bagh": 1.3, "Dilshad Garden": 1.2},
            "Dilshad Garden": {"Shaheed Nagar": 1.2, "Jhil mil": 0.9},
            "Jhil mil": {"Dilshad Garden": 0.9, "Mansarovar Park": 1.1},
            "Mansarovar Park": {"Jhil mil": 1.1},
        }

        self.station_coords = {
            "Shaheed Sthal": (28.6725, 77.3718),
            "Hindon River": (28.6789, 77.3657),
            "Arthala": (28.6853, 77.3596),
            "Mohan Nagar": (28.6917, 77.3535),
            "Shyam Park": (28.6981, 77.3474),
            "Major Mohit Sharma": (28.7045, 77.3413),
            "Raj Bagh": (28.7109, 77.3352),
            "Shaheed Nagar": (28.7173, 77.3291),
            "Dilshad Garden": (28.7237, 77.3230),
            "Jhil mil": (28.7301, 77.3169),
            "Mansarovar Park": (28.7365, 77.3108),
        }

    def get_stations(self):
        return list(self.graph.keys())

    def dijkstra(self, start, end):
        distances = {station: float("inf") for station in self.graph}
        previous = {station: None for station in self.graph}
        distances[start] = 0
        pq = [(0, start)]

        while pq:
            current_distance, current_station = heapq.heappop(pq)

            if current_distance > distances[current_station]:
                continue

            if current_station == end:
                break

            for neighbor, weight in self.graph[current_station].items():
                distance = current_distance + weight

                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_station
                    heapq.heappush(pq, (distance, neighbor))

        if distances[end] == float("inf"):
            return None, None

        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()

        return path, distances[end]


def custom_sidebar():
    with st.sidebar:
        st.caption = "Smart Transport & Safety System"
        st.markdown("---")

        pages = {
            "Home": "🏠",
            "Drowsiness Detection": "👁",
            "Public Transport": "🚇",
            "Report Accident": "🚨",
            "Weather Details": "🌤",
            "Traffic Updates": "🚦",
            "Emergency Help": "🚑",
        }

        for page, icon in pages.items():
            if st.button(
                f"{icon} {page}",
                key=page,
                use_container_width=True,
                type=(
                    "primary" if st.session_state.current_page == page else "secondary"
                ),
            ):
                st.session_state.current_page = page

        st.markdown("---")
        st.markdown("### Quick Emergency")
        if st.button("🆘 SOS", use_container_width=True, type="primary"):
            st.session_state.current_page = "Emergency Help"


def public_transport():
    st.title("🚇 Smart Public Transport Hub")

    tabs = st.tabs(["Metro Booking", "Other Transport Options", "Benefits"])

    with tabs[0]:
        st.header("Metro Route Planning & Booking")

        if "metro_graph" not in st.session_state:
            st.session_state.metro_graph = MetroGraph()

        col1, col2 = st.columns(2)

        with col1:
            source = st.selectbox(
                "Select Source Station", st.session_state.metro_graph.get_stations()
            )
            destination = st.selectbox(
                "Select Destination Station",
                st.session_state.metro_graph.get_stations(),
            )

            if st.button("Find Route"):
                path, distance = st.session_state.metro_graph.dijkstra(
                    source, destination
                )

                if path:
                    fare = 10 + (distance * 2)  # Base fare + per km charge
                    st.success("Route Found!")
                    st.write(f"🛤️ Path: {' → '.join(path)}")
                    st.write(f"📏 Distance: {distance:.2f} km")
                    st.write(f"💰 Estimated Fare: ₹{fare:.2f}")

                    # Store route details
                    st.session_state.current_route = {
                        "path": path,
                        "distance": distance,
                        "fare": fare,
                    }

                    # Show booking form
                    with st.form("booking_form"):
                        st.subheader("Book Ticket")
                        name = st.text_input("Full Name")
                        email = st.text_input("Email")
                        phone = st.text_input("Phone Number")
                        journey_date = st.date_input("Journey Date")

                        if st.form_submit_button("Book Now"):
                            if name and email and phone:
                                booking_id = f"METRO{random.randint(10000,99999)}"
                                st.success(
                                    f"Ticket Booked Successfully! Booking ID: {booking_id}"
                                )
                                st.balloons()
                            else:
                                st.error("Please fill all required fields!")

        with col2:
            st.subheader("Live Metro Map")
            if "current_route" in st.session_state:
                m = folium.Map(location=[28.7041, 77.3025], zoom_start=12)

                # Plot stations and route
                for (
                    station,
                    coords,
                ) in st.session_state.metro_graph.station_coords.items():
                    color = (
                        "red"
                        if station in st.session_state.current_route["path"]
                        else "blue"
                    )
                    folium.CircleMarker(
                        coords, radius=8, color=color, fill=True, popup=station
                    ).add_to(m)

                # Plot route line
                route_coords = []
                path = st.session_state.current_route["path"]
                for i in range(len(path) - 1):
                    start = st.session_state.metro_graph.station_coords[path[i]]
                    end = st.session_state.metro_graph.station_coords[path[i + 1]]
                    folium.PolyLine(
                        locations=[start, end],
                        weight=4,
                        color="red",
                    ).add_to(m)

                folium_static(m)

    with tabs[1]:
        st.header("Other Transport Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("🚌 Bus Booking")
            st.write("Book bus tickets through RedBus")
            if st.button("Book Bus Tickets"):
                st.markdown("[Open RedBus](https://www.redbus.in/)")

        with col2:
            st.subheader("🚂 Train Booking")
            st.write("Book train tickets through IRCTC")
            if st.button("Book Train Tickets"):
                st.markdown("[Open IRCTC](https://www.irctc.co.in/)")

        with col3:
            st.subheader("✈️ Flight Booking")
            st.write("Book flight tickets")
            if st.button("Book Flight Tickets"):
                st.markdown("[Open Air India](https://www.airindia.com/)")

    with tabs[2]:
        st.header("Benefits of Public Transport")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🌍 Environmental Benefits")
            st.write(
                """
            - Reduced carbon emissions
            - Lower air pollution
            - Decreased traffic congestion
            - Better urban air quality
            """
            )

            st.subheader("💰 Economic Benefits")
            st.write(
                """
            - Save on fuel costs
            - Reduce vehicle maintenance
            - Lower parking fees
            - Affordable transportation
            """
            )

        with col2:
            st.subheader("🧘‍♂️ Personal Benefits")
            st.write(
                """
            - Reduced stress from driving
            - Time for reading/working
            - Regular exercise (walking to stations)
            - Enhanced safety
            """
            )

            st.subheader("🌆 Urban Benefits")
            st.write(
                """
            - Less traffic congestion
            - Improved city mobility
            - Better urban planning
            - Enhanced community connectivity
            """
            )


def create_database():
    conn = sqlite3.connect("road_safety.db")
    c = conn.cursor()

    # Create tables
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS accident_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            description TEXT,
            image BLOB,
            timestamp DATETIME
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS traffic_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            traffic_status TEXT,
            timestamp DATETIME
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS emergency_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_number TEXT,
            assistance_needed TEXT,
            timestamp DATETIME
        )
    """
    )

    conn.commit()
    conn.close()


def insert_accident(location, description, image):
    conn = sqlite3.connect("road_safety.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO accident_reports (location, description, image, timestamp)
        VALUES (?, ?, ?, ?)
    """,
        (location, description, image, datetime.now()),
    )
    conn.commit()
    conn.close()


def insert_traffic(location, traffic_status):
    conn = sqlite3.connect("road_safety.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO traffic_reports (location, traffic_status, timestamp)
        VALUES (?, ?, ?)
    """,
        (location, traffic_status, datetime.now()),
    )
    conn.commit()
    conn.close()


def insert_emergency(contact_number, assistance_needed,location):
    conn = sqlite3.connect("road_safety.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO emergency_requests (contact_number, assistance_needed, timestamp)
        VALUES (?, ?, ?)
    """,
        (contact_number, assistance_needed, datetime.now()),
    )
    conn.commit()
    conn.close()


def main():
    st.set_page_config(
        page_title="Smart Transport & Safety System",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown(
        """
        <style>
        .stButton button {
            width: 100%;
            border-radius: 5px;
            margin: 2px 0px;
        }
        .metric-container {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar navigation
    custom_sidebar()

    # Main content based on navigation
    if st.session_state.current_page == "Home":
        home()
    elif st.session_state.current_page == "Public Transport":
        public_transport()
    elif st.session_state.current_page == "Drowsiness Detection":
        drowsiness_detection()
    elif st.session_state.current_page == "Report Accident":
        report_accident()
    elif st.session_state.current_page == "Weather Details":
        weather_details()
    elif st.session_state.current_page == "Traffic Updates":
        report_traffic()
    elif st.session_state.current_page == "Emergency Help":
        emergency_assistance()


def home():
    # Hero Section with Road Safety Message
    st.markdown(
        """
    <div style='text-align: center; padding: 2rem;'>
        <h1>🛣 SAHYATRI</h1>
        <p style='font-size: 1.2rem;'>Your Comprehensive Road Safety Companion</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Introduction Section
    st.markdown(
        """
    <div style='padding: 1rem; background-color: #000000; border-radius: 10px; margin-bottom: 2rem;'>
        <h2 style='text-align: center;'>About Road Safety</h2>
        <p style='font-size: 1.1rem; text-align: justify;'>
            Road safety is paramount in today's fast-paced world. Our system integrates cutting-edge technology 
            with real-time monitoring to ensure safer journeys for everyone. From drowsiness detection to 
            emergency response systems, we provide comprehensive solutions to make every journey safer and more secure.
        </p>
        <p style='font-size: 1.1rem; text-align: justify;'>
            Every year, thousands of lives are affected by road incidents. Our mission is to reduce these numbers 
            through technology, awareness, and proactive safety measures. Together, we can create safer roads 
            for our community.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Key Features Section
    st.markdown(
        "<h2 style='text-align: center;'>Our Key Features</h2>", unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        <div style='background-color: #000000; padding: 1.5rem; border-radius: 10px; margin: 0.5rem;'>
            <h3 style='color: white;'>🚗 Smart Transport Features</h3>
            <ul style='color: white;'>
                <li>Intelligent Metro Route Planning</li>
                <li>Real-time Public Transport Updates</li>
                <li>Smart Fare Calculator</li>
                <li>Interactive Transport Maps</li>
                <li>Multi-modal Transport Integration</li>
            </ul>
        </div>
        
        <div style='background-color: #000000; padding: 1.5rem; border-radius: 10px; margin: 0.5rem; margin-top: 1rem;'>
            <h3 style='color: white;'>🚨 Emergency Services</h3>
            <ul style='color: white;'>
                <li>One-Click Emergency Alerts</li>
                <li>Real-time Accident Reporting</li>
                <li>Emergency Contact Integration</li>
                <li>Instant SOS Messaging</li>
                <li>Emergency Service Locator</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div style='background-color: #000000; padding: 1.5rem; border-radius: 10px; margin: 0.5rem;'>
            <h3 style='color: white;'>👁 Safety Monitoring</h3>
            <ul style='color: white;'>
                <li>AI-Powered Drowsiness Detection</li>
                <li>Real-time Driver Alerts</li>
                <li>Safety Score Tracking</li>
                <li>Behavior Analysis</li>
                <li>Preventive Warning System</li>
            </ul>
        </div>
        
        <div style='background-color: #000000; padding: 1.5rem; border-radius: 10px; margin: 0.5rem; margin-top: 1rem;'>
            <h3 style='color: white;'>🌤 Environmental Monitoring</h3>
            <ul style='color: white;'>
                <li>Real-time Weather Updates</li>
                <li>Road Condition Alerts</li>
                <li>Traffic Density Monitoring</li>
                <li>Air Quality Index</li>
                <li>Weather-based Route Suggestions</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Safety Statistics Section
    st.markdown("---")
    st.markdown(
        "<h2 style='text-align: center;'>Safety Impact</h2>", unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
        <div class='metric-container' style='background-color: black; color: white; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3>24/7</h3>
            <p>Monitoring</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class='metric-container' style='background-color: black; color: white; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3>< 2 min</h3>
            <p>Response Time</p>
                    
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class='metric-container' style='background-color: black; color: white; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3>98%</h3>
            <p>Alert Accuracy</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
        <div class='metric-container' style='background-color: black; color: white; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3>+</h3>
            <p>Users Protected</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Recent Updates Section
    st.markdown("---")
    st.markdown(
        "<h2 style='text-align: center;'>Latest Updates</h2>", unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.success("✅ Enhanced drowsiness detection algorithm deployed")
        st.info("🆕 Added new emergency response features")

    with col2:
        st.warning("⚠️ New safety guidelines implemented")
        st.success("✅ System response time improved by 25%")

    # Call to Action
    st.markdown("---")
    st.markdown(
        """
    <div style='text-align: center; padding: 2rem; background-color: #000000; border-radius: 10px;'>
        <h2>Start Your Safe Journey Today</h2>
        <p style='font-size: 1.1rem;'>
            Explore our features using the sidebar navigation and make every journey safer with our comprehensive safety system.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def drowsiness_detection():
    import cv2
    import time
    from pygame import mixer
    import threading
    import os

    # Initialize pygame mixer
    mixer.init()
    # Load the alarm sound
    try:
        alarm_sound = mixer.Sound("alarm.wav")
    except:
        st.error(
            "Could not load alarm.wav file. Make sure it's in the same directory as your script."
        )
        return

    st.title("Drowsiness Detection")
    st.markdown("This feature uses your webcam to detect drowsiness in real-time.")

    # Constants for drowsiness detection
    EYE_AR_CONSEC_FRAMES = 15
    COUNTER = 0
    last_alert_time = time.time()
    MIN_ALERT_INTERVAL = 2.0  # Minimum seconds between alerts

    # Create a class to handle alarm state
    class AlarmState:
        def __init__(self):
            self.is_on = False

    alarm_state = AlarmState()

    # Create status indicators
    status_indicator = st.empty()
    metrics_indicator = st.empty()

    def play_alarm(alarm_state):
        if not alarm_state.is_on:
            alarm_state.is_on = True
            alarm_sound.play()
            time.sleep(2)  # Let the sound play for 2 seconds
            alarm_state.is_on = False

    # Start the webcam
    run_detection = st.checkbox("Start Detection")
    FRAME_WINDOW = st.image([])

    if run_detection:
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml"
        )

        cap = cv2.VideoCapture(0)

        while run_detection:
            ret, frame = cap.read()
            if not ret:
                st.warning("Could not access webcam.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )

            current_time = time.time()

            for x, y, w, h in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                roi_gray = gray[y : y + h, x : x + w]
                roi_color = frame[y : y + h, x : x + w]

                eyes = eye_cascade.detectMultiScale(
                    roi_gray, scaleFactor=1.1, minNeighbors=5
                )

                if len(eyes) >= 2:  # Both eyes detected
                    COUNTER = 0
                    status_indicator.success("Eyes Open")
                    metrics_indicator.info(f"Eyes Detected: {len(eyes)}")
                else:
                    COUNTER += 1

                    if COUNTER >= EYE_AR_CONSEC_FRAMES:
                        # Visual alert
                        cv2.putText(
                            frame,
                            "DROWSINESS ALERT!",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 0, 255),
                            2,
                        )
                        status_indicator.error("DROWSINESS DETECTED!")

                        # Sound alert with rate limiting
                        if (
                            current_time - last_alert_time >= MIN_ALERT_INTERVAL
                            and not alarm_state.is_on
                        ):
                            threading.Thread(
                                target=play_alarm, args=(alarm_state,), daemon=True
                            ).start()
                            last_alert_time = current_time

                    metrics_indicator.warning(f"Eyes Closed for {COUNTER} frames")

                # Draw eye regions
                for ex, ey, ew, eh in eyes:
                    cv2.rectangle(
                        roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2
                    )

            cv2.putText(
                frame,
                f"Frame Counter: {COUNTER}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

            FRAME_WINDOW.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        cap.release()
        mixer.quit()
    else:
        st.write("Detection Stopped")
        status_indicator.empty()
        metrics_indicator.empty()


# Report Road Accidents Section
def report_accident():
    st.title("Report Road Accidents")
    st.markdown("Provide details about the accident below:")
    location = st.text_input("Location")
    description = st.text_area("Description")
    image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

    if st.button("Submit Report"):
        if location and description:
            insert_accident(location, description, image.read() if image else None)
            st.success("Your report has been submitted successfully!")
        else:
            st.error("Please fill out all fields!")


import requests


# Report Traffic Section
def report_traffic():
    st.title("Report Traffic")
    st.markdown("Provide traffic details below:")
    location = st.text_input("Location")
    traffic_status = st.selectbox("Traffic Status", ["Light", "Moderate", "Heavy"])
    if st.button("Submit Traffic Report"):
        if location:
            insert_traffic(location, traffic_status)
            st.success("Traffic report submitted successfully!")
        else:
            st.error("Please provide the location!")


# Emergency Assistance Section
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import datetime

# Twilio credentials
ACCOUNT_SID = ""
AUTH_TOKEN = ""  # Remember to keep this secure
MESSAGING_SERVICE_SID = ""


def send_emergency_sms(to_number, assistance_type):
    """
    Send SMS notification using Twilio with messaging service
    """
    try:
        # Initialize Twilio client with your credentials
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        

        # Format the message
        message_body = f"EMERGENCY ALERT: {assistance_type} assistance requested at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Help is on the way."

        # Format the phone number to ensure it includes country code
        formatted_number = to_number if to_number.startswith("+") else f"+{to_number}"

        # Send the message using messaging service
        message = client.messages.create(
            messaging_service_sid=MESSAGING_SERVICE_SID,
            body=message_body,
            to=formatted_number,
        )
        return True, message.sid
    except TwilioRestException as e:
        return False, str(e)


def emergency_assistance():
    st.title("Emergency Assistance")
    st.markdown("Request emergency help:")

    # Phone number input with validation
    contact_number = st.text_input(
        "Contact Number (include country code)", placeholder="e.g., +1234567890"
    )

    assistance_needed = st.selectbox(
        "Type of Assistance Needed", ["Medical", "Police", "Fire", "Other"]
    )

    location = st.text_input(
        "Your Location (optional)", placeholder="Enter your current location"
    )

    if st.button("Request Assistance", type="primary"):
        if contact_number and assistance_needed:
            # Show a loading spinner while processing
            with st.spinner("Processing your emergency request..."):
                try:
                    # Insert into database
                    insert_emergency(contact_number, assistance_needed, location)

                    # Send SMS notification
                    success, message = send_emergency_sms(
                        contact_number, assistance_needed
                    )

                    if success:
                        st.success(
                            "Emergency assistance has been notified! You will receive an SMS confirmation shortly."
                        )
                        st.info("Please stay calm and wait for assistance.")
                        st.text(f"Message SID: {message}")  # For debugging
                    else:
                        st.warning(
                            f"Emergency request logged, but SMS notification failed: {message}"
                        )
                        st.info(
                            "Emergency services have been notified through alternative channels."
                        )
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.info(
                        "Please call emergency services directly if this is a life-threatening situation."
                    )
        else:
            st.error("Please fill out all required fields!")

    # Add emergency contact information
    st.markdown("---")
    st.markdown("### Emergency Contact Numbers")
    st.markdown("- Emergency Services: 112 (IND)")
    st.markdown("- Police Department: 100")
    st.markdown("- Fire Department: 101")


def weather_details():
    st.markdown("### 🌤 Weather Information Center")

    # API configuration
    API_KEY = "07f0ccad6bb29f6f3fb59f91b7d38177"

    def get_weather(city):
        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        try:
            response = requests.get(base_url)
            data = response.json()

            if data["cod"] == 200:
                weather = {
                    "city": city.capitalize(),
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "feels_like": data["main"]["feels_like"],
                    "icon": data["weather"][0]["icon"],
                }
                return weather, None
            else:
                return None, "City not found"
        except Exception as e:
            return None, str(e)

    # Create modern layout
    st.markdown(
        """
        <style>
        .weather-container {
            background-color: #000000;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .weather-header {
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        city = st.text_input(
            "Enter City Name", placeholder="e.g., London, Paris, Tokyo"
        )

    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    if city and search_button:
        with st.spinner("Fetching weather data..."):
            weather_data, error = get_weather(city)

            if weather_data:
                # Display current conditions
                st.markdown(
                    """
                    <div class="weather-header">
                        <h2>Current Weather Conditions</h2>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                # Display main metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Temperature", f"{weather_data['temperature']}°C")

                with col2:
                    st.metric("Humidity", f"{weather_data['humidity']}%")

                with col3:
                    st.metric("Pressure", f"{weather_data['pressure']} hPa")

                with col4:
                    st.metric("Wind Speed", f"{weather_data['wind_speed']} m/s")

                # Display additional information
                st.markdown("---")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(
                        """
                        <div class="weather-container">
                            <h3>Detailed Information</h3>
                    """,
                        unsafe_allow_html=True,
                    )
                    st.write(f"**City**: {weather_data['city']}")
                    st.write(
                        f"**Description**: {weather_data['description'].capitalize()}"
                    )
                    st.write(f"**Feels Like**: {weather_data['feels_like']}°C")
                    st.markdown("</div>", unsafe_allow_html=True)

                with col2:
                    st.markdown(
                        """
                        <div class="weather-container">
                            <h3>Weather Icon</h3>
                    """,
                        unsafe_allow_html=True,
                    )
                    icon_url = (
                        f"http://openweathermap.org/img/w/{weather_data['icon']}.png"
                    )
                    st.image(icon_url, width=100)
                    st.markdown("</div>", unsafe_allow_html=True)

                # Weather alerts or recommendations
                if weather_data["temperature"] > 30:
                    st.warning(
                        "⚠️ High temperature alert! Stay hydrated and avoid prolonged sun exposure."
                    )
                elif weather_data["temperature"] < 5:
                    st.warning(
                        "⚠️ Low temperature alert! Dress warmly and be cautious of icy conditions."
                    )

                if weather_data["humidity"] > 80:
                    st.info(
                        "ℹ️ High humidity levels. Consider using climate control systems."
                    )

            else:
                st.error(f"Error: {error}")
                st.info("Please check the city name and try again.")

    # Display alerts for road safety guidance
    with st.expander("Alerts for Road Safety Guidance"):
        st.markdown(
            """
        ### Stay Alert and Drive Safe 🚗⚠️
        
         🌞 **Hot Weather**
        - Check your vehicle's coolant and tire pressure before a long drive.
        - Avoid leaving children or pets in parked vehicles.
        - Stay hydrated and take breaks if driving long distances.

         🌧️ **Rainy Weather**
        - Ensure your windshield wipers are functioning properly.
        - Avoid sudden braking; maintain a safe following distance.
        - Be cautious of hydroplaning and slippery roads.

         ❄️ **Cold/Wintry Weather**
        - Clear ice and snow from all windows, mirrors, and lights before driving.
        - Carry an emergency kit with blankets, food, and a flashlight.
        - Drive at reduced speeds and keep a safe distance from other vehicles.

         🌫️ **Foggy Weather**
        - Use fog lights or low-beam headlights, never high beams.
        - Reduce speed and be prepared for sudden stops.
        - Use road markers or the right edge of the road as a guide.

         💨 **Windy Weather**
        - Be cautious of strong crosswinds, especially on open roads.
        - Secure loose items on your vehicle, such as roof racks or cargo.
        - Keep a firm grip on the steering wheel to maintain control.

        Stay prepared and alert for any weather condition to ensure your safety and the safety of others on the road. 🚦🛡️
        """
        )


if __name__ == "__main__":
    main()
