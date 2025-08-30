import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import os
import face_recognition
import numpy as np
from datetime import datetime
import mysql.connector
import queue
import time

# -----------------------------
# MySQL Connection with error handling
# -----------------------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Enter your MySQL password
            database="attendance_system",
            autocommit=True
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error connecting to database: {err}")
        return None

# -----------------------------
# Face recognition setup
# -----------------------------
known_faces_dir = r"C:\Users\NAVEEN\Desktop\face_project\known_faces"
known_encodings = []
known_names = []

def load_known_faces():
    global known_encodings, known_names
    known_encodings = []
    known_names = []
    
    if not os.path.exists(known_faces_dir):
        os.makedirs(known_faces_dir)
        print(f"Created directory: {known_faces_dir}")
        return
    
    for person_name in os.listdir(known_faces_dir):
        person_folder = os.path.join(known_faces_dir, person_name)
        if not os.path.isdir(person_folder):
            continue
        for image_name in os.listdir(person_folder):
            image_path = os.path.join(person_folder, image_name)
            try:
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                if len(encodings) > 0:
                    known_encodings.append(encodings[0])
                    known_names.append(person_name)
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
    
    print(f"✅ Loaded {len(known_encodings)} known faces.")

load_known_faces()

# -----------------------------
# Global variables
# -----------------------------
cap = None
is_camera_running = False
frame_queue = queue.Queue(maxsize=2)
processed_frame_queue = queue.Queue(maxsize=2)
multi_frame_count = {}
threshold = 0.5  # Face distance threshold
frames_required = 3  # Multi-frame verification

# -----------------------------
# Modern Tkinter Window
# -----------------------------
root = tk.Tk()
root.title("AI Attendance System")
root.geometry("1200x800")
root.configure(bg='#f5f5f5')

# Set style
style = ttk.Style()
style.theme_use('clam')

# Configure colors
style.configure('Title.TLabel', background='#2c3e50', foreground='white', font=('Segoe UI', 18, 'bold'))
style.configure('Header.TFrame', background='#2c3e50')
style.configure('Card.TFrame', background='white', relief='raised', borderwidth=1)
style.configure('Card.TLabel', background='white', foreground='#2c3e50', font=('Segoe UI', 10))
style.configure('Primary.TButton', background='#3498db', foreground='white', font=('Segoe UI', 10, 'bold'))
style.configure('Secondary.TButton', background='#95a5a6', foreground='white', font=('Segoe UI', 10, 'bold'))
style.configure('Success.TButton', background='#2ecc71', foreground='white', font=('Segoe UI', 10, 'bold'))
style.configure('Treeview', font=('Segoe UI', 9))
style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))

# Header
header_frame = tk.Frame(root, bg='#2c3e50', height=70)
header_frame.pack(fill='x', side='top')
header_frame.pack_propagate(False)

title_label = tk.Label(header_frame, text="AI Attendance System", 
                      font=('Segoe UI', 20, 'bold'), fg='white', bg='#2c3e50')
title_label.pack(pady=20)

# Main content frame
main_frame = tk.Frame(root, bg='#f5f5f5', padx=20, pady=20)
main_frame.pack(fill='both', expand=True)

# Left panel for camera and controls
left_panel = tk.Frame(main_frame, bg='#f5f5f5')
left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))

# Camera frame with card style
camera_card = tk.Frame(left_panel, bg='white', relief='raised', borderwidth=1)
camera_card.pack(fill='both', expand=True, pady=(0, 10))

camera_header = tk.Frame(camera_card, bg='#3498db', height=40)
camera_header.pack(fill='x', side='top')
camera_header.pack_propagate(False)

camera_title = tk.Label(camera_header, text="Live Camera Feed", 
                       font=('Segoe UI', 12, 'bold'), fg='white', bg='#3498db')
camera_title.pack(pady=8)

camera_label = tk.Label(camera_card, bg='#34495e')
camera_label.pack(padx=10, pady=10)

# Control buttons frame
control_frame = tk.Frame(left_panel, bg='#f5f5f5')
control_frame.pack(fill='x', pady=10)

# Right panel for attendance table
right_panel = tk.Frame(main_frame, bg='#f5f5f5')
right_panel.pack(side='right', fill='both', expand=True, padx=(10, 0))

# Attendance card
attendance_card = tk.Frame(right_panel, bg='white', relief='raised', borderwidth=1)
attendance_card.pack(fill='both', expand=True)

