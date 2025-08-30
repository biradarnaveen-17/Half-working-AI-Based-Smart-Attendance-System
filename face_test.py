import face_recognition
import cv2
import pickle

# Load encodings
with open("encodings.pickle", "rb") as f:
    known_encodings, known_names = pickle.load(f)

# Test image path (change this as needed)
test_image_path = "known_faces/naveen/1.jpg"

# Load test image
image = face_recognition.load_image_file(test_image_path)
rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Detect and encode
locations = face_recognition.face_locations(rgb_image)
encodings = face_recognition.face_encodings(rgb_image, locations)

# Draw results
for encoding, location in zip(encodings, locations):
    matches = face_recognition.compare_faces(known_encodings, encoding)
    name = "Unknown"

    if True in matches:
        first_match = matches.index(True)
        name = known_names[first_match]

    top, right, bottom, left = location
    cv2.rectangle(rgb_image, (left, top), (right, bottom), (0, 255, 0), 2)
    cv2.putText(rgb_image, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Show output
cv2.imshow("Result", cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
cv2.waitKey(0)
cv2.destroyAllWindows()
