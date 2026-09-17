# Privacy Policy — Face Attendance System

**Effective date:** [set to the date you submit]

This privacy policy explains what Face Attendance System ("the app") does with
your information. The app is a fully **offline** application. It does not
connect to any network service, does not call any external API, and does not
send data anywhere.

## 1. What the app collects

- **Face images and embeddings.** When you register a student, the app captures
  several photos of a face from your camera, converts each into a numerical
  mathematical representation ("face embedding"), and stores only those numbers
  locally. The app does **not** store photos of faces.
- **Attendance records.** Student IDs, names, and attendance timestamps are
  stored in a local database.
- **Login credentials.** The app's admin username and password are stored
  locally, hashed with the PBKDF2 key-derivation function. Default credentials
  are `admin` / `admin` and can be changed in the app's Settings.

## 2. Where data is stored

All data (the local database, face embeddings, attendance records, and exports)
is stored **only on your device**, inside the app's per-user data folder
(`%LOCALAPPDATA%\FaceAttendanceSystem` or, for the Microsoft Store version, the
app's `LocalCache\Local` folder). Nothing is transmitted or uploaded.

## 3. Camera use

The app uses your **webcam** solely to detect and recognise faces for attendance
during a session you start manually. Camera frames are processed locally in real
time and are never recorded, transmitted, or stored beyond the numerical
embeddings you choose to save when registering a student.

## 4. No third parties

The app does not include advertising, analytics, tracking, or any third-party
network service. No personal data is shared with or sold to anyone.

## 5. Your control

- Registered students and their face data can be **deleted** at any time from
  the Students tab.
- Attendance records can be deleted by removing the app's data folder.
- Uninstalling the app removes the app and its per-user data.

## 6. Security

Data stays on your device, protected by your Windows account. We cannot access
your local data, and no server exists that could hold it.

## 7. Contact

For any privacy questions, contact [your email address here].