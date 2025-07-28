# Video Annotation

This Python script automates video analysis by extracting keyframes at regular intervals and using a local multimodal AI model running for instance in LMStudio to generate detailed annotations for each frame. The final output is a structured CSV file, perfect for data analysis, content logging, or creating video summaries.

This project was kickstarted with the help of Google Gemini.

## Usage

Clone from git and run `uv sync` to set up the virtual environment and install the required packages.
 
```
usage: uv run main.py [-h] -v VIDEO -m MODEL [-i INTERVAL] [-u API_URL]
```

## Output File

The script generates a CSV file in the same directory as your video. For a video named my_trip.mp4, the output will be my_trip.csv.

The table will have the following columns:

- timestamp: The timestamp of the keyframe in seconds.
- title: The generated title for the scene.
- caption: The one-sentence summary.
- scene_description: The detailed description of the scene.
- persons: A comma-separated list of people identified.
- objects: A comma-separated list of key objects.

# Further use

You can feed the video description to an LLM with the following prompt:

```
Please make a description of a video for me. The video has been taken by an amateuer videographer in the 1970s and is a super-8 home video without audio. Focus on the content of the video and describe what is going on from the beginning to end. I have an automated video annotation in a five seconds interval: 
...
```