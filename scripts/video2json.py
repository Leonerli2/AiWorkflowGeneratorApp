from pydantic import BaseModel
from openai import OpenAI
import json
from typing import List, Union
import cv2
import os
from moviepy import VideoFileClip

OPENAI_API_KEY = "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"


class VideoPathHandler:
    def __init__(self, video_dir: str, audio_dir: str, transcription_with_timestamps_json_dir: str, instructions_with_timestamps_json_dir: str, instructions_basic_json_dir: str, instructions_advanced_json_dir: str, elam_json_dir: str, image_output_dir: str):
        self.video_dir = video_dir
        self.audio_dir = audio_dir
        self.transcription_with_timestamps_json_dir = transcription_with_timestamps_json_dir
        self.instructions_with_timestamps_json_dir = instructions_with_timestamps_json_dir
        self.instructions_basic_json_dir = instructions_basic_json_dir
        self.instructions_advanced_json_dir = instructions_advanced_json_dir
        self.elam_json_dir = elam_json_dir
        self.image_output_dir = image_output_dir

    def get_video_path(self, video_nr):
        return f"{self.video_dir}/video{video_nr}.mp4"
    
    def get_audio_path(self, video_nr):
        return f"{self.audio_dir}/audio{video_nr}.mp3"
    
    def get_transcription_with_timestamps_json_path(self, video_nr):
        return f"{self.transcription_with_timestamps_json_dir}/transcript{video_nr}.json"
    
    def get_instructions_with_timestamps_json_path(self, video_nr):
        return f"{self.instructions_with_timestamps_json_dir}/instructions{video_nr}.json"
    
    def get_instructions_basic_json_path(self, video_nr):
        return f"{self.instructions_basic_json_dir}/instructions_basic{video_nr}.json"
    
    def get_instructions_advanced_json_path(self, video_nr):
        return f"{self.instructions_advanced_json_dir}/instructions_advanced{video_nr}.json"
    
    def get_elam_json_path(self, video_nr):
        return f"{self.elam_json_dir}/elam{video_nr}.json"
    
    def get_image_output_dir(self, video_nr):
        return f"{self.image_output_dir}/video{video_nr}"

def video_transcription_with_timestamps_json_2_instructions_with_timestamps_json(transcription_with_timestamps_json_path, output_json_path, save_instructions=True):
    print("\n### Converting video transcription with timestamps to JSON with basic instructions...")

    # Load the JSON file
    with open(transcription_with_timestamps_json_path, 'r') as file:
        transcript_data = json.load(file)
        print(f"Loaded transcription data from {transcription_with_timestamps_json_path}")

   
    client = OpenAI(api_key = OPENAI_API_KEY)
    
    # Prompts
    system_prompt = "Sie sind ein Assistent, der Videotranskriptionsdaten verarbeitet, die in einzelnen Anweisungen im JSON-Format umgewandelt werden sollen." # Da es sich um eine erste extraktion handelt, sollen Sie die jeweilige Beschreibung des Arbeitsschritts so detailiert wie möglich angeben."
    user_prompt = f""" ### KONTEXRT:
        Sie haben eine Transkriptions-JSON mit einer kompletten Arbeitsanweisung, welches von einem Video mithilfe von whisper extrahiert wurde, welches nun die jeweiligen Zeitstempel und gesprochenen Text enthalten.
        Das JSON enthält eine komplette Arbeitsanweisung und muss in konkrete einzelne Arbeitsschritte aufgeteilt werden.

        ### AUFGABE:
        Bitte extrahiren sie jeden einzelnen Schritt der Arbeitsanweisung und führen sie dann die folgenden Schritte aus:
        1. Extrahieren Sie die Nummer des Arbeitsschritts. -> welcher dan in die jeweilige Anweisung unter "step" eingetragen wird.
        2. Extrahieren Sie die Beschreibung des Arbeitsschritts. -> welcher dan in die jeweilige Anweisung unter "text" eingetragen wird.
        2. Überprüfen Sie, ob das Wort "Foto" im Text erwähnt wird:
        - Falls "Foto" erscheint, notieren Sie den Zeitstempel, an dem es zuerst erwähnt wird.
        - Falls "Foto" nicht erwähnt wird, setzen Sie dieses Feld auf null.
        -> welcher dan in die jeweilige Anweisung unter "picture_time" eingetragen wird.
        3. Geben Sie jede Arbeitsanweisung zurück mit:
        - Zeitstempeln für Beginn und Ende der jeweiligen Anweisung, -> welcher dan in die jeweilige Anweisung unter "start_time" eingetragen wird.
        - Einem separaten Eintrag für den "Foto"-Zeitstempel oder null. -> welcher dan in die jeweilige Anweisung unter "photo_timestamp" eingetragen wird.

        ### BEMERKUNG:
        Da es sich um die erste Extraktion handelt, sollen die Arbeitsschritte so detailiert wie möglich angegeben werden! Es wird später nocheinmal reduziert und zusammengefasst. Es ist wichtig, dass folgendes in diesem Text enthalten ist:
        - was wird gemacht?
        - wird ein spezielles tool verwendet?
        - wird eine exakte Anzahl von Teilen erwähnt?

        ### TRANSKTIPTION-JSON FÜR DIE ANALYSE:
        Hier ist die zu analysierende komplette Transkriptions-JSON:

        {transcript_data}
        """
    
    class InstructionStep(BaseModel):
        step: int
        text: str
        picture_time: Union[float, None]
        start_time: float
        end_time: float
    
    class Instruction(BaseModel):
        instructions: List[InstructionStep]

    print("Calling OpenAI API...")
    text = transcript_data
    # Call OpenAI API
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt,
            }
        ],
        response_format=Instruction,  # Parse into the defined schema
    )
    
    # Convert the message content to JSON and store it
    instructions_json = json.loads(response.choices[0].message.content)
    if save_instructions:
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w") as json_file:
            json.dump(instructions_json, json_file, indent=4)
        print(f"Instructions saved to {output_json_path}")

    print("Instructions extracted successfully!")

    return instructions_json

