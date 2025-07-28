import cv2
import base64
import os
import argparse
import json
import pandas as pd
from openai import OpenAI
from pathlib import Path
from tqdm import tqdm

system_prompt = """You are a video annotator specializing in describing keyframes from digitized Super-8 videos that are 40 to 50 years old. These videos capture memories and events without audio. Your task is to focus solely on the visual content of the images. Avoid any commentary on artistic style, lighting issues, or technical problems such as cuts and artifacts. Describe what is happening in the scene, the subjects involved, and the environment in a clear and objective manner."""


def get_frame_annotation(
    client: OpenAI, base64_image: str, model_name: str
) -> dict | None:
    """
    Sends a single frame to the multimodal AI model in LMStudio.

    Args:
        client: The OpenAI client configured for LMStudio.
        base64_image: The base64 encoded string of the frame.
        model_name: The identifier of the model loaded in LMStudio.

    Returns:
        A dictionary with the annotation data or None if an error occurs.
    """
    # This prompt asks the model to return a structured JSON object.
    prompt = """
    Analyze the provided image and return a clean JSON object with the following keys:
    - "title": A concise, catchy title for the scene (string).
    - "caption": A single-sentence summary of the main action or subject (string).
    - "scene_description": A detailed paragraph describing the scene, activities, and setting (string).
    - "persons": A list of short strings, describing each person visible. If none, return an empty list.
    - "objects": A list of short strings, identifying key objects in the scene. If none, return an empty list.

    Your response must be ONLY the JSON object, without any additional text or markdown formatting.
    """

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            max_tokens=1500,  # Adjust if descriptions are long
            temperature=0.7,
        )
        content = response.choices[0].message.content

        # Clean up potential markdown formatting from the model's response
        if content.startswith("```json"):  # type: ignore
            content = content[7:-4]  # type: ignore

        data = json.loads(content)  # type: ignore

        # Basic validation
        required_keys = ["title", "caption", "scene_description", "persons", "objects"]
        if not all(key in data for key in required_keys):
            print(f"⚠️ Warning: Model response missing required keys. Response: {data}")
            return None

        return data

    except json.JSONDecodeError:
        print(f"❌ Error: Failed to decode JSON from model response:\n{content}")
        return None
    except Exception as e:
        print(f"❌ An error occurred while communicating with the API: {e}")
        return None


def process_video(
    video_path: str, interval_seconds: int, api_url: str, model_name: str
):
    """
    Extracts keyframes from a video, gets annotations from an AI model,
    and saves the results to a CSV file.
    """
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found at '{video_path}'")
        return

    # Initialize the OpenAI client to connect to the LMStudio server
    try:
        client = OpenAI(
            base_url=api_url, api_key="lm-studio"
        )  # API key is not used by LMStudio but required by the library
        client.models.list()  # Test connection
    except Exception as e:
        print(f"❌ Error connecting to LMStudio at {api_url}. Is the server running?")
        print(f"   Details: {e}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ Error: Could not open video file.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_seconds = total_frames / fps

    print(
        f"🎬 Video Info:\n  - Path: {video_path}\n  - FPS: {fps:.2f}\n  - Duration: {duration_seconds:.2f}s"
    )
    print(f"🔍 Analyzing one frame every {interval_seconds} seconds.")

    all_annotations = []

    # Calculate the timestamps for keyframes
    timestamps = [
        i * interval_seconds for i in range(int(duration_seconds / interval_seconds))
    ]

    with tqdm(total=len(timestamps), desc="Analyzing Keyframes") as pbar:
        for timestamp_sec in timestamps:
            frame_id = int(timestamp_sec * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            ret, frame = cap.read()

            if not ret:
                continue

            # Encode frame to JPEG format in memory and then to base64
            _, buffer = cv2.imencode(".jpg", frame)
            base64_image = base64.b64encode(buffer).decode("utf-8")

            pbar.set_description(f"Analyzing frame at {timestamp_sec:.1f}s")
            annotation = get_frame_annotation(client, base64_image, model_name)

            if annotation:
                annotation["timestamp"] = round(timestamp_sec, 2)
                # Convert lists to comma-separated strings for clean CSV storage
                annotation["persons"] = ", ".join(annotation.get("persons", []))
                annotation["objects"] = ", ".join(annotation.get("objects", []))
                all_annotations.append(annotation)
                pbar.write(
                    f"  ✅ Annotated frame at {timestamp_sec:.1f}s. Title: {annotation['title']}: {annotation['caption']}"
                )
            else:
                pbar.write(
                    f"  ⚠️ Failed to get annotation for frame at {timestamp_sec:.1f}s."
                )

            pbar.update(1)

    cap.release()

    if not all_annotations:
        print("\nNo annotations were generated. Exiting.")
        return

    # Create a pandas DataFrame
    df = pd.DataFrame(all_annotations)
    column_order = [
        "timestamp",
        "title",
        "caption",
        "scene_description",
        "persons",
        "objects",
    ]
    df = df[column_order]

    # Save to CSV
    output_path = Path(video_path).with_suffix(".csv")
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n✨ Analysis complete! Results saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze a video by extracting keyframes and using a multimodal AI in LMStudio for annotation."
    )
    parser.add_argument(
        "-v", "--video", type=str, required=True, help="Path to the input video file."
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        required=True,
        help="Model identifier from LMStudio (e.g., 'llava-hf/llava-1.5-7b-hf'). Find this in the LMStudio server logs.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=5,
        help="Interval in seconds between keyframes. Default is 5.",
    )
    parser.add_argument(
        "-u",
        "--api_url",
        type=str,
        default="http://localhost:1234/v1",
        help="URL of the LMStudio server API. Default is http://localhost:1234/v1.",
    )

    args = parser.parse_args()

    process_video(
        video_path=args.video,
        interval_seconds=args.interval,
        api_url=args.api_url,
        model_name=args.model,
    )
