import cv2
import os

def extract_frames(video_path, output_dir, step=30):
    """
    Extract frames from a video file.
    video_path: path to the video
    output_dir: folder to save images
    step: grab a frame every N frames
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % step == 0:
            filename = os.path.join(output_dir, f"frame_{saved_count:04d}.jpg")
            cv2.imwrite(filename, frame)
            saved_count += 1
        frame_count += 1
    cap.release()

# Example usage
extract_frames("drone_video.mp4", "frames/", step=60)  # save one frame every 60 frames (~2 sec if 30fps)