attendance_header = tk.Frame(attendance_card, bg='#2c3e50', height=40)
attendance_header.pack(fill='x', side='top')
attendance_header.pack_propagate(False)

attendance_title = tk.Label(attendance_header, text="Attendance Records", 
                           font=('Segoe UI', 12, 'bold'), fg='white', bg='#2c3e50')
attendance_title.pack(pady=8)

# Table frame with scrollbars
table_frame = tk.Frame(attendance_card, bg='white')
table_frame.pack(fill='both', expand=True, padx=10, pady=10)

# Add scrollbars
vsb = ttk.Scrollbar(table_frame, orient="vertical")
vsb.pack(side='right', fill='y')

hsb = ttk.Scrollbar(table_frame, orient="horizontal")
hsb.pack(side='bottom', fill='x')

# Attendance table
columns = ("ID", "Name", "Date", "Time")
tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                   yscrollcommand=vsb.set, xscrollcommand=hsb.set)

vsb.config(command=tree.yview)
hsb.config(command=tree.xview)

# Configure columns
tree.column("ID", width=50, anchor='center')
tree.column("Name", width=150, anchor='w')
tree.column("Date", width=100, anchor='center')
tree.column("Time", width=100, anchor='center')

for col in columns:
    tree.heading(col, text=col)

tree.pack(fill='both', expand=True)

# Status bar
status_frame = tk.Frame(root, bg='#ecf0f1', height=30)
status_frame.pack(fill='x', side='bottom')
status_frame.pack_propagate(False)

status_label = tk.Label(status_frame, text="Ready", font=('Segoe UI', 9), 
                       fg='#7f8c8d', bg='#ecf0f1', anchor='w')
status_label.pack(side='left', padx=10)

face_count_label = tk.Label(status_frame, text=f"Known Faces: {len(known_encodings)}", 
                           font=('Segoe UI', 9), fg='#7f8c8d', bg='#ecf0f1', anchor='e')
face_count_label.pack(side='right', padx=10)

# -----------------------------
# Update Attendance Table
# -----------------------------
def update_table():
    try:
        for row in tree.get_children():
            tree.delete(row)
            
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance ORDER BY date DESC, time DESC")
            rows = cursor.fetchall()
            for row in rows:
                tree.insert("", tk.END, values=row)
            cursor.close()
            conn.close()
            status_label.config(text="Attendance records updated")
    except Exception as e:
        status_label.config(text=f"Error updating table: {str(e)}")
        print(f"Error updating table: {e}")

# -----------------------------
# Camera and Face Processing Threads
# -----------------------------
def initialize_camera():
    global cap
    try:
        if cap is None:
            cap = cv2.VideoCapture(0)
            # Set lower resolution for better performance
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 15)
        return cap.isOpened()
    except Exception as e:
        status_label.config(text=f"Camera error: {str(e)}")
        return False

def camera_capture_thread():
    global is_camera_running
    
    if not initialize_camera():
        status_label.config(text="Camera not available")
        return
        
    while is_camera_running:
        try:
            ret, frame = cap.read()
            if ret:
                # Resize frame for faster processing
                frame = cv2.resize(frame, (320, 240))
                if frame_queue.full():
                    try:
                        frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                frame_queue.put(frame.copy())
            time.sleep(0.03)  # ~30 FPS
        except Exception as e:
            print(f"Camera capture error: {e}")
            time.sleep(0.1)
    
    # Release camera when thread stops
    if cap is not None:
        cap.release()

def face_processing_thread():
    while is_camera_running:
        try:
            # Get frame from queue with timeout
            frame = frame_queue.get(timeout=0.5)
            
            # Process faces
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(known_encodings, face_encoding)
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index] and face_distances[best_match_index] < threshold:
                        name = known_names[best_match_index]
                    else:
                        name = "Unknown"
                else:
                    name = "Unknown"

                # Multi-frame verification
                if name != "Unknown":
                    multi_frame_count[name] = multi_frame_count.get(name, 0) + 1
                    if multi_frame_count[name] >= frames_required:
                        # Insert into DB if not already marked today
                        today = datetime.now().date()
                        conn = get_db_connection()
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT * FROM attendance WHERE name=%s AND date=%s", (name, today))
                            if cursor.fetchone() is None:
                                now = datetime.now()
                                cursor.execute("INSERT INTO attendance (name, date, time) VALUES (%s, %s, %s)",
                                               (name, now.date(), now.time()))
                                conn.commit()
                                status_label.config(text=f"✅ Attendance marked for {name} at {now.strftime('%H:%M:%S')}")
                                update_table()
                            cursor.close()
                            conn.close()
                        multi_frame_count[name] = 0

                # Draw rectangle (scale back up for display)
                top, right, bottom, left = [coord * 2 for coord in face_location]
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, name, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            # Put processed frame in queue for display
            if processed_frame_queue.full():
                try:
                    processed_frame_queue.get_nowait()
                except queue.Empty:
                    pass
            processed_frame_queue.put(frame)
            
        except queue.Empty:
            # No frames to process, continue
            continue
        except Exception as e:
            print(f"Face processing error: {e}")
            time.sleep(0.1)

