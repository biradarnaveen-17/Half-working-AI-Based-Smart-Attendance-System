import cv2

url = "http://192.168.1.80:4747/video"  # Your phone's IP Webcam URL
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("❌ Cannot open IP Webcam")
    exit()
else:
    print("✅ IP Webcam connected!")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break
    cv2.imshow("IP Webcam Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
