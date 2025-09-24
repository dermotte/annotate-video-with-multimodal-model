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

Alternative, longer prompt:

```
The following CSV data describes the visual content of an edited super-8 video roughly 40-50 years old. The first column gives the time stamp in seconds, the remaining columns give title, caption, description, persons, and objects in the respective frame based on automated analysis. Please summarize the CSV data and give me a description of the video (2 paragraphs). Then find scenes in the video based on the frame descriptions by grouping subsequent frames with similar descriptions. For each scene you detect, estimate the beginning and the duration. Then describe what is happening, including eventuall described objects, persons and interaction. Do not use emojis. Note that at the beginning if each video, there are a few frames without content, mostly sand colored and scratchy, that the automated analysis might have mistaken for actual content. Please ignore them, and skip that scene in the description.
...
```