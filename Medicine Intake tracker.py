import streamlit as st
import pandas as pd
from datetime import datetime, time
import random
import json
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Medicine Intake Tracker",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #E8F4F8 0%, #B8E1F0 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .motivational-quote {
        background-color: #FFF3CD;
        padding: 1.5rem;
        border-left: 5px solid #FFC107;
        border-radius: 5px;
        font-style: italic;
        margin: 1rem 0;
        font-size: 1.1rem;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .emergency-box {
        background-color: #FFEBEE;
        padding: 1.5rem;
        border-left: 5px solid #F44336;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-message {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 5px;
        color: #2E7D32;
    }
    .warning-message {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 5px;
        color: #E65100;
    }
    .reminder-box {
        background-color: #E1F5FE;
        padding: 1.5rem;
        border-left: 5px solid #0288D1;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .notification-alert {
        background-color: #FFF9C4;
        padding: 1.5rem;
        border: 2px solid #FBC02D;
        border-radius: 10px;
        margin: 1rem 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []

if 'total_intake' not in st.session_state:
    st.session_state.total_intake = 0

if 'total_missed' not in st.session_state:
    st.session_state.total_missed = 0

# Initialize reminder settings with default times
if 'reminder_settings' not in st.session_state:
    st.session_state.reminder_settings = {
        'enabled': True,
        'morning_time': time(8, 0),  # 8:00 AM
        'afternoon_time': time(13, 0),  # 1:00 PM
        'night_time': time(19, 30),  # 7:30 PM
        'email_notifications': False,
        'sound_enabled': True
    }

if 'last_reminder_shown' not in st.session_state:
    st.session_state.last_reminder_shown = None

# Function to check if it's time for a reminder
def check_reminder():
    """Check if current time matches any reminder time"""
    if not st.session_state.reminder_settings['enabled']:
        return None, None
    
    current_time = datetime.now().time()
    current_hour_min = (current_time.hour, current_time.minute)
    
    morning = st.session_state.reminder_settings['morning_time']
    afternoon = st.session_state.reminder_settings['afternoon_time']
    night = st.session_state.reminder_settings['night_time']
    
    # Check if current time matches any reminder time (within 1 minute)
    if (morning.hour, morning.minute) == current_hour_min:
        return 'Morning', medicine_schedule['Morning']
    elif (afternoon.hour, afternoon.minute) == current_hour_min:
        return 'Afternoon', medicine_schedule['Afternoon']
    elif (night.hour, night.minute) == current_hour_min:
        return 'Night', medicine_schedule['Night']
    
    return None, None

# Function to get next reminder time
def get_next_reminder():
    """Get the next upcoming reminder"""
    current_time = datetime.now().time()
    
    morning = st.session_state.reminder_settings['morning_time']
    afternoon = st.session_state.reminder_settings['afternoon_time']
    night = st.session_state.reminder_settings['night_time']
    
    times = [
        (morning, 'Morning', medicine_schedule['Morning']),
        (afternoon, 'Afternoon', medicine_schedule['Afternoon']),
        (night, 'Night', medicine_schedule['Night'])
    ]
    
    # Find next reminder
    for reminder_time, period, medicines in times:
        if current_time < reminder_time:
            return period, reminder_time, medicines
    
    # If all times have passed, return tomorrow's first reminder
    return 'Morning', morning, medicine_schedule['Morning']

# Motivational quotes
motivational_quotes = [
    "You're doing the best you can, and that starts with taking your medicine. 💪",
    "Every pill you take is a step toward better health. Keep going! 🌟",
    "Your health is an investment, not an expense. Take your medicine today! 💊",
    "Small steps every day lead to big changes. Don't skip your medication! 🎯",
    "You deserve to feel your best. Take your medicine on time! ❤️",
    "Consistency is key. Your future self will thank you! 🌈",
    "Taking care of yourself is not selfish, it's essential. 🌺",
    "You're stronger than you think. Keep up with your medication! 💙"
]

# Medicine schedule
medicine_schedule = {
    'Morning': ['Metformin', 'Sulfonylureas'],
    'Afternoon': ['DPP-4 Inhibitors', 'SGLT2 Inhibitors'],
    'Night': ['Metformin', 'Thiazolidinediones']
}

# Sidebar menu
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2913/2913133.png", width=100)
    st.title("📋 Menu")
    
    menu_option = st.radio(
        "Navigate to:",
        ["🏠 Home", "📊 History", "⏰ Reminders", "🚨 Emergency Contact", "ℹ️ About"]
    )
    
    st.markdown("---")
    
    # User Info Box
    st.markdown("""
    <div class="info-box">
        <h4>👤 User Information</h4>
        <p><b>Name:</b> Dave</p>
        <p><b>GP:</b> Dr. Satish</p>
        <p><b>Condition:</b> Diabetic</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats
    st.markdown("### 📈 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Taken", st.session_state.total_intake)
    with col2:
        st.metric("❌ Missed", st.session_state.total_missed)

# Main content based on menu selection
if menu_option == "🏠 Home":
    # Check for active reminder
    reminder_period, reminder_medicines = check_reminder()
    
    # Header
    st.markdown('<h1 class="main-header">💊 Medicine Intake Tracker</h1>', unsafe_allow_html=True)
    st.markdown(f'<h3 style="text-align: center;">Hello Dave! Welcome to Your Health Journey</h3>', unsafe_allow_html=True)
    
    # Show reminder notification if it's time
    if reminder_period and reminder_medicines:
        st.markdown(f"""
        <div class="notification-alert">
            <h2 style="color: #F57C00; margin: 0;">🔔 MEDICATION REMINDER!</h2>
            <h3 style="margin: 10px 0;">It's time for your {reminder_period} medication, Dave!</h3>
            <p style="font-size: 1.2rem; margin: 10px 0;"><b>Please take:</b> {', '.join(reminder_medicines)}</p>
            <p style="margin: 5px 0;">⏰ Reminder set for: {st.session_state.reminder_settings[f'{reminder_period.lower()}_time'].strftime('%I:%M %p')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Play sound notification if enabled
        if st.session_state.reminder_settings['sound_enabled']:
            st.markdown("""
                <audio autoplay>
                    <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
                </audio>
            """, unsafe_allow_html=True)
    else:
        # Show next reminder info
        next_period, next_time, next_medicines = get_next_reminder()
        st.info(f"⏰ Next reminder: {next_period} at {next_time.strftime('%I:%M %p')} - {', '.join(next_medicines)}")
    
    # Random motivational quote
    st.markdown(f'<div class="motivational-quote">"{random.choice(motivational_quotes)}"</div>', unsafe_allow_html=True)
    
    # Medicine images
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2913/2913099.png", width=150)
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3209/3209265.png", width=150)
    with col3:
        st.image("https://cdn-icons-png.flaticon.com/512/2913/2913145.png", width=150)
    
    st.markdown("---")
    
    # Time selection
    st.subheader("⏰ What time is it, Dave?")
    time_of_day = st.selectbox(
        "Select the time period:",
        ["Morning", "Afternoon", "Night"],
        help="Choose when you're taking your medication"
    )
    
    # Display medicines for selected time
    medicines_to_take = medicine_schedule[time_of_day]
    
    st.info(f"**Time to take:** {', '.join(medicines_to_take)}")
    
    # Medicine intake confirmation
    st.markdown("### Did you take your medication?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Yes, I took it!", type="primary", use_container_width=True):
            # Record the intake
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.history.append({
                'Date & Time': timestamp,
                'Time of Day': time_of_day,
                'Medicines': ', '.join(medicines_to_take),
                'Status': 'Taken',
                'Notes': 'Medication taken on time'
            })
            st.session_state.total_intake += 1
            
            st.markdown('<div class="success-message">🎉 Great job, Dave! You took your medicine correctly. Keep going!</div>', unsafe_allow_html=True)
            st.balloons()
    
    with col2:
        if st.button("❌ No, I missed it", use_container_width=True):
            # Record the missed dose
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.history.append({
                'Date & Time': timestamp,
                'Time of Day': time_of_day,
                'Medicines': ', '.join(medicines_to_take),
                'Status': 'Missed',
                'Notes': 'Medication missed'
            })
            st.session_state.total_missed += 1
            
            st.markdown('<div class="warning-message">Don\'t give up, Dave! Good days are ahead. Remember to set a reminder for next time! ⏰</div>', unsafe_allow_html=True)
    
    # Medication reminder tips
    with st.expander("💡 Tips for Remembering Your Medication"):
        st.markdown("""
        - Set daily alarms on your phone
        - Use a pill organizer
        - Keep medications in a visible spot
        - Link taking pills to daily routines (e.g., brushing teeth)
        - Use medication reminder apps
        - Keep a medication diary
        """)

elif menu_option == "📊 History":
    st.markdown('<h1 class="main-header">📊 Medication History</h1>', unsafe_allow_html=True)
    
    if st.session_state.history:
        # Create DataFrame
        df = pd.DataFrame(st.session_state.history)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📋 Total Records", len(df))
        with col2:
            taken_count = len(df[df['Status'] == 'Taken'])
            st.metric("✅ Taken", taken_count)
        with col3:
            missed_count = len(df[df['Status'] == 'Missed'])
            st.metric("❌ Missed", missed_count)
        with col4:
            if len(df) > 0:
                compliance_rate = (taken_count / len(df)) * 100
                st.metric("📈 Compliance Rate", f"{compliance_rate:.1f}%")
        
        st.markdown("---")
        
        # Display data table
        st.subheader("📝 Detailed History")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status:",
                options=['Taken', 'Missed'],
                default=['Taken', 'Missed']
            )
        with col2:
            time_filter = st.multiselect(
                "Filter by Time of Day:",
                options=['Morning', 'Afternoon', 'Night'],
                default=['Morning', 'Afternoon', 'Night']
            )
        
        # Apply filters
        filtered_df = df[
            (df['Status'].isin(status_filter)) & 
            (df['Time of Day'].isin(time_filter))
        ]
        
        # Display table with color coding
        def highlight_status(row):
            if row['Status'] == 'Taken':
                return ['background-color: #E8F5E9'] * len(row)
            else:
                return ['background-color: #FFEBEE'] * len(row)
        
        styled_df = filtered_df.style.apply(highlight_status, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Download option
        st.download_button(
            label="📥 Download History as CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f'medication_history_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
        
        # Clear history option
        if st.button("🗑️ Clear All History", type="secondary"):
            if st.checkbox("Are you sure? This cannot be undone."):
                st.session_state.history = []
                st.session_state.total_intake = 0
                st.session_state.total_missed = 0
                st.rerun()
        
        # Motivational message based on performance
        st.markdown("---")
        if compliance_rate >= 80:
            st.success(f"🌟 Excellent work, Dave! You took your medicine {taken_count} times correctly. Keep up the fantastic work!")
        elif compliance_rate >= 60:
            st.info(f"👍 Good job, Dave! You took your medicine {taken_count} times. Let's aim even higher!")
        else:
            st.warning(f"💪 You took your medicine {taken_count} times. Don't give up, Dave! Every day is a new opportunity. Good days are ahead!")
    
    else:
        st.info("📭 No history available yet. Start tracking your medication intake from the Home page!")
        st.image("https://cdn-icons-png.flaticon.com/512/4076/4076478.png", width=200)

elif menu_option == "⏰ Reminders":
    st.markdown('<h1 class="main-header">⏰ Medication Reminders</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="reminder-box">
        <h3>📱 Set Your Daily Medication Reminders</h3>
        <p>Configure when you want to be reminded to take your medications. The app will alert you at your specified times!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enable/Disable Reminders
    st.markdown("### ⚙️ Reminder Settings")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        reminder_enabled = st.toggle(
            "Enable Medication Reminders",
            value=st.session_state.reminder_settings['enabled'],
            help="Turn on/off all medication reminders"
        )
        st.session_state.reminder_settings['enabled'] = reminder_enabled
    
    with col2:
        sound_enabled = st.toggle(
            "🔊 Sound Alerts",
            value=st.session_state.reminder_settings['sound_enabled'],
            help="Play a sound when reminder appears"
        )
        st.session_state.reminder_settings['sound_enabled'] = sound_enabled
    
    st.markdown("---")
    
    # Time Settings
    st.markdown("### 🕐 Set Reminder Times")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🌅 Morning")
        st.caption("Medicines: Metformin, Sulfonylureas")
        morning_time = st.time_input(
            "Morning Reminder",
            value=st.session_state.reminder_settings['morning_time'],
            key="morning_time_input",
            help="Set time for morning medication reminder"
        )
        st.session_state.reminder_settings['morning_time'] = morning_time
        st.success(f"Set for {morning_time.strftime('%I:%M %p')}")
    
    with col2:
        st.markdown("#### ☀️ Afternoon")
        st.caption("Medicines: DPP-4 Inhibitors, SGLT2 Inhibitors")
        afternoon_time = st.time_input(
            "Afternoon Reminder",
            value=st.session_state.reminder_settings['afternoon_time'],
            key="afternoon_time_input",
            help="Set time for afternoon medication reminder"
        )
        st.session_state.reminder_settings['afternoon_time'] = afternoon_time
        st.success(f"Set for {afternoon_time.strftime('%I:%M %p')}")
    
    with col3:
        st.markdown("#### 🌙 Night")
        st.caption("Medicines: Metformin, Thiazolidinediones")
        night_time = st.time_input(
            "Night Reminder",
            value=st.session_state.reminder_settings['night_time'],
            key="night_time_input",
            help="Set time for night medication reminder"
        )
        st.session_state.reminder_settings['night_time'] = night_time
        st.success(f"Set for {night_time.strftime('%I:%M %p')}")
    
    st.markdown("---")
    
    # Current Time and Next Reminder
    st.markdown("### 📅 Reminder Schedule")
    
    current_time = datetime.now()
    st.info(f"🕐 Current Time: {current_time.strftime('%I:%M:%S %p')}")
    
    # Display all reminders
    reminder_data = {
        'Time Period': ['Morning', 'Afternoon', 'Night'],
        'Reminder Time': [
            st.session_state.reminder_settings['morning_time'].strftime('%I:%M %p'),
            st.session_state.reminder_settings['afternoon_time'].strftime('%I:%M %p'),
            st.session_state.reminder_settings['night_time'].strftime('%I:%M %p')
        ],
        'Medications': [
            ', '.join(medicine_schedule['Morning']),
            ', '.join(medicine_schedule['Afternoon']),
            ', '.join(medicine_schedule['Night'])
        ],
        'Status': []
    }
    
    # Check status for each reminder
    current_time_obj = current_time.time()
    for period in ['Morning', 'Afternoon', 'Night']:
        reminder_time = st.session_state.reminder_settings[f'{period.lower()}_time']
        if current_time_obj < reminder_time:
            reminder_data['Status'].append('⏳ Upcoming')
        elif current_time_obj.hour == reminder_time.hour and current_time_obj.minute == reminder_time.minute:
            reminder_data['Status'].append('🔔 ACTIVE')
        else:
            reminder_data['Status'].append('✅ Completed')
    
    df_reminders = pd.DataFrame(reminder_data)
    st.dataframe(df_reminders, use_container_width=True, hide_index=True)
    
    # Next Reminder Info
    next_period, next_time, next_medicines = get_next_reminder()
    time_until = datetime.combine(datetime.today(), next_time) - datetime.combine(datetime.today(), current_time.time())
    
    if time_until.total_seconds() < 0:
        time_until = time_until + pd.Timedelta(days=1)
    
    hours = int(time_until.total_seconds() // 3600)
    minutes = int((time_until.total_seconds() % 3600) // 60)
    
    st.markdown(f"""
    <div class="reminder-box">
        <h3>⏰ Next Reminder</h3>
        <p><b>Period:</b> {next_period}</p>
        <p><b>Time:</b> {next_time.strftime('%I:%M %p')}</p>
        <p><b>Medications:</b> {', '.join(next_medicines)}</p>
        <p><b>Time Until:</b> {hours} hours and {minutes} minutes</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Additional Notification Settings
    st.markdown("### 🔔 Additional Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        snooze_duration = st.selectbox(
            "Snooze Duration (minutes)",
            [5, 10, 15, 30],
            index=1,
            help="How long to snooze a reminder"
        )
    
    with col2:
        reminder_window = st.selectbox(
            "Reminder Window (minutes before/after)",
            [0, 5, 10, 15],
            index=1,
            help="Show reminder within this time window"
        )
    
    # Save Settings Button
    if st.button("💾 Save Reminder Settings", type="primary", use_container_width=True):
        st.success("✅ Reminder settings saved successfully!")
        st.balloons()
    
    # Reset to Defaults
    if st.button("🔄 Reset to Default Times", use_container_width=True):
        st.session_state.reminder_settings['morning_time'] = time(8, 0)
        st.session_state.reminder_settings['afternoon_time'] = time(13, 0)
        st.session_state.reminder_settings['night_time'] = time(19, 30)
        st.rerun()
    
    st.markdown("---")
    
    # Tips Section
    with st.expander("💡 Tips for Effective Reminders"):
        st.markdown("""
        - **Consistency**: Set reminders for the same time each day
        - **Meal Times**: Align reminders with your regular meal times
        - **Routine**: Link medication times to daily activities
        - **Sound**: Keep sound alerts on if you're often busy
        - **Check-in**: Review your reminder times weekly and adjust as needed
        - **Backup**: Set additional phone alarms as backup reminders
        - **Weekend**: Consider different times for weekends if your schedule changes
        """)
    
    # Test Reminder
    if st.button("🧪 Test Reminder Alert"):
        st.markdown("""
        <div class="notification-alert">
            <h2 style="color: #F57C00; margin: 0;">🔔 TEST REMINDER!</h2>
            <h3 style="margin: 10px 0;">This is how your reminder will look, Dave!</h3>
            <p style="font-size: 1.2rem; margin: 10px 0;"><b>Sample Medication Alert</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.reminder_settings['sound_enabled']:
            st.info("🔊 Sound alert would play here if this were a real reminder!")

elif menu_option == "🚨 Emergency Contact":
    st.markdown('<h1 class="main-header">🚨 Emergency Contact Information</h1>', unsafe_allow_html=True)
    
    st.image("https://cdn-icons-png.flaticon.com/512/3004/3004458.png", width=150)
    
    st.markdown("""
    <div class="emergency-box">
        <h3>🏥 Emergency Numbers</h3>
        <p><b>Hospital Emergency:</b> <a href="tel:+911234567890">+91 123-456-7890</a></p>
        <p><b>Dr. Satish (GP):</b> <a href="tel:+919876543210">+91 987-654-3210</a></p>
        <p><b>Pharmacy 24/7:</b> <a href="tel:+911122334455">+91 112-233-4455</a></p>
        <p><b>Ambulance:</b> <a href="tel:108">108</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("⚠️ When to Seek Emergency Help")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Diabetic Emergency Signs:**
        - Blood sugar very high (>300 mg/dL)
        - Blood sugar very low (<70 mg/dL)
        - Confusion or unconsciousness
        - Severe nausea or vomiting
        - Difficulty breathing
        """)
    
    with col2:
        st.markdown("""
        **What to Do:**
        1. Call emergency number immediately
        2. Check blood sugar if possible
        3. Stay calm and don't panic
        4. Have someone stay with you
        5. Keep medication list handy
        """)
    
    st.markdown("---")
    
    st.subheader("📞 Quick Contact Form")
    with st.form("contact_form"):
        issue = st.text_area("Describe your concern:")
        urgency = st.select_slider(
            "Urgency Level:",
            options=["Low", "Medium", "High", "Emergency"]
        )
        submitted = st.form_submit_button("Send Alert")
        
        if submitted:
            if urgency == "Emergency":
                st.error("🚨 EMERGENCY: Please call 108 or your hospital immediately!")
            else:
                st.success("✅ Your message has been logged. Dr. Satish will contact you soon.")

else:  # About section
    st.markdown('<h1 class="main-header">ℹ️ About Medicine Intake Tracker</h1>', unsafe_allow_html=True)
    
    st.image("https://cdn-icons-png.flaticon.com/512/2785/2785482.png", width=200)
    
    st.markdown("""
    ### 💊 About This Application
    
    The **Medicine Intake Tracker** is designed to help you stay on top of your medication schedule and maintain better health management.
    
    #### 🎯 Features:
    - **Easy Tracking**: Record your medication intake with just one click
    - **History Management**: View and analyze your medication history
    - **Emergency Contacts**: Quick access to important phone numbers
    - **Motivational Support**: Daily quotes to keep you motivated
    - **Statistics**: Track your compliance rate and progress
    
    #### 📋 Your Current Medication Schedule:
    """)
    
    for time, medicines in medicine_schedule.items():
        st.markdown(f"**{time}:** {', '.join(medicines)}")
    
    st.markdown("""
    ---
    #### 💡 Tips for Best Results:
    - Use the app at the same time each day
    - Be honest about missed doses
    - Review your history regularly
    - Set reminders on your phone
    - Share your progress with your doctor
    
    ---
    #### 👨‍⚕️ Medical Disclaimer:
    This app is a tracking tool and does not replace professional medical advice. 
    Always consult with Dr. Satish or your healthcare provider for medical decisions.
    
    ---
    **Version:** 1.0  
    **Last Updated:** February 2026
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>💙 Take care of yourself, Dave. Your health matters! 💙</p>
        <p style='font-size: 0.9rem;'>Made with ❤️ for better health management</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-refresh every 30 seconds to check for reminders (only on Home page)
if menu_option == "🏠 Home" and st.session_state.reminder_settings['enabled']:
    st.markdown("""
        <script>
            setTimeout(function() {
                window.location.reload();
            }, 30000);
        </script>
    """, unsafe_allow_html=True)
    
    # Display refresh indicator
    st.caption("🔄 Auto-refreshing every 30 seconds to check for reminders...")
