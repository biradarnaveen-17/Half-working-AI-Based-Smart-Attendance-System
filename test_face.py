import face_recognition

# Load image
image = face_recognition.load_image_file(
    r"C:\Users\NAVEEN\Desktop\face_project\known_faces\naveen\1.jpg"
)

# Encode face
encoding = face_recognition.face_encodings(image)

if len(encoding) > 0:
    print("✅ Face detected and encoding generated successfully!")
else:
    print("❌ No face found in the image.")