def update_camera_display():
    if not is_camera_running:
        return
        
    try:
        # Get processed frame from queue
        frame = processed_frame_queue.get_nowait()
        
        # Convert and display
        frame = cv2.resize(frame, (640, 480))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk
        camera_label.configure(image=imgtk)
    except queue.Empty:
        # No processed frames available, continue
        pass
    except Exception as e:
        print(f"Display error: {e}")
    
    # Schedule next update
    if is_camera_running:
        camera_label.after(30, update_camera_display)

def start_camera():
    global is_camera_running
    
    if is_camera_running:
        return
        
    is_camera_running = True
    
    # Start camera capture thread
    capture_thread = threading.Thread(target=camera_capture_thread, daemon=True)
    capture_thread.start()
    
    # Start face processing thread
    processing_thread = threading.Thread(target=face_processing_thread, daemon=True)
    processing_thread.start()
    
    # Start display update
    update_camera_display()

def stop_camera():
    global is_camera_running
    is_camera_running = False

# -----------------------------
# Register New Student with Modern UI
# -----------------------------
def register_student():
    name = simpledialog.askstring("Register Student", "Enter student name:")
    if not name:
        return

    student_folder = os.path.join(known_faces_dir, name)
    os.makedirs(student_folder, exist_ok=True)
    messagebox.showinfo("Info", "Click 'Capture' 3 times to save images for the student.")

    count = [0]  # mutable counter

    # Modern Tkinter window for camera capture
    cam_win = tk.Toplevel()
    cam_win.title(f"Capture Images for {name}")
    cam_win.geometry("800x600")
    cam_win.configure(bg='#f5f5f5')
    
    # Center the window
    cam_win.update_idletasks()
    x = (cam_win.winfo_screenwidth() // 2) - (800 // 2)
    y = (cam_win.winfo_screenheight() // 2) - (600 // 2)
    cam_win.geometry(f'800x600+{x}+{y}')
    
    # Header frame
    header_frame = tk.Frame(cam_win, bg='#2c3e50', height=80)
    header_frame.pack(fill='x', side='top')
    header_frame.pack_propagate(False)
    
    title_label = tk.Label(header_frame, text=f"Registering: {name}", 
                          font=('Segoe UI', 16, 'bold'), fg='white', bg='#2c3e50')
    title_label.pack(pady=20)
    
    # Main content frame
    content_frame = tk.Frame(cam_win, bg='#f5f5f5', padx=20, pady=20)
    content_frame.pack(fill='both', expand=True)
    
    # Instructions
    instruction_text = "Please look directly at the camera and ensure good lighting.\nClick 'Capture' 3 times from slightly different angles."
    instruction_label = tk.Label(content_frame, text=instruction_text, 
                                font=('Segoe UI', 10), fg='#34495e', bg='#f5f5f5', 
                                wraplength=500, justify='center')
    instruction_label.pack(pady=(0, 20))
    
    # Camera frame with border
    cam_container = tk.Frame(content_frame, bg='#bdc3c7', padx=2, pady=2)
    cam_container.pack(pady=(0, 20))
    
    cam_label = tk.Label(cam_container, bg='#34495e')
    cam_label.pack()
    
    # Progress indicator
    progress_frame = tk.Frame(content_frame, bg='#f5f5f5')
    progress_frame.pack(pady=(0, 20))
    
    progress_label = tk.Label(progress_frame, text="Progress: 0/3", 
                             font=('Segoe UI', 10, 'bold'), fg='#2c3e50', bg='#f5f5f5')
    progress_label.pack(side='left')
    
    progress_bars = []
    for i in range(3):
        bar = tk.Frame(progress_frame, width=20, height=5, bg='#bdc3c7', relief='sunken', bd=1)
        bar.pack(side='left', padx=2)
        progress_bars.append(bar)
    
    # Button frame
    button_frame = tk.Frame(content_frame, bg='#f5f5f5')
    button_frame.pack(pady=10)

    # Create a separate camera for registration
    reg_cap = cv2.VideoCapture(0)
    if not reg_cap.isOpened():
        messagebox.showerror("Error", "Cannot open camera for registration")
        cam_win.destroy()
        return

    def capture_frame():
        ret, frame = reg_cap.read()
        if ret and count[0] < 3:
            image_path = os.path.join(student_folder, f"{count[0]+1}.jpg")
            cv2.imwrite(image_path, frame)
            count[0] += 1
            
            # Update progress
            progress_label.config(text=f"Progress: {count[0]}/3")
            for i in range(count[0]):
                progress_bars[i].config(bg='#2ecc71')  # Green for completed
            
            print(f"Captured image {count[0]} for {name}")
            if count[0] == 3:
                reg_cap.release()
                cam_win.destroy()
                load_known_faces()
                face_count_label.config(text=f"Known Faces: {len(known_encodings)}")
                messagebox.showinfo("Success", f"Student {name} registered successfully!")

    # Modern styled button
    capture_btn = tk.Button(button_frame, text="CAPTURE IMAGE", command=capture_frame,
                           font=('Segoe UI', 10, 'bold'), bg='#3498db', fg='white',
                           activebackground='#2980b9', activeforeground='white',
                           relief='flat', padx=20, pady=10, cursor='hand2')
    capture_btn.pack()
    
    # Add hover effect
    def on_enter(e):
        capture_btn['background'] = '#2980b9'
        
    def on_leave(e):
        capture_btn['background'] = '#3498db'
        
    capture_btn.bind("<Enter>", on_enter)
    capture_btn.bind("<Leave>", on_leave)

    def update_cam():
        ret, frame = reg_cap.read()
        if ret:
            # Resize frame to fit better in the UI
            frame = cv2.resize(frame, (640, 480))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            cam_label.imgtk = imgtk
            cam_label.configure(image=imgtk)
        if cam_win.winfo_exists():
            cam_label.after(30, update_cam)

    update_cam()
    
    # Handle window closing
    def on_cam_win_close():
        reg_cap.release()
        cam_win.destroy()
    
    cam_win.protocol("WM_DELETE_WINDOW", on_cam_win_close)

# -----------------------------
# Manual Mark Present
# -----------------------------
def manual_mark():
    student = simpledialog.askstring("Manual Attendance", "Enter student name to mark present:")
    if student:
        try:
            now = datetime.now()
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO attendance (name, date, time) VALUES (%s, %s, %s)",
                               (student, now.date(), now.time()))
                conn.commit()
                cursor.close()
                conn.close()
                update_table()
                status_label.config(text=f"Manually marked {student} present at {now.strftime('%H:%M:%S')}")
                messagebox.showinfo("Success", f"{student} marked present at {now.strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark attendance: {str(e)}")

# -----------------------------
# Modern Buttons
# -----------------------------
def create_modern_button(parent, text, command, color='primary'):
    color_map = {
        'primary': ('#3498db', '#2980b9'),
        'secondary': ('#95a5a6', '#7f8c8d'),
        'success': ('#2ecc71', '#27ae60')
    }
    
    bg_color, active_bg = color_map.get(color, ('#3498db', '#2980b9'))
    
    btn = tk.Button(parent, text=text, command=command,
                   font=('Segoe UI', 10, 'bold'), bg=bg_color, fg='white',
                   activebackground=active_bg, activeforeground='white',
                   relief='flat', padx=15, pady=8, cursor='hand2')
    
    # Add hover effect
    def on_enter(e):
        btn['background'] = active_bg
        
    def on_leave(e):
        btn['background'] = bg_color
        
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn

# Create buttons
register_btn = create_modern_button(control_frame, "Register New Student", register_student, 'primary')
register_btn.pack(side='left', padx=5)

manual_btn = create_modern_button(control_frame, "Manual Mark Present", manual_mark, 'success')
manual_btn.pack(side='left', padx=5)

refresh_btn = create_modern_button(control_frame, "Refresh Attendance", update_table, 'secondary')
refresh_btn.pack(side='left', padx=5)

# -----------------------------
# Start
# -----------------------------
update_table()
start_camera()

# Handle window closing
def on_closing():
    stop_camera()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()