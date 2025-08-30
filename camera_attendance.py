import cv2
import face_recognition
import os
import numpy as np
import csv
from datetime import datetime

# -----------------------------
# Step 1: Load known faces
# -----------------------------
known_faces_dir = r"C:\Users\NAVEEN\Desktop\face_project\known_faces"
known_encodings = []
known_names = []

for person_name in os.listdir(known_faces_dir):
    person_folder = os.path.join(known_faces_dir, person_name)
    if not os.path.isdir(person_folder):
        continue
    for image_name in os.listdir(person_folder):
        image_path = os.path.join(person_folder, image_name)
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) > 0:
            known_encodings.append(encodings[0])
            known_names.append(person_name)

print(f"✅ Loaded {len(known_encodings)} known faces.")

# -----------------------------
# Step 2: Connect to Laptop Camera
# -----------------------------
cap = cv2.VideoCapture(0)  # 0 = Laptop webcam

if not cap.isOpened():
    print("❌ Cannot open laptop camera")
    exit()
else:
    print("✅ Laptop camera connected successfully!")

# -----------------------------
# Step 3: Attendance CSV setup
# -----------------------------
csv_file = r"C:\Users\NAVEEN\Desktop\face_project\attendance.csv"

if not os.path.exists(csv_file):
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Time"])

# -----------------------------
# Step 4: Process video frames
# -----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break

    # Convert to RGB and ensure correct type
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_frame = rgb_frame.astype(np.uint8)

    # Detect faces
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = []

    if face_locations:
        try:
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        except Exception as e:
            print("❌ Face encoding failed:", e)
            face_encodings = []

    # -----------------------------
    # Process each face
    # -----------------------------
    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)

        threshold = 0.5  # distance threshold (tune 0.4–0.6)

        if matches[best_match_index] and face_distances[best_match_index] < threshold:
            name = known_names[best_match_index]
        else:
            name = "Unknown"

        # Mark attendance only for known faces
        if name != "Unknown":
            with open(csv_file, "r+") as f:
                existing_entries = [line.split(",")[0] for line in f.readlines()]
                if name not in existing_entries:
                    now = datetime.now().strftime("%H:%M:%S")
                    f.write(f"{name},{now}\n")
                    print(f"✅ Attendance marked for {name} at {now}")

        # Draw rectangle and label
        top, right, bottom, left = face_location
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Display the frame
    cv2.imshow("Attendance System - Laptop Camera", frame)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
