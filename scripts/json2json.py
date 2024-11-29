import json
from typing import List, Union
from pydantic import BaseModel
from openai import OpenAI
import os
from tqdm import tqdm

OPENAI_API_KEY = "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"

# Define the JSON structure for the separate instruction blocks of ELAM
class BaseTask(BaseModel):
    id: int
    name: str
    task: str
    description: str
    image_uri: str

class Manual(BaseTask):
    pass

class Scan(BaseTask):
    pass

class Tightening(BaseTask):
    count: int
    program: int

class Rivet(BaseTask):
    count: int
    program: int

class Smartlabel(BaseTask):
    duretiongui: int
    targetnumber: int

class Pick_to_Light(BaseTask):
    count: int

class SmartTower(BaseTask):
    count: int

class Info(BaseModel):
    durationgui: int

class Checklist(BaseTask):
    checklist: List['ChecklistItem']

class ChecklistItem(BaseTask):
    id: int
    question: str
    correctAnswer: str


class InstructionStep(BaseModel):
    type: str
    count: int
    program: int
    duretiongui: int
    targetnumber: int
    id: int
    question: str
    correctAnswer: str

class Instruction(BaseModel):
    instructions: List[InstructionStep]


def predict_instruction_type(instruction_text):

    # Initialize the OpenAI API client
    client = OpenAI(api_key=OPENAI_API_KEY)

    system_prompt = "Sie assistieren bei einer interpretation einer Arbeitsanweisung und sollen die Art der Anweisung bestimmen. Da sie spezialisiert sind für die Bossard ELAM software sollen sie die Anweisung in eine der folgenden Kategorien einordnen: Manual, Scan, Tightening, Rivet, Smartlabel, Pick_to_Light, SmartTower, Info, ChecklistItem."
    user_prompt = f"""
    Ich gebe Ihnen eine Anweisung, und Sie sollen vorhersagen, um welche Art von Anweisung es sich handelt.
    Die möglichen Anweisungstypen sind:
    Manual, Scan, Tightening, Rivet, Smartlabel, Pick_to_Light, SmartTower, Info, ChecklistItem
    
    Anweisung: "{instruction_text}"
    
    Bitte geben Sie nur die Art der Anweisung an (z.B. 'Scan', 'Manual', etc.).

    Falls Sie nicht sicher sind, geben Sie 'Unsicher' an.
    """

    # Call to the OpenAI API to predict the instruction type
    response = client.chat.completions.create(
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
        ]
    )

    # Extract and return the response text (which should be the instruction type)
    instruction_type = response.choices[0].message.content
    return instruction_type


