import os
import cv2
import face_recognition
import pickle

# Load encodings
with open("encodings.pickle", "rb") as f:
    known_encodings, known_names = pickle.load(f)

# Path to test folder
TEST_DIR = "known_faces"

for name in os.listdir(TEST_DIR):
    person_dir = os.path.join(TEST_DIR, name)
    if not os.path.isdir(person_dir):
        continue

    for filename in os.listdir(person_dir):
        filepath = os.path.join(person_dir, filename)

        # Load image
        image = face_recognition.load_image_file(filepath)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect and encode
        locations = face_recognition.face_locations(rgb_image)
        encodings = face_recognition.face_encodings(rgb_image, locations)

        for encoding, location in zip(encodings, locations):
            matches = face_recognition.compare_faces(known_encodings, encoding)
            label = "Unknown"

            if True in matches:
                first_match = matches.index(True)
                label = known_names[first_match]

            top, right, bottom, left = location
            cv2.rectangle(rgb_image, (left,_
