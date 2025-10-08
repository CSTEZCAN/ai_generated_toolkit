import cv2
import os
from skimage.metrics import structural_similarity as ssim

# === CONFIG ===
INPUT_DIR = r"."
OUTPUT_DIR = os.path.join(INPUT_DIR, "slides_output")
SSIM_THRESHOLD = 0.75    # lower = more sensitive
SAMPLE_RATE = 1.0        # seconds between sampled frames
EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi", ".wmv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_slides(video_path):
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps < 1:
        fps = 25  # fallback if metadata is missing
    frame_jump = int(fps * SAMPLE_RATE)

    success, prev_frame = cap.read()
    if not success:
        print(f"[!] Cannot read {video_path}")
        return 0

    frame_idx = 0
    slide_idx = 1
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    # --- Save the very first slide immediately ---
    out_name = f"{base_name}_slide{slide_idx:03d}.jpg"
    out_path = os.path.join(OUTPUT_DIR, out_name)
    cv2.imwrite(out_path, prev_frame)
    print(f"[+] {out_name} (initial frame)")
    slide_idx += 1

    while True:
        # Jump ahead by N seconds worth of frames
        frame_idx += frame_jump
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (prev_gray.shape[1], prev_gray.shape[0]))
        score = ssim(prev_gray, gray)

        if score < SSIM_THRESHOLD:
            out_name = f"{base_name}_slide{slide_idx:03d}.jpg"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            cv2.imwrite(out_path, frame)
            print(f"[+] {out_name} (t={frame_idx/fps:.1f}s, SSIM={score:.3f})")
            slide_idx += 1
            prev_gray = gray
        else:
            prev_gray = gray

    cap.release()
    return slide_idx - 1


def batch_process():
    print(f"Scanning {INPUT_DIR} for videos...\n")
    total_slides = 0
    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith(EXTENSIONS):
            path = os.path.join(INPUT_DIR, file)
            print(f"=== Processing {file} ===")
            count = extract_slides(path)
            print(f" -> Extracted {count} slides\n")
            total_slides += count
    print(f"✅ Done. Total slides extracted: {total_slides}")
    print(f"Saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    batch_process()