def extract_frames(video_nr, video_path, instructions_json_path, output_dir):
    print(f"\n### Extracting frames from video {video_nr}...")

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # load json
    with open(instructions_json_path, 'r') as file:
        instructions_json = json.load(file)

    # Get the video's frame rate
    fps = cap.get(cv2.CAP_PROP_FPS)

    for idx, instruction in enumerate(instructions_json["instructions"]):

        end_time = instruction["end_time"]
        photo_time = instruction["picture_time"]

        if photo_time is not None:
            # print(f"Extracting frame for step {idx + 1}: {description}")
            time = photo_time
        else:  
            time = end_time


        # Calculate the frame number for each timestamp
        frame_number = int(time * fps)
        # Set the video position to the frame number
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        # Read the frame
        ret, frame = cap.read()

        if ret:
            # Save the frame as an image file)
            output_path = f"{output_dir}/instruction{video_nr}_{idx+1}.jpg"
            # Create the output directory if it does not exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cv2.imwrite(output_path, frame)
        else:
            print(f"Could not extract frame at {time}s")

    # Release the video capture object
    cap.release()

    print(f"Frames extracted successfully to {output_dir}/instructions{video_nr}")

def extract_audio(video_path, audio_output="speech.mp3"):
    print("\n### Extracting audio from video...")

    # Load the video file
    video = VideoFileClip(video_path)
    print(f"Loaded video file from {video_path}")
    
    # Extract the audio
    audio = video.audio
    
    # Write the audio file
    os.makedirs(os.path.dirname(audio_output), exist_ok=True)
    audio.write_audiofile(audio_output)
    print(f"Audio extracted successfully to {audio_output}")
    
    # Close the video file to free up resources
    video.close()

def audio_text_extraction_timestamps(audio_file_path, json_file_path = "src/transcript.json"):
    print("\n### Extracting text from audio with timestamps...")

    client = OpenAI(api_key = OPENAI_API_KEY)

    audio_file = open(audio_file_path, "rb")
    print(f"Loaded audio file from {audio_file_path}")

    transcript = client.audio.transcriptions.create(
    file=audio_file,
    model="whisper-1",
    response_format="verbose_json",
    timestamp_granularities=["word"]
    )
    # Store the transcript data in a JSON file
    os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
    with open(json_file_path, "w") as json_file:
        json.dump(transcript.model_dump(), json_file, indent=4)
    
    print(f"Transcript saved to {json_file_path}")
    return transcript.words

def instructions_with_timestamps_json_2_basic_instruction_json(video_nr, instructions_with_timestamps_json_path, output_json_path, images_dir, save_instructions=True):
    print("\n### Converting video transcription with timestamps to JSON with basic instructions...")

    # Load the JSON file
    with open(instructions_with_timestamps_json_path, 'r') as file:
        instruction_input = json.load(file)
    print(f"Loaded transcription data from {instructions_with_timestamps_json_path}")

    # Initialize the output JSON which is taking the instruction_input and delete "picture_time", "start_time", "end_time" for each instruction and add the image path instead on "image_uri"
    instruction_output = instruction_input
    for instruction in instruction_output["instructions"]:
        instruction.pop("picture_time", None)
        instruction.pop("start_time", None)
        instruction.pop("end_time", None)
        instruction["image_uri"] = f"{images_dir}/instruction{video_nr}_{instruction['step']}.jpg"

    if save_instructions:
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w") as json_file:
            json.dump(instruction_output, json_file, indent=4)
        print(f"Instructions saved to {output_json_path}")

    print("Instructions extracted successfully!")