def instruction_basic_json_2_instruction_advanced_json(instruction_basic_json_path, instruction_advanced_json_path):
    print(f"\n### Start converting basic instruction JSON to advanced JSON with different types of instructions ###")
    
    with open(instruction_basic_json_path, 'r') as file:
        instruction_basic_json = json.load(file)
    print(f"Loaded basic instruction JSON from {instruction_basic_json_path}")
    

    # Initialize the OpenAI API client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Empty list to store the parsed instructions
    instructions = []
    
    # Create a dictionary to map instruction type strings to their respective classes
    instruction_type_to_class = {
        "Manual": Manual,
        "Scan": Scan,
        "Tightening": Tightening,
        "Rivet": Rivet,
        "Smartlabel": Smartlabel,
        "Pick_to_Light": Pick_to_Light,
        "SmartTower": SmartTower,
        "Info": Info,
        "ChecklistItem": ChecklistItem,
    }

    # Loop over the steps in the instruction JSON and process each one with the OpenAI API
    for instruction in tqdm(instruction_basic_json['instructions']):

        # Predict the instruction type
        instruction_text = instruction['text']
        # print(f"\nPredicting instruction type for: {instruction_text}")
        instruction_type = predict_instruction_type(instruction_text)
        # print(f"Predicted instruction type: {instruction_type}")
        if instruction_type == "Unsicher":
            instruction_type = "Manual"
            print(f"Defaulting to Manual instruction type")



        # Define the system and user prompts for the API call
        system_prompt = "Sie sind ein Assistent, der Videotranskriptionsdaten verarbeitet, die in Anweisungen im JSON-Format umgewandelt werden sollen."
        user_prompt = f"""### KONTEXRT:
            Du bekommst ein einzelner Schritt einer Arbeitsanweisung und sollst herausfinden was für ein Type von Anweisung es ist, die Beschreibung des Arbeitsschritts verbessern und einen Titel für die Anweisung erstellen. Auch sollst du abhängig vom gewählten Type von Anweisung, spezifische Informationen extrahieren und eintragen.

            ### AUFGABE:
            1. Welche Art von Anweisung ist es? Es soll aus einer der folgenden Klassennamen gewählt werden: Manual, Scan, Tightening, Rivet, Smartlabel, Pick_to_Light, SmartTower, Info, ChecklistItem und in das Feld "type" eingetragen werden.
            2. Extrahiere die attribute die alle Anweisungen gemeinsam haben:
                - class BaseTask(BaseModel):
                    name: str (Titel für die Anweisung)
                    task: str (Titel für die Art der Anweisung)
                    description: str (Optimierte Beschreibung des Arbeitsschritts)
                    image_uri: str (Pfad zum Bild des Arbeitsschritts, falls vorhanden, sonst None)
            3. Extrahiere die spezifischen Informationen für die jeweilige Anweisung:
                - class Manual(BaseTask):
                    pass (keine spezifischen Informationen)
                - class Scan(BaseTask):
                    pass (keine spezifischen Informationen)
                - class Tightening(BaseTask):
                    count: int (Anzahl der Bauteile (z.B. Schrauben))
                    program: int (Programmnummer, falls erwähnt, sonst "auto")
                - class Rivet(BaseTask):
                    count: int (Anzahl der Bauteile (z.B. Nieten))
                    program: int (Programmnummer, falls erwähnt, sonst "auto")
                - class Smartlabel(BaseTask):
                    duretiongui: int (Dauer in Sekunden, die das GUI-Element angezeigt wird)
                    targetnumber: int (Zielnummer, falls erwähnt, sonst None)
                - class Pick_to_Light(BaseTask):
                    count: int (Anzahl der Bauteile (z.B. Schrauben))
                - class SmartTower(BaseTask):
                    count: int (Anzahl der Bauteile (z.B. Schrauben))
                - class Info(BaseModel):
                    durationgui: int (Dauer in Sekunden, die das GUI-Element angezeigt wird)
                - class ChecklistItem(BaseModel):
                    id: int (ID der Checkliste, Nummer der aufgabe in der Checkliste, oft mehrere Punkte in einer Checkliste. Ist aus dem Kontext des Zusatzwissens zu entnehmen)
                    question: str () (Fragestellung/Aufgabe der Checklisten-Aufgabe)
                    correctAnswer: str (Korrekte Antwort auf die Fragestellung/Aufgabe der Checklisten-Aufgabe)


            ### INSTRUCTION WELCHE ANALYSIERT WERDEN SOLL:
            {instruction}


            ### ZUSATZWISSEN -  KOMPLETTE ANLEITUNG:
            {instruction_basic_json}
            """


        # Structured API call to extract instructions
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
            response_format=instruction_type_to_class[instruction_type]
        )

        # Append the parsed instruction to the list
        instructions.append(json.loads(response.choices[0].message.content))



    print(f"Converted {len(instructions)} basic instructions to advanced instructions")

    # Save the parsed instructions to a new JSON file
    os.makedirs(os.path.dirname(instruction_advanced_json_path), exist_ok=True)
    with open(instruction_advanced_json_path, 'w') as file:
        json.dump(instructions, file, indent=4)
    print(f"Saved advanced instruction JSON to {instruction_advanced_json_path}")

    # Output the results as JSON
    return instructions




