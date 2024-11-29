import json
from typing import List
from pydantic import BaseModel
from openai import OpenAI

OPENAI_API_KEY = "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"

# Define the JSON structure for the separate instruction blocks of ELAM
class BaseTask(BaseModel):
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

class ChecklistItem(BaseModel):
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


def instruction_basic_json_2_ELAM_flowchart_json(instruction_basic_json_path, elam_flowchart_json_path):
    print(f"\n### Start converting basic instruction JSON to final ELAM flowchart JSON ###")
    
    with open(instruction_basic_json_path, 'r') as file:
        instruction_basic_json = json.load(file)
    print(f"Loaded basic instruction JSON from {instruction_basic_json_path}")
    

    # Initialize the OpenAI API client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Loop over the steps in the instruction JSON and process each one with the OpenAI API
    for instruction in instruction_basic_json['instructions']:
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


            ### BEMERKUNG:



            ### TRANSKTIPTION-JSON FÜR DIE ANALYSE:



            ### ZUSATZWISSEN -  KOMPLETTE ANLEITUNG:
            {instruction_basic_json}

            Sie haben eine Transkriptions-JSON mit einer kompletten Arbeitsanweisung, die jeweils Zeitstempel und gesprochenen Text enthalten, welcher mithilfe von whisper von einem Video extrahiert wurde.
            Bitte extrahiren sie jeden einzelnen Schritt der Arbeitsanweisung und führen sie die folgenden Schritte aus:
            1. Welche Art von Anweisung ist es? Es soll aus einer der folgenden Klassennamen gewählt werden: Manual, Scan, Tightening, Rivet, Smartlabel, Pick_to_Light, SmartTower, Info, ChecklistItem und in das Feld "type" eingetragen werden.
            2. Extrahieren Sie die Beschreibung des Arbeitsschritts. -> welcher dan in die jeweilige Anweisung unter "description" eingetragen wird.
            3. Einen Titel für die art der Anweisung erstellen -> welcher dan in die jeweilige Anweisung unter "name" eingetragen wird.
            3. Einen Titel für die Anweisung erstellen -> welcher dan in die jeweilige Anweisung unter "task" eingetragen wird.
            2. Überprüfen Sie, ob das Wort "Foto" im Text erwähnt wird:
            - Falls "Foto" erscheint, notieren Sie den Zeitstempel, an dem es erstmals in diesem Arbeitsschritt erwähnt wird.
            - Falls "Foto" nicht erwähnt wird, setzen Sie dieses Feld auf null.
            3. Geben Sie jede Arbeitsanweisung zurück mit:
            - Zeitstempeln für Beginn und Ende der jeweiligen Anweisung, welche in den Feldern "task_start_time" und "task_end_time" eingetragen werden.
            - Erstelle einen separaten Eintrag für den "Foto"-Zeitstempel, welcher auch null sein kann und schreibe es in das Feld "image_frame_time".

            Hier ist die zu analysierende Transkriptions-JSON:
            {instruction_basic_json}
            """


        # Structured API call to extract instructions
        completion = client.beta.chat.completions.parse(
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

        # Extract the parsed instructions
        instructions = [choice.message.parsed for choice in completion.choices]

    # Output the results as JSON
    return instructions



    elam_flowchart_json = {
        "steps": []
    }
    
    for step in instruction_basic_json["steps"]:
        elam_flowchart_json["steps"].append({
            "description": step["description"],
            "start_time": step["start_time"],
            "end_time": step["end_time"],
            "photo_timestamp": step["photo_timestamp"]
        })
    
    with open(elam_flowchart_json_path, "w") as json_file:
        json.dump(elam_flowchart_json, json_file, indent=4)
        
    return elam_flowchart_json



