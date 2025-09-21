import cv2
import os
import numpy as np

def extract_frames(video_path, output_dir, num_frames=10):
    """
    Extract a fixed number of evenly spaced frames from a video.
    
    video_path: path to the video
    output_dir: folder to save images
    num_frames: how many frames to extract total
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        print(f"⚠️ Could not read {video_path}")
        return

    # pick evenly spaced frame indices
    frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

    saved_count = 0
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        filename = os.path.join(
            output_dir, f"{os.path.basename(video_path)}_frame_{saved_count:04d}.jpg"
        )
        cv2.imwrite(filename, frame)
        saved_count += 1

    cap.release()
    print(f"✅ Extracted {saved_count} frames from {os.path.basename(video_path)}")


# Process ALL videos in data/videos/
videos_dir = "backend/data/videos/"
frames_dir = "backend/data/frames/"

for video in os.listdir(videos_dir):
    if video.lower().endswith(".mp4"):
        extract_frames(os.path.join(videos_dir, video), frames_dir, num_frames=10)
