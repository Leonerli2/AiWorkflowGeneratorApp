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
    imagefilename: str

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

class Info(BaseTask):
    durationgui: int

class Checklist(BaseTask):
    checklist: List['ChecklistItem']

class ChecklistItem(BaseTask):
    id: int
    question: str
    correctAnswer: str


# class InstructionStep(BaseModel):
#     type: str
#     count: int
#     program: int
#     duretiongui: int
#     targetnumber: int
#     id: int
#     question: str
#     correctAnswer: str

# class Instruction(BaseModel):
#     instructions: List[InstructionStep]


def predict_instruction_type(instruction_text):

    # Initialize the OpenAI API client
    client = OpenAI(api_key=OPENAI_API_KEY)

    system_prompt = "Sie assistieren bei einer interpretation einer Arbeitsanweisung und sollen die Art der Anweisung bestimmen. Da sie spezialisiert sind für die Bossard ELAM software sollen sie die Anweisung in eine der folgenden Kategorien einordnen: Manual, Scan, Tightening, Rivet, Smartlabel, Pick_to_Light, SmartTower, Info, ChecklistItem."
    user_prompt = f"""
    Ich gebe Ihnen eine Anweisung, und Sie sollen vorhersagen, um welche Art von Anweisung es sich handelt.
    Die möglichen Anweisungstypen sind:
    Manual, Scan, Tightening, Rivet, Smartlabel, Pick_to_Light, SmartTower, Info, ChecklistItem
    
    ### ANWEISUNG, DIE ANALYSIERT WERDEN SOLL:
    {instruction_text}
    
    ### BEMERKUNGEN: 
    - Manual ist der standardmässige Anweisungstyp. Die Anderen Anweisungstypen werden eher selten vorkommen und müssen spezifisch erwähnt werden.
      Einzig wenn ein konkretes Tool bennant wird, wie z.B. Scanner oder Akkuschrauber, usw. 
    - Bitte geben Sie nur die Art der Anweisung an (z.B. 'Scan', 'Manual', etc.).
    - Falls Sie nicht sicher sind, geben Sie 'Unsicher' an.
    - Tightening sind wirklich nur SmartTools wie Akkuschrauber oder ähnliches gemeint, keine manuellen Schraubenzieher oder sonstiges.
    - Tightening soll nicht verwendet werden, wenn schrauben nur angesetzt (oder ähnliches) werden. Es muss wirklich ein Drehmoment oder eine Anzahl Umdrehungen erwähnt werden, sowie dass die Schrauben angezugen/festgezogen (oder ähnliches) werden.
    - Sobald die Anzahl von Bauteilen, welche entnommen werden sollen, erwähnt wird, ist es Pick_to_Light.
    - Fotos werden eigentlich nicht gemacht, diese Fotos sind einzig für die kreierung der Anweisungen. Nicht berücksichtigen für die Bemerkung und den Typen der Anweisung.

    ### WICHTIG:
    Bitte geben Sie nur die Art der Anweisung an und zwar eine der folgenden Kategorien:
    Manual, Scan, Tightening, Rivet, Smartlabel, Pick_to_Light, SmartTower, Info, ChecklistItem
    Es muss exakt so geschrieben werden, wie oben angegeben.
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
                    description: str (Beschreibung des Arbeitsschritts, kurz und bündig)
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
                - class Info(BaseTask):
                    durationgui: int (Dauer in Sekunden, die das GUI-Element angezeigt wird)
                - class ChecklistItem(BaseTask):
                    id: int (ID der Checkliste, Nummer der aufgabe in der Checkliste, oft mehrere Punkte in einer Checkliste. Ist aus dem Kontext des Zusatzwissens zu entnehmen)
                    question: str () (Fragestellung/Aufgabe der Checklisten-Aufgabe)
                    correctAnswer: str (Korrekte Antwort auf die Fragestellung/Aufgabe der Checklisten-Aufgabe)

                    
            ### BEMERKUNGEN:
            - Die Beschreibung muss nicht zu genau sein, sie soll den Arbeitsschritt beschreiben und nicht zu viel dazu erfinden. Die Beschreibung soll immer mit dem gesamten Kontext der Anweisung übereinstimmen und sinnvoll sein.
              Denke immer daran, dass es sich um eine Montageanleitung handelt. Somit werden viele Teile aus einem Behälter/Box genommen und irgendwo eingebaut. -> Du kannst es also sehr langweilig beschreiben mit "Nehme ein Teil aus dem Behälter und setze es ein." oder "Nehme ein Teil aus der Box und setze es ein."
            - Wenn nicht original erwähnt, dann lasse zusätzliche beschreibungen (wie bspw. vorsichtig, langsam, etc.) weg.
            - Fotos werden eigentlich nicht gemacht, diese Fotos sind einzig für die kreierung der Anweisungen. Nicht berücksichtigen für die Bemerkung und den Typen der Anweisung.



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


def get_type_id(task: str) -> str:
    if task == "Start":
        return "3b321cae-fa35-4919-81b8-35b36c967475"
    elif task == "Manual":
        return "631ca9e9-6a3b-4274-b890-b209790dca9c"
    elif task == "Scan":
        return "dc9df31b-c042-4055-b915-7257f2a397c9"
    elif task == "Tightening":
        return "083deae0-2901-4956-8322-7b75a55ce30b"
    elif task == "Rivet":
        return "82ad86ae-212b-48b3-9a06-7f3bba21bc79"
    elif task == "Smartlabel":
        return "45dce8f5-f566-41d7-8e9b-de8250290af0"
    elif task == "Pick_to_Light":
        return "ddb791b5-7395-4f13-883d-2f3efb05d1ba"
    elif task == "SmartTower":
        return "5d907caa-6aa5-47dc-882e-ec040e570bd4"
    elif task == "Info":
        return "fea138c5-fd5d-4c79-bcc7-e9525e405b42"
    elif task == "ChecklistItem":
        return "545c8959-7452-4f8e-8dcf-e098912f5082"
    else:
        return "631ca9e9-6a3b-4274-b890-b209790dca9c" # Default to Manual
    
def get_type_image_url(task: str) -> str:
    if task == "Start":
        return "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI1MCIgaGVpZ2h0PSI1MCIgdmlld0JveD0iMCAwIDQwIDQwLjAwMiI+PHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiByeD0iMjAiIGZpbGw9IiNmZmYiLz48cGF0aCBkPSJNMjA2NTUsMjM1OTNhMjAsMjAsMCwxLDEsMjAsMjBBMjAsMjAsMCwwLDEsMjA2NTUsMjM1OTNabTcuOTc3LTEyLjAyM0ExNywxNywwLDEsMCwyMDY3NSwyMzU3NiwxNi45LDE2LjksMCwwLDAsMjA2NjIuOTc5LDIzNTgwLjk3N1ptNy4xMzUsMy41MjUsMTUuMzg1LDguNS0xNS4zODUsOC41WiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTIwNjU1IC0yMzU3MykiIGZpbGw9IiM0ZGExNjciLz48L3N2Zz4="
    elif task == "Manual":
        return "data:image/svg+xml;base64,PHN2ZyBpZD0iQ2xpZW50X1RBRl9NYW51ZWxsIiBkYXRhLW5hbWU9IkNsaWVudCBUQUYgTWFudWVsbCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCI+CiAgPHJlY3QgaWQ9IlJlY2h0ZWNrXzExNTEiIGRhdGEtbmFtZT0iUmVjaHRlY2sgMTE1MSIgd2lkdGg9IjQ1IiBoZWlnaHQ9IjQ1IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSg3LjUgNy41KSIgZmlsbD0ibm9uZSIvPgogIDxwYXRoIGlkPSJQYXRoXzMxMjYiIGRhdGEtbmFtZT0iUGF0aCAzMTI2IiBkPSJNMjguOTcxLDQ3LjFhMTIuMDU4LDEyLjA1OCwwLDAsMS01LjM0Mi0xLjc4NEEzMy42ODcsMzMuNjg3LDAsMCwxLDE5LjMxNyw0Mi41QzE3LjMsNDAuOTMxLDEwLjA0NSwzMS41ODcsOC43OTQsMjkuOTMzbC0uMDExLS4wMTVhOC4xNjYsOC4xNjYsMCwwLDEtLjg5My0xLjY5MWMtLjY1OS0xLjc0OS0uMTg1LTIuNzY0LjMzLTMuMzA3QTMuMjM4LDMuMjM4LDAsMCwxLDkuOSwyMy45cS0uODU1LTEuMDMzLTEuMTI3LTEuNDMyQTUuOCw1LjgsMCwwLDEsNy43MSwxOS44ODJhMy4wNjEsMy4wNjEsMCwwLDEsLjg2NC0yLjU0MiwyLjcyOSwyLjcyOSwwLDAsMSwyLjAwOC0uOHEuMTE3LDAsLjIzNi4wMDhhNi4xNzIsNi4xNzIsMCwwLDEtMS4xOS0zLjU3MywyLjU0MiwyLjU0MiwwLDAsMSwuOTQ3LTEuODA2LDMuNywzLjcsMCwwLDEsMi4zNTItLjlBNC4zOSw0LjM5LDAsMCwxLDE2LjIsMTIuMDMxbC4wMTcuMDIxQTIuNCwyLjQsMCwwLDEsMTcsMTAuNDI1LDMuMzg4LDMuMzg4LDAsMCwxLDE5LjIyNyw5LjYsNC4zMTYsNC4zMTYsMCwwLDEsMjIuNSwxMS4yNTRjMS4xMzIsMS4yODMsNi41MzUsNy43NjYsOS42NzQsMTEuNTM4LS4yOTUtLjk1LS42MTItMS45NjktLjktMi44NjlhNS40LDUuNCwwLDAsMS0uMS0zLjU1OCwzLjAyOSwzLjAyOSwwLDAsMSwxLjk0Ni0xLjg0NCwyLjM3OCwyLjM3OCwwLDAsMSwuNzE3LS4xMDgsMy44MSwzLjgxLDAsMCwxLDIuMjg4LjlBNC42MTksNC42MTksMCwwLDEsMzcuNiwxNy4yNDRjLjIzOS42NDgsMS41MTUsNC40NDgsMi43OSw4LjM3MSwyLjQ1LDcuNTQzLDIuNDUsNy45ODUsMi40NSw4LjIsMCwuMDY0LDAsLjEzNiwwLC4yMTZhMTAuNzA2LDEwLjcwNiwwLDAsMS0xLjc2OSw2LjJjLTEuMjM5LDIuMDI0LTMuOTg0LDMuNzM5LTUuNTEsNC41ODJBMTcuNzQyLDE3Ljc0MiwwLDAsMSwyOS4zLDQ3LjA5MkMyOS4xOTEsNDcuMSwyOS4wODEsNDcuMSwyOC45NzEsNDcuMVpNOS45MjQsMjkuMDg3YzEuNjkzLDIuMjM2LDguNTIsMTAuOTQxLDEwLjI1OSwxMi4zLDEuOTEyLDEuNDksNi4yMSw0LjMwNyw4Ljc4OCw0LjMwNy4wNzYsMCwuMTUxLDAsLjIyMy0uMDA4YTE2LjYzMywxNi42MzMsMCwwLDAsNS42ODgtMi4xMTIsMTMuOTUxLDEzLjk1MSwwLDAsMCw0Ljk4OS00LjA4Myw5LjI1NCw5LjI1NCwwLDAsMCwxLjU2MS01LjQzM2MwLS4wOCwwLS4xNTMsMC0uMjE5LS4xNDItMS4xLTQuNTI5LTE0LjQxLTUuMTUyLTE2LjFhMy4xNTUsMy4xNTUsMCwwLDAtMi40MzctMS45MDUuOTc0Ljk3NCwwLDAsMC0uMjkzLjA0MiwxLjYyMSwxLjYyMSwwLDAsMC0xLjA1MywxLDQuMTE3LDQuMTE3LDAsMCwwLC4xMjcsMi42MjVjLjgyMywyLjYxMiwxLjkzMiw2LjIyMSwxLjk0Myw2LjI1N2wtMS4yMTYuNjZjLS4xLS4xMjQtMTAuMzM3LTEyLjQ0Ny0xMS45MDYtMTQuMjI1YTIuOTU4LDIuOTU4LDAsMCwwLTIuMjEzLTEuMTc0LDEuOTc5LDEuOTc5LDAsMCwwLTEuMy40NzUsMS4wNDksMS4wNDksMCwwLDAtLjMwOC43NTMsMy44LDMuOCwwLDAsMCwuOTI5LDIuNDgzYzEuMDM3LDEuMTc3LDcuNTA1LDkuMTMsNy43OCw5LjQ2OGwtMS4wODkuOWMtLjA5LS4xMDgtOS4wMjEtMTAuODUtMTAuMTE2LTEyLjE1NGEzLjE0OSwzLjE0OSwwLDAsMC0yLjE5NS0xLjI2LDIuMzQsMi4zNCwwLDAsMC0xLjQ2Ni41OTEsMS4xMTUsMS4xMTUsMCwwLDAtLjQyNy44MjVjLS4wOTMsMS4xMDguOTE5LDIuODExLDEuOSwzLjkyNC4xLjExOCw5LjE4MSwxMC42LDkuNTY4LDExLjA0OUwyMS40MzgsMjljLS4wODItLjA5NC04LjE4Ny05LjM2OC04Ljk0MS0xMC4yMzhhMi44MDksMi44MDksMCwwLDAtMS45MTUtLjgsMS4zMzgsMS4zMzgsMCwwLDAtMSwuMzcyYy0uOTM1Ljk1OC0uMzIzLDIuMzQ4LjM1NiwzLjM0Ni4yNTUuMzc0LDEuMTU1LDEuNTA4LDQsNC43ODgsMS44NDYsMi4wOTIsNC44NTYsNS41MjksNC44ODYsNS41NjNsLTEuMDU3LjkzN2MtLjAyNS0uMDI4LTIuNTM5LTIuODU5LTQuODktNS41NjgtLjcxNC0uODA5LTEuMTY1LTEuMzE3LTEuMzQtMS41MDlhMS43LDEuNywwLDAsMC0xLjE0My0uNjE3LDEuNjYyLDEuNjYyLDAsMCwwLTEuMTUyLjYyN0M4LjUsMjYuNjc1LDkuNTA2LDI4LjUsOS45MjQsMjkuMDg3WiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoNC4wNDIgMC44OTYpIiBmaWxsPSIjZmZmIi8+Cjwvc3ZnPgo="
    elif task == "Scan":
        return "data:image/svg+xml;base64,PHN2ZyBpZD0iQ2xpZW50X1RBRl9TY2FubmVyIiBkYXRhLW5hbWU9IkNsaWVudCBUQUYgU2Nhbm5lciIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCI+CiAgPHJlY3QgaWQ9IlJlY2h0ZWNrXzExNTAiIGRhdGEtbmFtZT0iUmVjaHRlY2sgMTE1MCIgd2lkdGg9IjQ1IiBoZWlnaHQ9IjQ1IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSg3LjUgNy41KSIgZmlsbD0ibm9uZSIvPgogIDxnIGlkPSJHcnVwcGVfNDQ0NSIgZGF0YS1uYW1lPSJHcnVwcGUgNDQ0NSIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTEuNzE5IDEyLjI5MykiPgogICAgPHBhdGggaWQ9IlBmYWRfMzEyNSIgZGF0YS1uYW1lPSJQZmFkIDMxMjUiIGQ9Ik0yMjM2Ny4yLDI0NDM3LjQzOGgtOS45OTR2LTEuNzgxaDkuOTk0di05Ljg0NGgxLjh2OS44NDRBMS43ODIsMS43ODIsMCwwLDEsMjIzNjcuMiwyNDQzNy40MzhabS0yMC44ODksMGgtOS45OTJhMS44LDEuOCwwLDAsMS0xLjgyLTEuNzgxdi05Ljg0NGgxLjgydjkuODQ0aDkuOTkydjEuNzgxWm0yMi42ODgtMjIuMzMyaC0xLjh2LTkuODI0aC05Ljk5NHYtMS43ODFoOS45OTRhMS43ODQsMS43ODQsMCwwLDEsMS44LDEuNzgxdjkuODI0Wm0tMzIuNjgsMGgtMS44MnYtOS44MjRhMS44LDEuOCwwLDAsMSwxLjgyLTEuNzgxaDkuOTkydjEuNzgxaC05Ljk5MnY5LjgyNFoiIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0yMjMzMyAtMjQ0MDMuNSkiIGZpbGw9IiNmZmYiLz4KICAgIDxwYXRoIGlkPSJQYXRoXzMwODIiIGRhdGEtbmFtZT0iUGF0aCAzMDgyIiBkPSJNMzYuMTA3LDFILjM5M0EuODMxLjgzMSwwLDAsMS0uNS4yNS44MzEuODMxLDAsMCwxLC4zOTMtLjVIMzYuMTA3QS44MzEuODMxLDAsMCwxLDM3LC4yNS44MzEuODMxLDAsMCwxLDM2LjEwNywxWiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMC41IDE2LjcyMikiIGZpbGw9IiNmZmYiLz4KICAgIDxwYXRoIGlkPSJQYXRoXzMwODItMiIgZGF0YS1uYW1lPSJQYXRoIDMwODIiIGQ9Ik0yMi45NjMsMUguNDk0QS45LjksMCwwLDEtLjUuMjUuOS45LDAsMCwxLC40OTQtLjVIMjIuOTYzYS45LjksMCwwLDEsLjk5NC43NUEuOS45LDAsMCwxLDIyLjk2MywxWiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoNy4wMjEgMTEuMzE2KSIgZmlsbD0iI2ZmZiIvPgogICAgPHBhdGggaWQ9IlBhdGhfMzA4Mi0zIiBkYXRhLW5hbWU9IlBhdGggMzA4MiIgZD0iTTIzLjQ2MywxLjVILjk5NEEuOS45LDAsMCwxLDAsLjc1LjkuOSwwLDAsMSwuOTk0LDBIMjMuNDYzYS45LjksMCwwLDEsLjk5NC43NUEuOS45LDAsMCwxLDIzLjQ2MywxLjVaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgzMC45NzkgMjMuMTI3KSByb3RhdGUoMTgwKSIgZmlsbD0iI2ZmZiIvPgogICAgPHBhdGggaWQ9IlBhdGhfMzA4Mi00IiBkYXRhLW5hbWU9IlBhdGggMzA4MiIgZD0iTTE0LjgxNSwxSC42NzlDLjAyOCwxLS41LjY2NC0uNS4yNVMuMDI4LS41LjY3OS0uNUgxNC44MTVjLjY1MSwwLDEuMTc5LjMzNiwxLjE3OS43NVMxNS40NjYsMSwxNC44MTUsMVoiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDExLjAwMyA3LjcxMykiIGZpbGw9IiNmZmYiLz4KICAgIDxwYXRoIGlkPSJQYXRoXzMwODItNSIgZGF0YS1uYW1lPSJQYXRoIDMwODIiIGQ9Ik0xNS4zMTUsMS41SDEuMTc5Qy41MjgsMS41LDAsMS4xNjQsMCwuNzVTLjUyOCwwLDEuMTc5LDBIMTUuMzE1Yy42NTEsMCwxLjE3OS4zMzYsMS4xNzkuNzVTMTUuOTY2LDEuNSwxNS4zMTUsMS41WiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjYuOTk3IDI2LjczKSByb3RhdGUoMTgwKSIgZmlsbD0iI2ZmZiIvPgogIDwvZz4KPC9zdmc+Cg=="
    elif task == "Tightening":
        return "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj4KICA8ZyBpZD0iR3J1cHBlXzUwMjgiIGRhdGEtbmFtZT0iR3J1cHBlIDUwMjgiIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0xMzM4IC05NjApIj4KICAgIDxnIGlkPSJDbGllbnRfVEFGX1NjaHJhdWJlciIgZGF0YS1uYW1lPSJDbGllbnQgVEFGIFNjaHJhdWJlciIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTMzOCA5NjApIj4KICAgICAgPHJlY3QgaWQ9IlJlY2h0ZWNrXzExNTMiIGRhdGEtbmFtZT0iUmVjaHRlY2sgMTE1MyIgd2lkdGg9IjQ1IiBoZWlnaHQ9IjQ1IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSg4LjI1IDcuNSkiIGZpbGw9Im5vbmUiLz4KICAgIDwvZz4KICAgIDxnIGlkPSJHcnVwcGVfNDk5OSIgZGF0YS1uYW1lPSJHcnVwcGUgNDk5OSIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTEyNTguODQyIDc2NS41KSI+CiAgICAgIDxnIGlkPSJSZWNodGVja18xNDU4IiBkYXRhLW5hbWU9IlJlY2h0ZWNrIDE0NTgiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDI2MTggMjQxLjYpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMSI+CiAgICAgICAgPHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjUiIHJ4PSIxIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cmVjdCB4PSIwLjUiIHk9IjAuNSIgd2lkdGg9IjIzIiBoZWlnaHQ9IjQiIHJ4PSIwLjUiIGZpbGw9Im5vbmUiLz4KICAgICAgPC9nPgogICAgICA8ZyBpZD0iUGZhZF80MDYzIiBkYXRhLW5hbWU9IlBmYWQgNDA2MyIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjY0Ni44NjQgMjMwLjc5MikiIGZpbGw9Im5vbmUiPgogICAgICAgIDxwYXRoIGQ9Ik0tMjQuNTgyLDBoMTMuN2ExMi44MzIsMTIuODMyLDAsMCwwLC4xNjMsMi4wNzNjLjE2Ni44MDcsMS4wMjQuODIsMS43NTQsMS4zODNBMS43MjYsMS43MjYsMCwwLDEtOC4yMzIsNC43VjkuMTE4YTYuNDY2LDYuNDY2LDAsMCwxLDEuMSwxLjAxLDcuMzE5LDcuMzE5LDAsMCwxLC45MjEsMS41NjVILTguNzIzbC0xNS45MzcuMDE2Yy0uMjQyLDAtMi44NDEtLjAwOC0yLjksMHMtLjU4Ni0uMDcxLS42NzguMTg4YTguNzk0LDguNzk0LDAsMCwxLC42NzgtMS41MThBMTkuMTQ0LDE5LjE0NCwwLDAsMS0yNS4xLDcuMzEyVi41MTRBLjUxNC41MTQsMCwwLDEtMjQuNTgyLDBaIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cGF0aCBkPSJNIC0yNC4wOTU3Nzk0MTg5NDUzMSAxLjAwMDAwMTkwNzM0ODYzMyBMIC0yNC4wOTU4ODA1MDg0MjI4NSA3LjcxNzk0MjIzNzg1NDAwNCBMIC0yNC4zNzg5MjkxMzgxODM1OSA4LjAwOTA0MjczOTg2ODE2NCBDIC0yNC44NDg1NzU1OTIwNDEwMiA4LjQ5MjA0ODI2MzU0OTgwNSAtMjYuMTEyMTU5NzI5MDAzOTEgOS44Njc0NTM1NzUxMzQyNzcgLTI2LjU5OTc0NjcwNDEwMTU2IDEwLjcwNTUwMDYwMjcyMjE3IEMgLTI1LjgxMzY5NzgxNDk0MTQxIDEwLjcwNjA0ODk2NTQ1NDEgLTI0LjgwNDgwOTU3MDMxMjUgMTAuNzA4OTgyNDY3NjUxMzcgLTI0LjY2MTM4MDc2NzgyMjI3IDEwLjcwODk4MjQ2NzY1MTM3IEwgLTguNzIyOTAwMzkwNjI1IDEwLjY5MzM2MjIzNjAyMjk1IEwgLTcuOTYyMTY3NzM5ODY4MTY0IDEwLjY5MzQ5MDk4MjA1NTY2IEMgLTguMzU4MTY5NTU1NjY0MDYyIDEwLjI1MTc5NTc2ODczNzc5IC04Ljc5Nzk0MzExNTIzNDM3NSA5Ljk0MjYyMTIzMTA3OTEwMiAtOC44MDA3NjAyNjkxNjUwMzkgOS45NDA2NDIzNTY4NzI1NTkgTCAtOS4yMzIxNzAxMDQ5ODA0NjkgOS42NDI0NTIyMzk5OTAyMzQgTCAtOS4yMzIxNzAxMDQ5ODA0NjkgNC43Mzk1MDA1MjI2MTM1MjUgQyAtOS4yMzI3MDIyNTUyNDkwMjMgNC43MzYzNzY3NjIzOTAxMzcgLTkuMjMzMzY0MTA1MjI0NjA5IDQuNzMyNzg1NzAxNzUxNzA5IC05LjIzNDE4ODA3OTgzMzk4NCA0LjcyODc0MjEyMjY1MDE0NiBMIC05LjIzMjE3MDEwNDk4MDQ2OSA0LjcwMDM0MjE3ODM0NDcyNyBMIC05LjIzNDM4NjQ0NDA5MTc5NyA0LjcyNzc3NzAwNDI0MTk0MyBDIC05LjI0OTEwMzU0NjE0MjU3OCA0LjY1NjUyMDg0MzUwNTg1OSAtOS4zMTI4Mzc2MDA3MDgwMDggNC40NTE2NTg3MjU3Mzg1MjUgLTkuNTc3NTI5OTA3MjI2NTYyIDQuMjQ3MzAyMDU1MzU4ODg3IEMgLTkuNzUwMzYwNDg4ODkxNjAyIDQuMTEzODcyMDUxMjM5MDE0IC05Ljk1OTI4OTU1MDc4MTI1IDQuMDE0MjkyMjQwMTQyODIyIC0xMC4xODA0OTA0OTM3NzQ0MSAzLjkwODg3MjEyNzUzMjk1OSBDIC0xMC43MDI3Mzk3MTU1NzYxNyAzLjY1OTk3MjE5MDg1NjkzNCAtMTEuNDkxOTcwMDYyMjU1ODYgMy4yODM4MjIwNTk2MzEzNDggLTExLjcwMDIxMDU3MTI4OTA2IDIuMjc0NzAyMDcyMTQzNTU1IEMgLTExLjc4MTY4Njc4MjgzNjkxIDEuODc5ODg3NTgwODcxNTgyIC0xMS44MjcwOTY5MzkwODY5MSAxLjQxMDY1MDI1MzI5NTg5OCAtMTEuODUyMzcxMjE1ODIwMzEgMS4wMDAwMDE5MDczNDg2MzMgTCAtMjQuMDk1Nzc5NDE4OTQ1MzEgMS4wMDAwMDE5MDczNDg2MzMgTSAtMjQuNTgxNjQ5NzgwMjczNDQgMS45MDczNDg2MzI4MTI1ZS0wNiBMIC0xMC44ODM4ODA2MTUyMzQzOCAxLjkwNzM0ODYzMjgxMjVlLTA2IEMgLTEwLjg4Mzg4MDYxNTIzNDM4IDEuOTA3MzQ4NjMyODEyNWUtMDYgLTEwLjg4NzMzMTAwODkxMTEzIDEuMjY1ODUxOTc0NDg3MzA1IC0xMC43MjA4NDk5OTA4NDQ3MyAyLjA3MjYwMjI3MjAzMzY5MSBDIC0xMC41NTQzNzA4ODAxMjY5NSAyLjg3OTM1MjU2OTU4MDA3OCAtOS42OTYzNzEwNzg0OTEyMTEgMi44OTIyMTE5MTQwNjI1IC04Ljk2NjQzMDY2NDA2MjUgMy40NTU3NTIzNzI3NDE2OTkgQyAtOC4yMzY0ODA3MTI4OTA2MjUgNC4wMTkyOTIzNTQ1ODM3NCAtOC4yMzIxNzAxMDQ5ODA0NjkgNC43MDAzNDIxNzgzNDQ3MjcgLTguMjMyMTcwMTA0OTgwNDY5IDQuNzAwMzQyMTc4MzQ0NzI3IEwgLTguMjMyMTcwMTA0OTgwNDY5IDkuMTE4MDIxOTY1MDI2ODU1IEMgLTguMjMyMTcwMTA0OTgwNDY5IDkuMTE4MDIxOTY1MDI2ODU1IC03LjYzODE2MDcwNTU2NjQwNiA5LjUyODYwMjYwMDA5NzY1NiAtNy4xMjgyNDA1ODUzMjcxNDggMTAuMTI4MjUyMDI5NDE4OTUgQyAtNi42MTgzMjA0NjUwODc4OTEgMTAuNzI3OTAyNDEyNDE0NTUgLTYuMjA3MjgxMTEyNjcwODk4IDExLjY5MzM2MjIzNjAyMjk1IC02LjIwNzI4MTExMjY3MDg5OCAxMS42OTMzNjIyMzYwMjI5NSBDIC02Ljc4ODQwNjM3MjA3MDMxMiAxMS42OTM5NjIwOTcxNjc5NyAtOC40Mzg5NDk1ODQ5NjA5MzggMTEuNjkzMzYyMjM2MDIyOTUgLTguNzIyOTAwMzkwNjI1IDExLjY5MzM2MjIzNjAyMjk1IEwgLTI0LjY2MDQwMDM5MDYyNSAxMS43MDg5ODI0Njc2NTEzNyBDIC0yNC45MDI4ODkyNTE3MDg5OCAxMS43MDg5ODI0Njc2NTEzNyAtMjcuNTAxMTgwNjQ4ODAzNzEgMTEuNzAwOTUyNTI5OTA3MjMgLTI3LjU2MDYzMDc5ODMzOTg0IDExLjcwODk4MjQ2NzY1MTM3IEMgLTI3LjU4MTg4NDM4NDE1NTI3IDExLjcxMTg1Njg0MjA0MTAyIC0yNy42NjI5MTYxODM0NzE2OCAxMS43MDM1NzYwODc5NTE2NiAtMjcuNzYyNDE2ODM5NTk5NjEgMTEuNzAzNTc2MDg3OTUxNjYgQyAtMjcuOTQxMjA3ODg1NzQyMTkgMTEuNzAzNTc2MDg3OTUxNjYgLTI4LjE3OTY4NzUgMTEuNzMwMjk4MDQyMjk3MzYgLTI4LjIzODUyOTIwNTMyMjI3IDExLjg5NjQ4MjQ2NzY1MTM3IEMgLTI4LjIzODUyOTIwNTMyMjI3IDExLjg5NjQ4MjQ2NzY1MTM3IC0yOC4xNDMzMDEwMTAxMzE4NCAxMS41MTAxOTE5MTc0MTk0MyAtMjcuNTYwNjMwNzk4MzM5ODQgMTAuMzc4MjkyMDgzNzQwMjMgQyAtMjYuOTc3OTYwNTg2NTQ3ODUgOS4yNDYzOTIyNTAwNjEwMzUgLTI1LjA5NTc3OTQxODk0NTMxIDcuMzExODEyNDAwODE3ODcxIC0yNS4wOTU3Nzk0MTg5NDUzMSA3LjMxMTgxMjQwMDgxNzg3MSBMIC0yNS4wOTU3Nzk0MTg5NDUzMSAwLjUxNDEzMjQ5OTY5NDgyNDIgQyAtMjUuMDk1Nzc5NDE4OTQ1MzEgMC4yMzAxODI2NDc3MDUwNzgxIC0yNC44NjU2MDA1ODU5Mzc1IDEuOTA3MzQ4NjMyODEyNWUtMDYgLTI0LjU4MTY0OTc4MDI3MzQ0IDEuOTA3MzQ4NjMyODEyNWUtMDYgWiIgc3Ryb2tlPSJub25lIiBmaWxsPSIjZmZmIi8+CiAgICAgIDwvZz4KICAgICAgPGcgaWQ9IlJlY2h0ZWNrXzE0NTkiIGRhdGEtbmFtZT0iUmVjaHRlY2sgMTQ1OSIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjYxMi4xMiAyMDIpIHJvdGF0ZSg4KSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEiPgogICAgICAgIDxyZWN0IHdpZHRoPSIzNS4wNjQiIGhlaWdodD0iOC41MzUiIHJ4PSIzIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cmVjdCB4PSIwLjUiIHk9IjAuNSIgd2lkdGg9IjM0LjA2NCIgaGVpZ2h0PSI3LjUzNSIgcng9IjIuNSIgZmlsbD0ibm9uZSIvPgogICAgICA8L2c+CiAgICAgIDxnIGlkPSJQZmFkXzQwNjQiIGRhdGEtbmFtZT0iUGZhZCA0MDY0IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgyNjE2LjE1OSAyMTEuMDg4KSByb3RhdGUoOCkiIGZpbGw9Im5vbmUiPgogICAgICAgIDxwYXRoIGQ9Ik0uODg5LS4zOTNIMjEuMWMuMjgzLDAsNS4yMjgsMCw1Ljc3Ni4wMDlhNC43NTMsNC43NTMsMCwwLDEtMi40MTksMS4zOTJjLTEuMTE1LjItMy40NzgtLjA4NS00LjI0NC42LTEuNjk0LDEuNTA5LjAyMSw2LjkyOS4wMjEsNi45MjkuMDc0LjMsMi4yNTYsOC4zODMsMi4yMDcsOC43MDYsMCwwLTkuODYyLDEuNC0xMC43ODUsMS41MTYtLjM0My0uMDkxLDEuNzg3LTEuMjA2LDEuNzktMy4zMDctLjMtMS45MzktLjg5Mi01LjY3OC0xLjIxMS03LjgzMy0uMS0uOTQ5LS4zNzgtMS40NjEtLjUxMS0xLjUxOWExMi4wNTMsMTIuMDUzLDAsMCwxLTEuMjE3LS42MTdjLTEuNjg0LS4wNjUtMi4zODMtLjItMi40NzctLjczNi0uMDctLjguMjI0LS43MTcuNDU4LTEuNzU2UzcuMDI2LDEuMTU0LDcuMDI2LDEuMTU0QzMuMzIsMS4wNDkuNi0uMzkzLjg4OS0uMzkzWiIgc3Ryb2tlPSJub25lIi8+CiAgICAgICAgPHBhdGggZD0iTSAxOS45MDA5OTMzNDcxNjc5NyAwLjYwNjM3MDkyNTkwMzMyMDMgTCA4LjA3NDk3NTk2NzQwNzIyNyAwLjYwNjY2ODQ3MjI5MDAzOTEgQyA4LjIwNTQzNjcwNjU0Mjk2OSAwLjY5MzM5OTQyOTMyMTI4OTEgOC4zNDUzNDQ1NDM0NTcwMzEgMC43OTQ2MzAwNTA2NTkxNzk3IDguNDgzNjcxMTg4MzU0NDkyIDAuOTA5MTUxMDc3MjcwNTA3OCBDIDkuNTgzMjAyMzYyMDYwNTQ3IDEuODE5NDcxMzU5MjUyOTMgOS41NzEyMDEzMjQ0NjI4OTEgMi43Mzc1MTA2ODExNTIzNDQgOS40NjYxNzEyNjQ2NDg0MzggMy4yMDM3MzA1ODMxOTA5MTggQyA5LjM0MjE2MTE3ODU4ODg2NyAzLjc1NDIyMDk2MjUyNDQxNCA5LjE5NDQyMTc2ODE4ODQ3NyA0LjA3MjIxMDMxMTg4OTY0OCA5LjA5NjY2MjUyMTM2MjMwNSA0LjI4MjYzMDkyMDQxMDE1NiBDIDkuMDgzOTQyNDEzMzMwMDc4IDQuMzEwMDA3MDk1MzM2OTE0IDkuMDczMTQ0OTEyNzE5NzI3IDQuMzMzMjUwOTk5NDUwNjg0IDkuMDY0MDI5NjkzNjAzNTE2IDQuMzUzNjM4NjQ4OTg2ODE2IEMgOS4zMDM5MTMxMTY0NTUwNzggNC4zOTk2ODM5NTIzMzE1NDMgOS43NDU2MTUwMDU0OTMxNjQgNC40NDY2MTMzMTE3Njc1NzggMTAuNTQ4MDIxMzE2NTI4MzIgNC40NzczNjA3MjU0MDI4MzIgTCAxMC44NjQ2MzE2NTI4MzIwMyA0LjQ4OTUwMDk5OTQ1MDY4NCBMIDExLjExNjQ5MTMxNzc0OTAyIDQuNjgxNzUwMjk3NTQ2Mzg3IEMgMTEuMjU2NDcxNjMzOTExMTMgNC43ODg2MTA0NTgzNzQwMjMgMTEuNTI4ODQxOTcyMzUxMDcgNC45MDI0MjA5OTc2MTk2MjkgMTEuNzI3NzExNjc3NTUxMjcgNC45ODU1MTA4MjYxMTA4NCBDIDExLjk0Njk0NzA5Nzc3ODMyIDUuMDc3MTE3OTE5OTIxODc1IDEyLjEyNTQ3OTY5ODE4MTE1IDUuMTUxNzIyOTA4MDIwMDIgMTIuMjg0NDk5MTY4Mzk2IDUuMjYyODYxMjUxODMxMDU1IEMgMTIuOTM0NjYwOTExNTYwMDYgNS42ODk2MDE4OTgxOTMzNTkgMTMuMTU1Mjg0ODgxNTkxOCA2LjgxMDc1MzgyMjMyNjY2IDEzLjIyOTc2Nzc5OTM3NzQ0IDcuNDg1NDA0MDE0NTg3NDAyIEMgMTMuNTIwMTk3ODY4MzQ3MTcgOS40NDkwMTE4MDI2NzMzNCAxNC4wMzkwNzg3MTI0NjMzOCAxMi43NTgzMDU1NDk2MjE1OCAxNC4zNDk0OTIwNzMwNTkwOCAxNC43MzgwMjA4OTY5MTE2MiBMIDE0LjQ0ODQxMTk0MTUyODMyIDE1LjM2OTA4MDU0MzUxODA3IEwgMTQuNDQ4MjkxNzc4NTY0NDUgMTUuNDQ3NzUwMDkxNTUyNzMgQyAxNC40NDcwODI1MTk1MzEyNSAxNi4yMTU5NjMzNjM2NDc0NiAxNC4yMzAxNDY0MDgwODEwNSAxNi44NzgwNzA4MzEyOTg4MyAxMy45MzY3MTcwMzMzODYyMyAxNy40Mjg0OTM0OTk3NTU4NiBDIDE2LjI0Mjc4MjU5Mjc3MzQ0IDE3LjEwNTE0NjQwODA4MTA1IDE5LjU3MTg1NzQ1MjM5MjU4IDE2LjYzNDI1MDY0MDg2OTE0IDIxLjI1MDczMjQyMTg3NSAxNi4zOTY1NTQ5NDY4OTk0MSBDIDIxLjAwNTQ3MDI3NTg3ODkxIDE1LjM4MDQ0NDUyNjY3MjM2IDIwLjQ4ODEwNTc3MzkyNTc4IDEzLjM2MjUxOTI2NDIyMTE5IDE5LjQ1ODE3MTg0NDQ4MjQyIDkuNDk5NDIwMTY2MDE1NjI1IEMgMTkuMzQ5MDU2MjQzODk2NDggOS4wOTAxNTM2OTQxNTI4MzIgMTkuMjk1Mjk5NTMwMDI5MyA4Ljg4ODQxNTMzNjYwODg4NyAxOS4yNzM3NDI2NzU3ODEyNSA4LjgwNTIxMjAyMDg3NDAyMyBDIDE5LjIwNzM5OTM2ODI4NjEzIDguNTkwNzg0MDcyODc1OTc3IDE4LjgxMTE2NDg1NTk1NzAzIDcuMjc0ODI4OTEwODI3NjM3IDE4LjU5OTkyMjE4MDE3NTc4IDUuNzcyNzQwMzY0MDc0NzA3IEMgMTguMjU3NjAyNjkxNjUwMzkgMy4zMzg3MTA3ODQ5MTIxMDkgMTguNTY4MjIyMDQ1ODk4NDQgMS43MzA2NDA0MTEzNzY5NTMgMTkuNTQ5NTEwOTU1ODEwNTUgMC44NTY2MTEyNTE4MzEwNTQ3IEMgMTkuNjU2NTMyMjg3NTk3NjYgMC43NjEyOTE1MDM5MDYyNSAxOS43NzQxOTg1MzIxMDQ0OSAwLjY3ODQ1NzI2MDEzMTgzNTkgMTkuOTAwOTkzMzQ3MTY3OTcgMC42MDYzNzA5MjU5MDMzMjAzIE0gMjEuMTAxMDcyMzExNDAxMzcgLTAuMzkzNjU5NTkxNjc0ODA0NyBDIDIxLjM4MzY5MTc4NzcxOTczIC0wLjM5MjIxMDAwNjcxMzg2NzIgMjYuMzI5NTQyMTYwMDM0MTggLTAuMzkxMzQwMjU1NzM3MzA0NyAyNi44NzcyNDExMzQ2NDM1NSAtMC4zODQ5NjAxNzQ1NjA1NDY5IEMgMjYuODc3MjQxMTM0NjQzNTUgLTAuMzg0OTYwMTc0NTYwNTQ2OSAyNS44NzE0ODA5NDE3NzI0NiAwLjc1NDg1OTkyNDMxNjQwNjIgMjQuNDU4NjIxOTc4NzU5NzcgMS4wMDY5MTAzMjQwOTY2OCBDIDIzLjM0Mzc5MTk2MTY2OTkyIDEuMjA1NzMwNDM4MjMyNDIyIDIwLjk4MDIyMDc5NDY3NzczIDAuOTIxNDYxMTA1MzQ2Njc5NyAyMC4yMTQ2MjI0OTc1NTg1OSAxLjYwMzM2MTEyOTc2MDc0MiBDIDE4LjUyMDgyMDYxNzY3NTc4IDMuMTEyMDAwNDY1MzkzMDY2IDIwLjIzNjA3MjU0MDI4MzIgOC41MzIxMDA2Nzc0OTAyMzQgMjAuMjM2MDcyNTQwMjgzMiA4LjUzMjEwMDY3NzQ5MDIzNCBDIDIwLjMwOTc2MTA0NzM2MzI4IDguODI4MTkwODAzNTI3ODMyIDIyLjQ5MjQ2MjE1ODIwMzEyIDE2LjkxNTEzMDYxNTIzNDM4IDIyLjQ0MzExMTQxOTY3NzczIDE3LjIzNzY0MDM4MDg1OTM4IEMgMjIuNDQzMTExNDE5Njc3NzMgMTcuMjM3NjQwMzgwODU5MzggMTIuNTgxNDcxNDQzMTc2MjcgMTguNjM1NTYwOTg5Mzc5ODggMTEuNjU4NDcyMDYxMTU3MjMgMTguNzUzMzIwNjkzOTY5NzMgQyAxMS4zMTU3NzExMDI5MDUyNyAxOC42NjI0Mjk4MDk1NzAzMSAxMy40NDQ5ODE1NzUwMTIyMSAxNy41NDcxMjEwNDc5NzM2MyAxMy40NDgyOTE3Nzg1NjQ0NSAxNS40NDYxNzA4MDY4ODQ3NyBDIDEzLjE0NDUyMTcxMzI1Njg0IDEzLjUwNzY0MDgzODYyMzA1IDEyLjU1NjM4MTIyNTU4NTk0IDkuNzY4NTkwOTI3MTI0MDIzIDEyLjIzNzcyMTQ0MzE3NjI3IDcuNjEyNzEwOTUyNzU4Nzg5IEMgMTIuMTM1NzExNjY5OTIxODggNi42NjM5MjA0MDI1MjY4NTUgMTEuODU5NjgyMDgzMTI5ODggNi4xNTE5MDAyOTE0NDI4NzEgMTEuNzI2OTYyMDg5NTM4NTcgNi4wOTM4NzAxNjI5NjM4NjcgQyAxMS41NTkzNzE5NDgyNDIxOSA1Ljk2MTY3MDg3NTU0OTMxNiAxMC45MTM4MjIxNzQwNzIyNyA1Ljc4NTEwMDkzNjg4OTY0OCAxMC41MDk3MjE3NTU5ODE0NSA1LjQ3NjYzMDIxMDg3NjQ2NSBDIDguODI1OTUyNTI5OTA3MjI3IDUuNDEyMTAwNzkxOTMxMTUyIDguMTI2ODUyMDM1NTIyNDYxIDUuMjgxMzgwNjUzMzgxMzQ4IDguMDMyNzQxNTQ2NjMwODU5IDQuNzQwMzQwMjMyODQ5MTIxIEMgNy45NjI4NTI0NzgwMjczNDQgMy45NDI5OTAzMDMwMzk1NTEgOC4yNTY0NjIwOTcxNjc5NjkgNC4wMjM0MTA3OTcxMTkxNDEgOC40OTA2MjE1NjY3NzI0NjEgMi45ODM5NjAxNTE2NzIzNjMgQyA4LjcyNDc3MTQ5OTYzMzc4OSAxLjk0NDUyMDk1MDMxNzM4MyA3LjAyNTY4MjQ0OTM0MDgyIDEuMTU0NDcwNDQzNzI1NTg2IDcuMDI1NjgyNDQ5MzQwODIgMS4xNTQ0NzA0NDM3MjU1ODYgQyAzLjMyMDMwMTA1NTkwODIwMyAxLjA0ODk1OTczMjA1NTY2NCAwLjYwNDg2MjIxMzEzNDc2NTYgLTAuMzkzMTUwMzI5NTg5ODQzOCAwLjg4ODgxMTExMTQ1MDE5NTMgLTAuMzkzMTUwMzI5NTg5ODQzOCBMIDIxLjEwMTA3MjMxMTQwMTM3IC0wLjM5MzY1OTU5MTY3NDgwNDcgWiIgc3Ryb2tlPSJub25lIiBmaWxsPSIjZmZmIi8+CiAgICAgIDwvZz4KICAgICAgPGcgaWQ9IlJlY2h0ZWNrXzE0NjAiIGRhdGEtbmFtZT0iUmVjaHRlY2sgMTQ2MCIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjYwOC4wMTUgMjA0LjA2Nikgcm90YXRlKDgpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMSI+CiAgICAgICAgPHBhdGggZD0iTTEuNDkxLDBoMi42NGEwLDAsMCwwLDEsMCwwVjIuOTgyYTAsMCwwLDAsMSwwLDBIMS40OTFBMS40OTEsMS40OTEsMCwwLDEsMCwxLjQ5MXYwQTEuNDkxLDEuNDkxLDAsMCwxLDEuNDkxLDBaIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cGF0aCBkPSJNMS40OTEuNWgyLjE0YTAsMCwwLDAsMSwwLDBWMi40ODJhMCwwLDAsMCwxLDAsMEgxLjQ5MUEuOTkxLjk5MSwwLDAsMSwuNSwxLjQ5MXYwQS45OTEuOTkxLDAsMCwxLDEuNDkxLjVaIiBmaWxsPSJub25lIi8+CiAgICAgIDwvZz4KICAgICAgPGcgaWQ9IlJlY2h0ZWNrXzE0NjEiIGRhdGEtbmFtZT0iUmVjaHRlY2sgMTQ2MSIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjYwMy42ODkgMjA0LjI5NSkgcm90YXRlKDgpIiBmaWxsPSIjZmZmIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMSI+CiAgICAgICAgPHBhdGggZD0iTS42MTcsMEg0LjY1YTAsMCwwLDAsMSwwLDBWMS4yMzRhMCwwLDAsMCwxLDAsMEguNjE3QS42MTcuNjE3LDAsMCwxLDAsLjYxN3YwQS42MTcuNjE3LDAsMCwxLC42MTcsMFoiIHN0cm9rZT0ibm9uZSIvPgogICAgICAgIDxwYXRoIGQ9Ik0uNjE3LjVINC4xNWEwLDAsMCwwLDEsMCwwVi43MzRhMCwwLDAsMCwxLDAsMEguNjE3QS4xMTcuMTE3LDAsMCwxLC41LjYxN3YwQS4xMTcuMTE3LDAsMCwxLC42MTcuNVoiIGZpbGw9Im5vbmUiLz4KICAgICAgPC9nPgogICAgICA8ZyBpZD0iUmVjaHRlY2tfMTQ2MiIgZGF0YS1uYW1lPSJSZWNodGVjayAxNDYyIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgyNjIyLjgwNSAyMDUuMjA2KSByb3RhdGUoOCkiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIwLjciPgogICAgICAgIDxyZWN0IHdpZHRoPSI4LjYzNyIgaGVpZ2h0PSIyLjk4MiIgcng9IjAuNSIgc3Ryb2tlPSJub25lIi8+CiAgICAgICAgPHJlY3QgeD0iMC4zNSIgeT0iMC4zNSIgd2lkdGg9IjcuOTM3IiBoZWlnaHQ9IjIuMjgyIiByeD0iMC4xNSIgZmlsbD0ibm9uZSIvPgogICAgICA8L2c+CiAgICA8L2c+CiAgICA8bGluZSBpZD0iTGluaWVfNTU1IiBkYXRhLW5hbWU9IkxpbmllIDU1NSIgeDI9IjMuMzIiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDEzNjQuNjggOTk4LjUpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIwLjciLz4KICAgIDxsaW5lIGlkPSJMaW5pZV81NTYiIGRhdGEtbmFtZT0iTGluaWUgNTU2IiB4Mj0iMy4zMiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTM2NC42OCA5OTkuOTczKSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS13aWR0aD0iMC43Ii8+CiAgICA8bGluZSBpZD0iTGluaWVfNTU3IiBkYXRhLW5hbWU9IkxpbmllIDU1NyIgeDI9IjMuMzIiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDEzNjQuNjggMTAwMS40NDcpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIwLjciLz4KICA8L2c+Cjwvc3ZnPgo="
    elif task == "Rivet":
        return "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj4KICA8ZyBpZD0iR3J1cHBlXzUxMjMiIGRhdGEtbmFtZT0iR3J1cHBlIDUxMjMiIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0xMzM4IC05NjApIj4KICAgIDxnIGlkPSJDbGllbnRfVEFGX1NjaHJhdWJlciIgZGF0YS1uYW1lPSJDbGllbnQgVEFGIFNjaHJhdWJlciIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTMzOCA5NjApIj4KICAgICAgPHJlY3QgaWQ9IlJlY2h0ZWNrXzExNTMiIGRhdGEtbmFtZT0iUmVjaHRlY2sgMTE1MyIgd2lkdGg9IjQ1IiBoZWlnaHQ9IjQ1IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSg4LjI1IDcuNSkiIGZpbGw9Im5vbmUiLz4KICAgIDwvZz4KICAgIDxnIGlkPSJHcnVwcGVfNDk5OSIgZGF0YS1uYW1lPSJHcnVwcGUgNDk5OSIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTEyNjQuODQyIDc2NS43KSI+CiAgICAgIDxnIGlkPSJSZWNodGVja18xNDU4IiBkYXRhLW5hbWU9IlJlY2h0ZWNrIDE0NTgiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDI2MTggMjQxLjYpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMSI+CiAgICAgICAgPHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjUiIHJ4PSIxIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cmVjdCB4PSIwLjUiIHk9IjAuNSIgd2lkdGg9IjIzIiBoZWlnaHQ9IjQiIHJ4PSIwLjUiIGZpbGw9Im5vbmUiLz4KICAgICAgPC9nPgogICAgICA8ZyBpZD0iUGZhZF80MDYzIiBkYXRhLW5hbWU9IlBmYWQgNDA2MyIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjY0Ni44NjQgMjMwLjc5MikiIGZpbGw9Im5vbmUiPgogICAgICAgIDxwYXRoIGQ9Ik0tMjQuNTgyLDBoMTMuN2ExMi44MzIsMTIuODMyLDAsMCwwLC4xNjMsMi4wNzNjLjE2Ni44MDcsMS4wMjQuODIsMS43NTQsMS4zODNBMS43MjYsMS43MjYsMCwwLDEtOC4yMzIsNC43VjkuMTE4YTYuNDY2LDYuNDY2LDAsMCwxLDEuMSwxLjAxLDcuMzE5LDcuMzE5LDAsMCwxLC45MjEsMS41NjVILTguNzIzbC0xNS45MzcuMDE2Yy0uMjQyLDAtMi44NDEtLjAwOC0yLjksMHMtLjU4Ni0uMDcxLS42NzguMTg4YTguNzk0LDguNzk0LDAsMCwxLC42NzgtMS41MThBMTkuMTQ0LDE5LjE0NCwwLDAsMS0yNS4xLDcuMzEyVi41MTRBLjUxNC41MTQsMCwwLDEtMjQuNTgyLDBaIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cGF0aCBkPSJNIC0yNC4wOTU3Nzk0MTg5NDUzMSAxLjAwMDAwMTkwNzM0ODYzMyBMIC0yNC4wOTU4ODA1MDg0MjI4NSA3LjcxNzk0MjIzNzg1NDAwNCBMIC0yNC4zNzg5MjkxMzgxODM1OSA4LjAwOTA0MjczOTg2ODE2NCBDIC0yNC44NDg1NzU1OTIwNDEwMiA4LjQ5MjA0ODI2MzU0OTgwNSAtMjYuMTEyMTU5NzI5MDAzOTEgOS44Njc0NTM1NzUxMzQyNzcgLTI2LjU5OTc0NjcwNDEwMTU2IDEwLjcwNTUwMDYwMjcyMjE3IEMgLTI1LjgxMzY5NzgxNDk0MTQxIDEwLjcwNjA0ODk2NTQ1NDEgLTI0LjgwNDgwOTU3MDMxMjUgMTAuNzA4OTgyNDY3NjUxMzcgLTI0LjY2MTM4MDc2NzgyMjI3IDEwLjcwODk4MjQ2NzY1MTM3IEwgLTguNzIyOTAwMzkwNjI1IDEwLjY5MzM2MjIzNjAyMjk1IEwgLTcuOTYyMTY3NzM5ODY4MTY0IDEwLjY5MzQ5MDk4MjA1NTY2IEMgLTguMzU4MTY5NTU1NjY0MDYyIDEwLjI1MTc5NTc2ODczNzc5IC04Ljc5Nzk0MzExNTIzNDM3NSA5Ljk0MjYyMTIzMTA3OTEwMiAtOC44MDA3NjAyNjkxNjUwMzkgOS45NDA2NDIzNTY4NzI1NTkgTCAtOS4yMzIxNzAxMDQ5ODA0NjkgOS42NDI0NTIyMzk5OTAyMzQgTCAtOS4yMzIxNzAxMDQ5ODA0NjkgNC43Mzk1MDA1MjI2MTM1MjUgQyAtOS4yMzI3MDIyNTUyNDkwMjMgNC43MzYzNzY3NjIzOTAxMzcgLTkuMjMzMzY0MTA1MjI0NjA5IDQuNzMyNzg1NzAxNzUxNzA5IC05LjIzNDE4ODA3OTgzMzk4NCA0LjcyODc0MjEyMjY1MDE0NiBMIC05LjIzMjE3MDEwNDk4MDQ2OSA0LjcwMDM0MjE3ODM0NDcyNyBMIC05LjIzNDM4NjQ0NDA5MTc5NyA0LjcyNzc3NzAwNDI0MTk0MyBDIC05LjI0OTEwMzU0NjE0MjU3OCA0LjY1NjUyMDg0MzUwNTg1OSAtOS4zMTI4Mzc2MDA3MDgwMDggNC40NTE2NTg3MjU3Mzg1MjUgLTkuNTc3NTI5OTA3MjI2NTYyIDQuMjQ3MzAyMDU1MzU4ODg3IEMgLTkuNzUwMzYwNDg4ODkxNjAyIDQuMTEzODcyMDUxMjM5MDE0IC05Ljk1OTI4OTU1MDc4MTI1IDQuMDE0MjkyMjQwMTQyODIyIC0xMC4xODA0OTA0OTM3NzQ0MSAzLjkwODg3MjEyNzUzMjk1OSBDIC0xMC43MDI3Mzk3MTU1NzYxNyAzLjY1OTk3MjE5MDg1NjkzNCAtMTEuNDkxOTcwMDYyMjU1ODYgMy4yODM4MjIwNTk2MzEzNDggLTExLjcwMDIxMDU3MTI4OTA2IDIuMjc0NzAyMDcyMTQzNTU1IEMgLTExLjc4MTY4Njc4MjgzNjkxIDEuODc5ODg3NTgwODcxNTgyIC0xMS44MjcwOTY5MzkwODY5MSAxLjQxMDY1MDI1MzI5NTg5OCAtMTEuODUyMzcxMjE1ODIwMzEgMS4wMDAwMDE5MDczNDg2MzMgTCAtMjQuMDk1Nzc5NDE4OTQ1MzEgMS4wMDAwMDE5MDczNDg2MzMgTSAtMjQuNTgxNjQ5NzgwMjczNDQgMS45MDczNDg2MzI4MTI1ZS0wNiBMIC0xMC44ODM4ODA2MTUyMzQzOCAxLjkwNzM0ODYzMjgxMjVlLTA2IEMgLTEwLjg4Mzg4MDYxNTIzNDM4IDEuOTA3MzQ4NjMyODEyNWUtMDYgLTEwLjg4NzMzMTAwODkxMTEzIDEuMjY1ODUxOTc0NDg3MzA1IC0xMC43MjA4NDk5OTA4NDQ3MyAyLjA3MjYwMjI3MjAzMzY5MSBDIC0xMC41NTQzNzA4ODAxMjY5NSAyLjg3OTM1MjU2OTU4MDA3OCAtOS42OTYzNzEwNzg0OTEyMTEgMi44OTIyMTE5MTQwNjI1IC04Ljk2NjQzMDY2NDA2MjUgMy40NTU3NTIzNzI3NDE2OTkgQyAtOC4yMzY0ODA3MTI4OTA2MjUgNC4wMTkyOTIzNTQ1ODM3NCAtOC4yMzIxNzAxMDQ5ODA0NjkgNC43MDAzNDIxNzgzNDQ3MjcgLTguMjMyMTcwMTA0OTgwNDY5IDQuNzAwMzQyMTc4MzQ0NzI3IEwgLTguMjMyMTcwMTA0OTgwNDY5IDkuMTE4MDIxOTY1MDI2ODU1IEMgLTguMjMyMTcwMTA0OTgwNDY5IDkuMTE4MDIxOTY1MDI2ODU1IC03LjYzODE2MDcwNTU2NjQwNiA5LjUyODYwMjYwMDA5NzY1NiAtNy4xMjgyNDA1ODUzMjcxNDggMTAuMTI4MjUyMDI5NDE4OTUgQyAtNi42MTgzMjA0NjUwODc4OTEgMTAuNzI3OTAyNDEyNDE0NTUgLTYuMjA3MjgxMTEyNjcwODk4IDExLjY5MzM2MjIzNjAyMjk1IC02LjIwNzI4MTExMjY3MDg5OCAxMS42OTMzNjIyMzYwMjI5NSBDIC02Ljc4ODQwNjM3MjA3MDMxMiAxMS42OTM5NjIwOTcxNjc5NyAtOC40Mzg5NDk1ODQ5NjA5MzggMTEuNjkzMzYyMjM2MDIyOTUgLTguNzIyOTAwMzkwNjI1IDExLjY5MzM2MjIzNjAyMjk1IEwgLTI0LjY2MDQwMDM5MDYyNSAxMS43MDg5ODI0Njc2NTEzNyBDIC0yNC45MDI4ODkyNTE3MDg5OCAxMS43MDg5ODI0Njc2NTEzNyAtMjcuNTAxMTgwNjQ4ODAzNzEgMTEuNzAwOTUyNTI5OTA3MjMgLTI3LjU2MDYzMDc5ODMzOTg0IDExLjcwODk4MjQ2NzY1MTM3IEMgLTI3LjU4MTg4NDM4NDE1NTI3IDExLjcxMTg1Njg0MjA0MTAyIC0yNy42NjI5MTYxODM0NzE2OCAxMS43MDM1NzYwODc5NTE2NiAtMjcuNzYyNDE2ODM5NTk5NjEgMTEuNzAzNTc2MDg3OTUxNjYgQyAtMjcuOTQxMjA3ODg1NzQyMTkgMTEuNzAzNTc2MDg3OTUxNjYgLTI4LjE3OTY4NzUgMTEuNzMwMjk4MDQyMjk3MzYgLTI4LjIzODUyOTIwNTMyMjI3IDExLjg5NjQ4MjQ2NzY1MTM3IEMgLTI4LjIzODUyOTIwNTMyMjI3IDExLjg5NjQ4MjQ2NzY1MTM3IC0yOC4xNDMzMDEwMTAxMzE4NCAxMS41MTAxOTE5MTc0MTk0MyAtMjcuNTYwNjMwNzk4MzM5ODQgMTAuMzc4MjkyMDgzNzQwMjMgQyAtMjYuOTc3OTYwNTg2NTQ3ODUgOS4yNDYzOTIyNTAwNjEwMzUgLTI1LjA5NTc3OTQxODk0NTMxIDcuMzExODEyNDAwODE3ODcxIC0yNS4wOTU3Nzk0MTg5NDUzMSA3LjMxMTgxMjQwMDgxNzg3MSBMIC0yNS4wOTU3Nzk0MTg5NDUzMSAwLjUxNDEzMjQ5OTY5NDgyNDIgQyAtMjUuMDk1Nzc5NDE4OTQ1MzEgMC4yMzAxODI2NDc3MDUwNzgxIC0yNC44NjU2MDA1ODU5Mzc1IDEuOTA3MzQ4NjMyODEyNWUtMDYgLTI0LjU4MTY0OTc4MDI3MzQ0IDEuOTA3MzQ4NjMyODEyNWUtMDYgWiIgc3Ryb2tlPSJub25lIiBmaWxsPSIjZmZmIi8+CiAgICAgIDwvZz4KICAgICAgPGcgaWQ9IlBmYWRfNDA2NCIgZGF0YS1uYW1lPSJQZmFkIDQwNjQiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDI2MTUuNTYgMjE1LjM0OSkgcm90YXRlKDgpIiBmaWxsPSJub25lIj4KICAgICAgICA8cGF0aCBkPSJNMjEuMS0uMzk0Yy4yODMsMC0uMTIxLDEuMDItLjg4NiwxLjU0OC0xLjY5NCwxLjE3LjAyMSw1LjM3Mi4wMjEsNS4zNzIuMDc0LjIzLDIuNDEyLDUuNTMxLDIuMjEzLDYuODA2LDAsMC04LjgyNSwxLjI3OS05Ljc0OCwxLjM3LS4zOTIuMDQ1Ljc0NC0xLjE4Ny43NDctMi44MTUtLjMtMS41LS44OTItNC40LTEuMjExLTYuMDczLS4xLS43MzYtLjM3OC0xLjEzMy0uNTExLTEuMTc3LS4xNjgtLjEtLjgxMy0uMjM5LTEuMjE3LS40NzktMS42ODQtLjA1LTIuMzgzLS4xNTEtMi40NzctLjU3MS0uMDctLjYxOC4yMjQtLjU1Ni40NTgtMS4zNjJzLTEtMi40OTUtMS0yLjQ5NVoiIHN0cm9rZT0ibm9uZSIvPgogICAgICAgIDxwYXRoIGQ9Ik0gMTkuMjk2NjUzNzQ3NTU4NTkgMC42MjI4MTEzMTc0NDM4NDc3IEwgOS4yMDg3MjQ5NzU1ODU5MzggMC43MTQ2NTMwMTUxMzY3MTg4IEMgOS41MTg3MzU4ODU2MjAxMTcgMS40Mjk2MzMxNDA1NjM5NjUgOS41OTUzNTU5ODc1NDg4MjggMi4wMDY3NDA1NzAwNjgzNTkgOS40NTA4OTkxMjQxNDU1MDggMi41MDM5MDA1Mjc5NTQxMDIgQyA5LjM4MDUxNDE0NDg5NzQ2MSAyLjc0NjExMTg2OTgxMjAxMiA5LjMwMzczOTU0NzcyOTQ5MiAyLjkzNDY4NTcwNzA5MjI4NSA5LjIzMTMyMTMzNDgzODg2NyAzLjA4NDgyMzYwODM5ODQzOCBDIDkuNTM4MzQxNTIyMjE2Nzk3IDMuMTE2NTk2MjIxOTIzODI4IDkuOTc1Mjk3OTI3ODU2NDQ1IDMuMTQwOTg5MzAzNTg4ODY3IDEwLjUzOTQxOTE3NDE5NDM0IDMuMTU3NzUwMTI5Njk5NzA3IEwgMTAuNzk3MTE5MTQwNjI1IDMuMTY1NDEwMDQxODA5MDgyIEwgMTEuMDE4OTk5MDk5NzMxNDUgMy4yOTY3MTAwMTQzNDMyNjIgQyAxMS4xNjU4NDc3NzgzMjAzMSAzLjM4MzYxMDcyNTQwMjgzMiAxMS40NDU4Njk0NDU4MDA3OCAzLjQ3NDMyMDQxMTY4MjEyOSAxMS42NTAzMjk1ODk4NDM3NSAzLjU0MDU2MDcyMjM1MTA3NCBDIDExLjg1MzM1OTIyMjQxMjExIDMuNjA2MzI4OTY0MjMzMzk4IDEyLjAyMDM0OTUwMjU2MzQ4IDMuNjYwNDIxMzcxNDU5OTYxIDEyLjE2ODU4MjkxNjI1OTc3IDMuNzM3NTQ3ODc0NDUwNjg0IEMgMTIuOTMzNDIzOTk1OTcxNjggNC4wOTkzNzA5NTY0MjA4OTggMTMuMTY1OTE4MzUwMjE5NzMgNS4yNDg4NDg5MTUxMDAwOTggMTMuMjI0MzgyNDAwNTEyNyA1LjY0ODgxMzI0NzY4MDY2NCBDIDEzLjUxNDM4OTAzODA4NTk0IDcuMTY4NDA3NDQwMTg1NTQ3IDE0LjAzMTI3NDc5NTUzMjIzIDkuNzI0MTQ2ODQyOTU2NTQzIDE0LjM0MDcxODI2OTM0ODE0IDExLjI1NDE4MDkwODIwMzEyIEwgMTQuNDQ4NDg4MjM1NDczNjMgMTEuNzg3MjEwNDY0NDc3NTQgTCAxNC40NDgyODg5MTc1NDE1IDExLjg4ODI4MDg2ODUzMDI3IEMgMTQuNDQ3MDcyOTgyNzg4MDkgMTIuNDg1OTI1Njc0NDM4NDggMTQuMzI1MzA5NzUzNDE3OTcgMTMuMDM0NTQ0OTQ0NzYzMTggMTQuMTcxMzgwOTk2NzA0MSAxMy41MDA3NzE1MjI1MjE5NyBDIDE2LjAzODYxMjM2NTcyMjY2IDEzLjI0MzQwMjQ4MTA3OTEgMTkuMTE5NDMwNTQxOTkyMTkgMTIuODAyMjEwODA3ODAwMjkgMjEuMzUyMjQ1MzMwODEwNTUgMTIuNDc5ODI3ODgwODU5MzggQyAyMS4yNTQ4MzUxMjg3ODQxOCAxMi4wNzA4NTQxODcwMTE3MiAyMS4wNzIyMjM2NjMzMzAwOCAxMS40NDI4NjM0NjQzNTU0NyAyMC43MzE4NTcyOTk4MDQ2OSAxMC40OTQ5ODA4MTIwNzI3NSBDIDIwLjI3OTc2OTg5NzQ2MDk0IDkuMjM1OTMwNDQyODEwMDU5IDE5LjczOTAyODkzMDY2NDA2IDcuOTM5NzUwNjcxMzg2NzE5IDE5LjQ3OTE2NzkzODIzMjQyIDcuMzE2ODMwNjM1MDcwODAxIEMgMTkuMzY2NzEwNjYyODQxOCA3LjA0NzI3MDc3NDg0MTMwOSAxOS4zMjQyMzAxOTQwOTE4IDYuOTQ1MDgxNzEwODE1NDMgMTkuMjk5OTY0OTA0Nzg1MTYgNi44Nzg0NTIzMDEwMjUzOTEgQyAxOS4yMjg0NDY5NjA0NDkyMiA2LjY5ODk2NDU5NTc5NDY3OCAxOC44MjI4NDU0NTg5ODQzOCA1LjY1MTQxODY4NTkxMzA4NiAxOC42MDYyMzkzMTg4NDc2NiA0LjQ1NzQwMDMyMTk2MDQ0OSBDIDE4LjI4NTUzMzkwNTAyOTMgMi42ODk1MzAzNzI2MTk2MjkgMTguNTE3ODQ1MTUzODA4NTkgMS40MDI2MTY1MDA4NTQ0OTIgMTkuMjk2NjUzNzQ3NTU4NTkgMC42MjI4MTEzMTc0NDM4NDc3IE0gMjEuMTAxMDY4NDk2NzA0MSAtMC4zOTM2NTk1OTE2NzQ4MDQ3IEMgMjEuMzgzNjg5ODgwMzcxMDkgLTAuMzkyNTI5NDg3NjA5ODYzMyAyMC45ODAyMTg4ODczMjkxIDAuNjI1ODkwNzMxODExNTIzNCAyMC4yMTQ2MjgyMTk2MDQ0OSAxLjE1NDU0MDA2MTk1MDY4NCBDIDE4LjUyMDgyODI0NzA3MDMxIDIuMzI0MTIwNTIxNTQ1NDEgMjAuMjM2MDc4MjYyMzI5MSA2LjUyNjA4MDYwODM2NzkyIDIwLjIzNjA3ODI2MjMyOTEgNi41MjYwODA2MDgzNjc5MiBDIDIwLjMwOTc2ODY3Njc1NzgxIDYuNzU1NjIwNDc5NTgzNzQgMjIuNjQ4NDM3NSAxMi4wNTcwODAyNjg4NTk4NiAyMi40NDg4NzkyNDE5NDMzNiAxMy4zMzE2MzA3MDY3ODcxMSBDIDIyLjQ0ODg3OTI0MTk0MzM2IDEzLjMzMTYzMDcwNjc4NzExIDEzLjYyMzkxODUzMzMyNTIgMTQuNjEwMzMwNTgxNjY1MDQgMTIuNzAwOTI5NjQxNzIzNjMgMTQuNzAxNjIwMTAxOTI4NzEgQyAxMi4zMDg5NDQ3MDIxNDg0NCAxNC43NDY4NDYxOTkwMzU2NCAxMy40NDQ5Nzg3MTM5ODkyNiAxMy41MTUwMTg0NjMxMzQ3NyAxMy40NDgyODc5NjM4NjcxOSAxMS44ODYyNTA0OTU5MTA2NCBDIDEzLjE0NDUyOTM0MjY1MTM3IDEwLjM4MzM5MDQyNjYzNTc0IDEyLjU1NjM3OTMxODIzNzMgNy40ODQ2NzA2MzkwMzgwODYgMTIuMjM3NzI4MTE4ODk2NDggNS44MTMzMjAxNTk5MTIxMDkgQyAxMi4xMzU3MTkyOTkzMTY0MSA1LjA3Nzc2MDY5NjQxMTEzMyAxMS44NTk2NzgyNjg0MzI2MiA0LjY4MDgyMDQ2NTA4Nzg5MSAxMS43MjY5NTkyMjg1MTU2MiA0LjYzNTgzMDg3OTIxMTQyNiBDIDExLjU1OTM2ODEzMzU0NDkyIDQuNTMzMzQwNDU0MTAxNTYyIDEwLjkxMzgyNzg5NjExODE2IDQuMzk2NDUwMDQyNzI0NjA5IDEwLjUwOTcxNzk0MTI4NDE4IDQuMTU3MzEwNDg1ODM5ODQ0IEMgOC44MjU5NDg3MTUyMDk5NjEgNC4xMDcyODA3MzEyMDExNzIgOC4xMjY4NTc3NTc1NjgzNTkgNC4wMDU5NDA0MzczMTY4OTUgOC4wMzI3Mzk2MzkyODIyMjcgMy41ODY1MDAxNjc4NDY2OCBDIDcuOTYyODQ4NjYzMzMwMDc4IDIuOTY4MzUwNDEwNDYxNDI2IDguMjU2NDU4MjgyNDcwNzAzIDMuMDMwNjkwMTkzMTc2MjcgOC40OTA2MTc3NTIwNzUxOTUgMi4yMjQ4NjAxOTEzNDUyMTUgQyA4LjcyNDc2OTU5MjI4NTE1NiAxLjQxOTAzMDE4OTUxNDE2IDcuNDkwNzc3OTY5MzYwMzUyIC0wLjI2OTc0OTY0MTQxODQ1NyA3LjQ5MDc3Nzk2OTM2MDM1MiAtMC4yNjk3NDk2NDE0MTg0NTcgTCAyMS4xMDEwNjg0OTY3MDQxIC0wLjM5MzY1OTU5MTY3NDgwNDcgWiIgc3Ryb2tlPSJub25lIiBmaWxsPSIjZmZmIi8+CiAgICAgIDwvZz4KICAgICAgPGcgaWQ9IkdydXBwZV81MTI0IiBkYXRhLW5hbWU9IkdydXBwZSA1MTI0IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSg0LjEzOCAtMikiPgogICAgICAgIDxnIGlkPSJQZmFkXzQxMjciIGRhdGEtbmFtZT0iUGZhZCA0MTI3IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgyNjEyLjExOSAyMDIpIHJvdGF0ZSg4KSIgZmlsbD0ibm9uZSI+CiAgICAgICAgICA8cGF0aCBkPSJNMywwaDI0LjA0YTMsMywwLDAsMSwzLDNWNS41MzVhMy42MTMsMy42MTMsMCwwLDEtMy44MjMsMy4xOTJjLS4xMTUsNS41MjMtLjIzOCw2LjIxOC0xLjM1Nyw2LjIxOCwwLDAtMTYuMzQyLjI1OC0xOC45MzguMTM0cy0zLjAzNS0xLjc0NC0zLjEtMi40MDlTMi45LDguNDEsMi45LDguNDFBMy4zLDMuMywwLDAsMSwwLDUuNTM1VjNBMywzLDAsMCwxLDMsMFoiIHN0cm9rZT0ibm9uZSIvPgogICAgICAgICAgPHBhdGggZD0iTSAyLjk5Njk0ODI0MjE4NzUgMC45OTk5OTcxMzg5NzcwNTA4IEMgMS44OTU4MjgyNDcwNzAzMTIgMC45OTk5OTcxMzg5NzcwNTA4IDAuOTk5OTk4MDkyNjUxMzY3MiAxLjg5NzE5Njc2OTcxNDM1NSAwLjk5OTk5ODA5MjY1MTM2NzIgMi45OTk5OTcxMzg5NzcwNTEgTCAwLjk5OTk5ODA5MjY1MTM2NzIgNS41MzQ2MzY0OTc0OTc1NTkgQyAwLjk5OTk5ODA5MjY1MTM2NzIgNi41NjA4ODYzODMwNTY2NDEgMi4zNzc3Mzg5NTI2MzY3MTkgNy40MDE1MjY5Mjc5NDc5OTggMi45MTg1MzkwNDcyNDEyMTEgNy40MTA1NDY3Nzk2MzI1NjggTCAzLjk0NDUyODU3OTcxMTkxNCA3LjQyNzY0NjYzNjk2Mjg5MSBMIDMuOTAwOTY4NTUxNjM1NzQyIDguNDUyODU3MDE3NTE3MDkgQyAzLjgzODgyOTA0MDUyNzM0NCA5LjkxNTQwNzE4MDc4NjEzMyAzLjc2OTYyODUyNDc4MDI3MyAxMi4xNTk3ODcxNzgwMzk1NSAzLjgxMDMxNzk5MzE2NDA2MiAxMi41NzAzODY4ODY1OTY2OCBDIDMuODc0MTg5Mzc2ODMxMDU1IDEzLjIxNDczNjkzODQ3NjU2IDQuMjk5NjI5MjExNDI1NzgxIDEzLjk5OTYyNzExMzM0MjI5IDUuOTYzNzU4NDY4NjI3OTMgMTQuMDc5NTk2NTE5NDcwMjEgQyA2LjQxNzczNzk2MDgxNTQzIDE0LjEwMTQxNjU4NzgyOTU5IDcuMzYxMDM4MjA4MDA3ODEyIDE0LjExMjQ3NjM0ODg3Njk1IDguNzY3NDY5NDA2MTI3OTMgMTQuMTEyNDc2MzQ4ODc2OTUgQyAxNC4xNzc4NzkzMzM0OTYwOSAxNC4xMTI0NzYzNDg4NzY5NSAyNC43MzE1OTc5MDAzOTA2MiAxMy45NDY1MTY5OTA2NjE2MiAyNC44Mzc1NjgyODMwODEwNSAxMy45NDQ4NDcxMDY5MzM1OSBMIDI0Ljg1MzM4OTczOTk5MDIzIDEzLjk0NDcxNjQ1MzU1MjI1IEMgMjQuODU3NDMzMzE5MDkxOCAxMy45NDQ3MTY0NTM1NTIyNSAyNC44NjEzNTQ4Mjc4ODA4NiAxMy45NDQ3MDIxNDg0Mzc1IDI0Ljg2NTE1NjE3MzcwNjA1IDEzLjk0NDY3MzUzODIwODAxIEMgMjQuOTE0NDcwNjcyNjA3NDIgMTMuODAzNDcxNTY1MjQ2NTggMjQuOTk0NDMyNDQ5MzQwODIgMTMuNDc1NTEyNTA0NTc3NjQgMjUuMDU2ODA4NDcxNjc5NjkgMTIuNzQ0OTM2OTQzMDU0MiBDIDI1LjEzMzgzODY1MzU2NDQ1IDExLjg0MjY3NzExNjM5NDA0IDI1LjE3Mjg5OTI0NjIxNTgyIDEwLjUzMDM5NzQxNTE2MTEzIDI1LjIxMDk1ODQ4MDgzNDk2IDguNzA1NTA3Mjc4NDQyMzgzIEwgMjUuMjMwNjA5ODkzNzk4ODMgNy43NjMyMTY5NzIzNTEwNzQgTCAyNi4xNzI0MDkwNTc2MTcxOSA3LjcyNzA4NzAyMDg3NDAyMyBDIDI3LjI5ODg1ODY0MjU3ODEyIDcuNjgzODg3MDA0ODUyMjk1IDI4LjExNTkwOTU3NjQxNjAyIDcuMzAzMzY2NjYxMDcxNzc3IDI4LjYwMDg3OTY2OTE4OTQ1IDYuNTk2MDk2OTkyNDkyNjc2IEMgMjguOTM2ODQzODcyMDcwMzEgNi4xMDYxMzgyMjkzNzAxMTcgMjkuMDE4NDg3OTMwMjk3ODUgNS42MDA3ODgxMTY0NTUwNzggMjkuMDMzNDM5NjM2MjMwNDcgNS40ODQyMDMzMzg2MjMwNDcgTCAyOS4wMzM0Mzk2MzYyMzA0NyAyLjk5OTk5NzEzODk3NzA1MSBDIDI5LjAzMzQzOTYzNjIzMDQ3IDEuODk3MTk2NzY5NzE0MzU1IDI4LjEzNzYwOTQ4MTgxMTUyIDAuOTk5OTk3MTM4OTc3MDUwOCAyNy4wMzY0ODk0ODY2OTQzNCAwLjk5OTk5NzEzODk3NzA1MDggTCAyLjk5Njk0ODI0MjE4NzUgMC45OTk5OTcxMzg5NzcwNTA4IE0gMi45OTY5NDgyNDIxODc1IC0yLjg2MTAyMjk0OTIxODc1ZS0wNiBMIDI3LjAzNjQ4OTQ4NjY5NDM0IC0yLjg2MTAyMjk0OTIxODc1ZS0wNiBDIDI4LjY5MTY1ODAyMDAxOTUzIC0yLjg2MTAyMjk0OTIxODc1ZS0wNiAzMC4wMzM0Mzk2MzYyMzA0NyAxLjM0MzE0NzI3NzgzMjAzMSAzMC4wMzM0Mzk2MzYyMzA0NyAyLjk5OTk5NzEzODk3NzA1MSBMIDMwLjAzMzQzOTYzNjIzMDQ3IDUuNTM0NjM2NDk3NDk3NTU5IEMgMzAuMDMzNDM5NjM2MjMwNDcgNS41MzQ2MzY0OTc0OTc1NTkgMjkuODM0MzM5MTQxODQ1NyA4LjU4NzM2NzA1NzgwMDI5MyAyNi4yMTA3MzkxMzU3NDIxOSA4LjcyNjM1NjUwNjM0NzY1NiBDIDI2LjA5NTU2OTYxMDU5NTcgMTQuMjQ5Mjc3MTE0ODY4MTYgMjUuOTcyMjkwMDM5MDYyNSAxNC45NDQ3MTY0NTM1NTIyNSAyNC44NTMzODk3Mzk5OTAyMyAxNC45NDQ3MTY0NTM1NTIyNSBDIDI0Ljg1MzM4OTczOTk5MDIzIDE0Ljk0NDcxNjQ1MzU1MjI1IDguNTExODg0Njg5MzMxMDU1IDE1LjIwMzIxNjU1MjczNDM4IDUuOTE1NzU4MTMyOTM0NTcgMTUuMDc4NDQ2Mzg4MjQ0NjMgQyAzLjMxOTYyOTY2OTE4OTQ1MyAxNC45NTM2ODY3MTQxNzIzNiAyLjg4MTE3OTgwOTU3MDMxMiAxMy4zMzQ3MDcyNjAxMzE4NCAyLjgxNTE5ODg5ODMxNTQzIDEyLjY2OTAxNjgzODA3MzczIEMgMi43NDkyMTc5ODcwNjA1NDcgMTIuMDAzMzM2OTA2NDMzMTEgMi45MDE4Njg4MjAxOTA0MyA4LjQxMDQwNzA2NjM0NTIxNSAyLjkwMTg2ODgyMDE5MDQzIDguNDEwNDA3MDY2MzQ1MjE1IEMgMS44ODU3MTkyOTkzMTY0MDYgOC4zOTM0NjY5NDk0NjI4OTEgLTEuOTA3MzQ4NjMyODEyNWUtMDYgNy4xOTE0ODczMTIzMTY4OTUgLTEuOTA3MzQ4NjMyODEyNWUtMDYgNS41MzQ2MzY0OTc0OTc1NTkgTCAtMS45MDczNDg2MzI4MTI1ZS0wNiAyLjk5OTk5NzEzODk3NzA1MSBDIC0xLjkwNzM0ODYzMjgxMjVlLTA2IDEuMzQzMTQ3Mjc3ODMyMDMxIDEuMzQxNzc5NzA4ODYyMzA1IC0yLjg2MTAyMjk0OTIxODc1ZS0wNiAyLjk5Njk0ODI0MjE4NzUgLTIuODYxMDIyOTQ5MjE4NzVlLTA2IFoiIHN0cm9rZT0ibm9uZSIgZmlsbD0iI2ZmZiIvPgogICAgICAgIDwvZz4KICAgICAgICA8ZyBpZD0iUmVjaHRlY2tfMTQ2MCIgZGF0YS1uYW1lPSJSZWNodGVjayAxNDYwIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgyNjA4LjAxNiAyMDQuMDY2KSByb3RhdGUoOCkiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxIj4KICAgICAgICAgIDxwYXRoIGQ9Ik0xLjQ5MSwwaDIuNjRhMCwwLDAsMCwxLDAsMFYyLjk4MmEwLDAsMCwwLDEsMCwwSDEuNDkxQTEuNDkxLDEuNDkxLDAsMCwxLDAsMS40OTF2MEExLjQ5MSwxLjQ5MSwwLDAsMSwxLjQ5MSwwWiIgc3Ryb2tlPSJub25lIi8+CiAgICAgICAgICA8cGF0aCBkPSJNMS40OTEuNWgyLjE0YTAsMCwwLDAsMSwwLDBWMi40ODJhMCwwLDAsMCwxLDAsMEgxLjQ5MUEuOTkxLjk5MSwwLDAsMSwuNSwxLjQ5MXYwQS45OTEuOTkxLDAsMCwxLDEuNDkxLjVaIiBmaWxsPSJub25lIi8+CiAgICAgICAgPC9nPgogICAgICAgIDxnIGlkPSJSZWNodGVja18xNDYxIiBkYXRhLW5hbWU9IlJlY2h0ZWNrIDE0NjEiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDI2MDMuNjg5IDIwNC4yOTUpIHJvdGF0ZSg4KSIgZmlsbD0iI2ZmZiIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEiPgogICAgICAgICAgPHBhdGggZD0iTS42MTcsMEg0LjY1YTAsMCwwLDAsMSwwLDBWMS4yMzRhMCwwLDAsMCwxLDAsMEguNjE3QS42MTcuNjE3LDAsMCwxLDAsLjYxN3YwQS42MTcuNjE3LDAsMCwxLC42MTcsMFoiIHN0cm9rZT0ibm9uZSIvPgogICAgICAgICAgPHBhdGggZD0iTS42MTcuNUg0LjE1YTAsMCwwLDAsMSwwLDBWLjczNGEwLDAsMCwwLDEsMCwwSC42MTdBLjExNy4xMTcsMCwwLDEsLjUuNjE3djBBLjExNy4xMTcsMCwwLDEsLjYxNy41WiIgZmlsbD0ibm9uZSIvPgogICAgICAgIDwvZz4KICAgICAgICA8ZyBpZD0iUmVjaHRlY2tfMTUxNSIgZGF0YS1uYW1lPSJSZWNodGVjayAxNTE1IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgyNjEzLjgwNSAyMDUuMjMpIHJvdGF0ZSg4KSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjAuNyI+CiAgICAgICAgICA8cmVjdCB3aWR0aD0iOC42MzciIGhlaWdodD0iMi45ODIiIHJ4PSIwLjUiIHN0cm9rZT0ibm9uZSIvPgogICAgICAgICAgPHJlY3QgeD0iMC4zNSIgeT0iMC4zNSIgd2lkdGg9IjcuOTM3IiBoZWlnaHQ9IjIuMjgyIiByeD0iMC4xNSIgZmlsbD0ibm9uZSIvPgogICAgICAgIDwvZz4KICAgICAgPC9nPgogICAgICA8ZyBpZD0iR3J1cHBlXzUxMjUiIGRhdGEtbmFtZT0iR3J1cHBlIDUxMjUiPgogICAgICAgIDxsaW5lIGlkPSJMaW5pZV81NjgiIGRhdGEtbmFtZT0iTGluaWUgNTY4IiB4Mj0iMy4zMiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjYyMy41MjEgMjMzKSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS13aWR0aD0iMC43Ii8+CiAgICAgICAgPGxpbmUgaWQ9IkxpbmllXzU2OSIgZGF0YS1uYW1lPSJMaW5pZSA1NjkiIHgyPSIzLjMyIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgyNjIzLjUyMSAyMzQuNDczKSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS13aWR0aD0iMC43Ii8+CiAgICAgICAgPGxpbmUgaWQ9IkxpbmllXzU3MCIgZGF0YS1uYW1lPSJMaW5pZSA1NzAiIHgyPSIzLjMyIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgyNjIzLjUyMSAyMzUuOTQ5KSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS13aWR0aD0iMC43Ii8+CiAgICAgIDwvZz4KICAgICAgPGcgaWQ9IlBmYWRfNDEyOCIgZGF0YS1uYW1lPSJQZmFkIDQxMjgiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDI2NDUuMzg3IDIwNi4xOTQpIHJvdGF0ZSg4KSIgZmlsbD0ibm9uZSI+CiAgICAgICAgPHBhdGggZD0iTS4wODYtLjE0OCwxMiwwYTEsMSwwLDAsMSwxLDFWNGExLDEsMCwwLDEtMSwxTC0uMjUsNC43NjFjLS41NTIsMC0uMTMxLS4zNzgtLjEzMS0uOTNMLS4zNDQuNjI0Qy0uMzQ0LjA3Mi0uNDY3LS4xNDguMDg2LS4xNDhaIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cGF0aCBkPSJNIDAuMTQ4NzgxNzc2NDI4MjIyNyAwLjM1MjY4NTkyODM0NDcyNjYgQyAwLjE1MjEwMTUxNjcyMzYzMjggMC40MzE2OTczNjg2MjE4MjYyIDAuMTU1ODAxNzczMDcxMjg5MSAwLjUyMTEyNjc0NzEzMTM0NzcgMC4xNTU4MDE3NzMwNzEyODkxIDAuNjI0MjkzODA0MTY4NzAxMiBMIDAuMTU1NzcxMjU1NDkzMTY0MSAwLjYyOTk5MzkxNTU1Nzg2MTMgTCAwLjExOTIzNzg5OTc4MDI3MzQgMy44MzM4OTk0OTc5ODU4NCBDIDAuMTE4ODk3NDM4MDQ5MzE2NCAzLjk5NTgxODYxNDk1OTcxNyAwLjA5NDEwOTUzNTIxNzI4NTE2IDQuMTQxMTMwNDQ3Mzg3Njk1IDAuMDYzNDk5NDUwNjgzNTkzNzUgNC4yNjY4NDQ3NDk0NTA2ODQgTCAxMi4wMDM4NTY2NTg5MzU1NSA0LjQ5OTk4ODU1NTkwODIwMyBDIDEyLjI3Nzc5OTYwNjMyMzI0IDQuNDk3OTIwOTg5OTkwMjM0IDEyLjUwMDAwMTkwNzM0ODYzIDQuMjc0NDI1MDI5NzU0NjM5IDEyLjUwMDAwMTkwNzM0ODYzIDQuMDAwMDAzODE0Njk3MjY2IEwgMTIuNTAwMDAxOTA3MzQ4NjMgMS4wMDAwMDM4MTQ2OTcyNjYgQyAxMi41MDAwMDE5MDczNDg2MyAwLjcyNDMwMzcyMjM4MTU5MTggMTIuMjc1NzAxNTIyODI3MTUgMC41MDAwMDM4MTQ2OTcyNjU2IDEyLjAwMDAwMTkwNzM0ODYzIDAuNTAwMDAzODE0Njk3MjY1NiBMIDExLjk5Mzc4MjA0MzQ1NzAzIDAuNDk5OTYzNzYwMzc1OTc2NiBMIDAuMTQ4NzgxNzc2NDI4MjIyNyAwLjM1MjY4NTkyODM0NDcyNjYgTSAwLjA4NTY4MTkxNTI4MzIwMzEyIC0wLjE0ODEzNjEzODkxNjAxNTYgTCAxMi4wMDAwMDE5MDczNDg2MyAzLjgxNDY5NzI2NTYyNWUtMDYgQyAxMi41NTIyODEzNzk2OTk3MSAzLjgxNDY5NzI2NTYyNWUtMDYgMTMuMDAwMDAxOTA3MzQ4NjMgMC40NDc3MTM4NTE5Mjg3MTA5IDEzLjAwMDAwMTkwNzM0ODYzIDEuMDAwMDAzODE0Njk3MjY2IEwgMTMuMDAwMDAxOTA3MzQ4NjMgNC4wMDAwMDM4MTQ2OTcyNjYgQyAxMy4wMDAwMDE5MDczNDg2MyA0LjU1MjI4Mzc2Mzg4NTQ5OCAxMi41NTIyODEzNzk2OTk3MSA1LjAwMDAwMzgxNDY5NzI2NiAxMi4wMDAwMDE5MDczNDg2MyA1LjAwMDAwMzgxNDY5NzI2NiBMIC0wLjI1MDAwODU4MzA2ODg0NzcgNC43NjA4MTM3MTMwNzM3MyBDIC0wLjgwMjI5ODU0NTgzNzQwMjMgNC43NjA4MTM3MTMwNzM3MyAtMC4zODA3NTgyODU1MjI0NjA5IDQuMzgyNzkzOTAzMzUwODMgLTAuMzgwNzU4Mjg1NTIyNDYwOSAzLjgzMDUwMzk0MDU4MjI3NSBMIC0wLjM0NDE5ODIyNjkyODcxMDkgMC42MjQyOTM4MDQxNjg3MDEyIEMgLTAuMzQ0MTk4MjI2OTI4NzEwOSAwLjA3MjAwMzg0MTQwMDE0NjQ4IC0wLjQ2NjU5ODUxMDc0MjE4NzUgLTAuMTQ4MTM2MTM4OTE2MDE1NiAwLjA4NTY4MTkxNTI4MzIwMzEyIC0wLjE0ODEzNjEzODkxNjAxNTYgWiIgc3Ryb2tlPSJub25lIiBmaWxsPSIjZmZmIi8+CiAgICAgIDwvZz4KICAgIDwvZz4KICA8L2c+Cjwvc3ZnPgo="
    elif task == "Smartlabel":
        return "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj4KICA8ZyBpZD0iR3J1cHBlXzUwNzAiIGRhdGEtbmFtZT0iR3J1cHBlIDUwNzAiIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0xNzk5IC04ODMpIj4KICAgIDxnIGlkPSJHcnVwcGVfNTA2NyIgZGF0YS1uYW1lPSJHcnVwcGUgNTA2NyI+CiAgICAgIDxnIGlkPSJHcnVwcGVfNDgwOCIgZGF0YS1uYW1lPSJHcnVwcGUgNDgwOCI+CiAgICAgICAgPHBhdGggaWQ9IlBmYWRfMzQwNCIgZGF0YS1uYW1lPSJQZmFkIDM0MDQiIGQ9Ik0wLDBINDVWNDVIMFoiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDE4MDcuODcxIDg5MC41KSIgZmlsbD0ibm9uZSIvPgogICAgICAgIDxwYXRoIGlkPSJQZmFkXzMzNTYiIGRhdGEtbmFtZT0iUGZhZCAzMzU2IiBkPSJNMywxLjVBMS41LDEuNSwwLDAsMCwxLjUsM1YyN0ExLjUsMS41LDAsMCwwLDMsMjguNUg0MC4zN2ExLjUsMS41LDAsMCwwLDEuNS0xLjVWM2ExLjUsMS41LDAsMCwwLTEuNS0xLjVIM00zLDBINDAuMzdhMywzLDAsMCwxLDMsM1YyN2EzLDMsMCwwLDEtMywzSDNhMywzLDAsMCwxLTMtM1YzQTMsMywwLDAsMSwzLDBaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxODA3LjMxNiA4OTgpIiBmaWxsPSIjZmZmIi8+CiAgICAgICAgPGcgaWQ9IkdydXBwZV80NzY5IiBkYXRhLW5hbWU9IkdydXBwZSA0NzY5Ij4KICAgICAgICAgIDxwYXRoIGlkPSJQZmFkXzMzNjAiIGRhdGEtbmFtZT0iUGZhZCAzMzYwIiBkPSJNMCwwSDNWMTQuMDA4SDBaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxODE0IDkwNS45OTIpIiBmaWxsPSIjZmZmIi8+CiAgICAgICAgICA8cGF0aCBpZD0iUGZhZF8zMzYxIiBkYXRhLW5hbWU9IlBmYWQgMzM2MSIgZD0iTTMsMEg2QTMsMywwLDAsMSw5LDNIMEEzLDMsMCwwLDEsMywwWiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTgxMSA5MDQpIiBmaWxsPSIjZmZmIi8+CiAgICAgICAgPC9nPgogICAgICA8L2c+CiAgICA8L2c+CiAgICA8bGluZSBpZD0iTGluaWVfNTYzIiBkYXRhLW5hbWU9IkxpbmllIDU2MyIgeDI9IjEwIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxODIzLjI1IDkwOCkiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2Utd2lkdGg9IjIiLz4KICAgIDxsaW5lIGlkPSJMaW5pZV81NjQiIGRhdGEtbmFtZT0iTGluaWUgNTY0IiB4Mj0iMjIiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDE4MjMuMjUgOTEzKSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS13aWR0aD0iMiIvPgogICAgPGxpbmUgaWQ9IkxpbmllXzU2NSIgZGF0YS1uYW1lPSJMaW5pZSA1NjUiIHgyPSIyMiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTgyMy4yNSA5MTgpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIyIi8+CiAgPC9nPgo8L3N2Zz4K"
    elif task == "Pick_to_Light":
        return "data:image/svg+xml;base64,PHN2ZyBpZD0iQ2xpZW50X1RBRl9QVEwiIGRhdGEtbmFtZT0iQ2xpZW50IFRBRiBQVEwiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgd2lkdGg9IjYwIiBoZWlnaHQ9IjYwIiB2aWV3Qm94PSIwIDAgNjAgNjAiPgogIDxyZWN0IGlkPSJSZWNodGVja18xMTU0IiBkYXRhLW5hbWU9IlJlY2h0ZWNrIDExNTQiIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoNy41IDcuNSkiIGZpbGw9Im5vbmUiLz4KICA8ZyBpZD0iR3J1cHBlXzQ0NDEiIGRhdGEtbmFtZT0iR3J1cHBlIDQ0NDEiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDExLjI1IDExLjI1KSI+CiAgICA8cGF0aCBpZD0iRWxsaXBzZV80NDEiIGRhdGEtbmFtZT0iRWxsaXBzZSA0NDEiIGQ9Ik04Ljc1LDEuMjVhNy41LDcuNSwwLDEsMCw3LjUsNy41LDcuNTA4LDcuNTA4LDAsMCwwLTcuNS03LjVNOC43NSwwQTguNzUsOC43NSwwLDEsMSwwLDguNzUsOC43NSw4Ljc1LDAsMCwxLDguNzUsMFoiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDEwLjAwMSAxMC4wMDEpIiBmaWxsPSIjZmZmIi8+CiAgICA8cGF0aCBpZD0iTGluZV80NjUiIGRhdGEtbmFtZT0iTGluZSA0NjUiIGQ9Ik0xNi4wNzUuNzVILjEyNWEuNjI1LjYyNSwwLDEsMSwwLTEuMjVoMTUuOTVhLjYyNS42MjUsMCwxLDEsMCwxLjI1WiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTAuNjUxIDE4LjYyNikiIGZpbGw9IiNmZmYiLz4KICAgIDxwYXRoIGlkPSJQb2x5Z29uXzM5IiBkYXRhLW5hbWU9IlBvbHlnb24gMzkiIGQ9Ik0zLjYsMi40ODYsMS44NjksNS45NDFINS4zMjNMMy42LDIuNDg2aDBtMC0xLjI1YTEuMjM2LDEuMjM2LDAsMCwxLDEuMTE4LjY5MUw2LjQ0MSw1LjM4MkExLjI1LDEuMjUsMCwwLDEsNS4zMjMsNy4xOTFIMS44NjhBMS4yNSwxLjI1LDAsMCwxLC43NSw1LjM4MkwyLjQ3OCwxLjkyN0ExLjIzNiwxLjIzNiwwLDAsMSwzLjYsMS4yMzZaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxNS4xNTQgMS41NjEpIiBmaWxsPSIjZmZmIi8+CiAgICA8cGF0aCBpZD0iUG9seWdvbl80MCIgZGF0YS1uYW1lPSJQb2x5Z29uIDQwIiBkPSJNMi45NzksMS4yNSwxLjI1Miw0LjdINC43MDZMMi45NzksMS4yNWgwbTAtMS4yNUExLjIzNiwxLjIzNiwwLDAsMSw0LjEuNjkxTDUuODI1LDQuMTQ2QTEuMjUsMS4yNSwwLDAsMSw0LjcwNyw1Ljk1NUgxLjI1MkExLjI1LDEuMjUsMCwwLDEsLjEzNCw0LjE0NkwxLjg2MS42OTFBMS4yMzYsMS4yMzYsMCwwLDEsMi45NzksMFoiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDIxLjcyOSAzNC43MDYpIHJvdGF0ZSgxODApIiBmaWxsPSIjZmZmIi8+CiAgICA8cGF0aCBpZD0iUmVjdGFuZ2xlXzEwNjciIGRhdGEtbmFtZT0iUmVjdGFuZ2xlIDEwNjciIGQ9Ik0zLjc1LDEuMjVhMi41LDIuNSwwLDAsMC0yLjUsMi41djMwYTIuNSwyLjUsMCwwLDAsMi41LDIuNWgzMGEyLjUsMi41LDAsMCwwLDIuNS0yLjV2LTMwYTIuNSwyLjUsMCwwLDAtMi41LTIuNWgtMzBNMy43NSwwaDMwQTMuNzUsMy43NSwwLDAsMSwzNy41LDMuNzV2MzBhMy43NSwzLjc1LDAsMCwxLTMuNzUsMy43NWgtMzBBMy43NSwzLjc1LDAsMCwxLDAsMzMuNzV2LTMwQTMuNzUsMy43NSwwLDAsMSwzLjc1LDBaIiBmaWxsPSIjZmZmIi8+CiAgPC9nPgo8L3N2Zz4K"
    elif task == "SmartTower":
        return "data:image/svg+xml;base64,PHN2ZyBpZD0iU21hcnRUb3dlciIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCI+CiAgPGcgaWQ9IkdydXBwZV80OTEyIiBkYXRhLW5hbWU9IkdydXBwZSA0OTEyIj4KICAgIDxnIGlkPSJHcnVwcGVfNDg3OSIgZGF0YS1uYW1lPSJHcnVwcGUgNDg3OSI+CiAgICAgIDxnIGlkPSJHcnVwcGVfNDg3OCIgZGF0YS1uYW1lPSJHcnVwcGUgNDg3OCI+CiAgICAgICAgPGcgaWQ9IkNsaWVudF9UQUZfUFRMIiBkYXRhLW5hbWU9IkNsaWVudCBUQUYgUFRMIj4KICAgICAgICAgIDxyZWN0IGlkPSJSZWNodGVja18xMTU0IiBkYXRhLW5hbWU9IlJlY2h0ZWNrIDExNTQiIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoNy41IDcuNSkiIGZpbGw9Im5vbmUiLz4KICAgICAgICAgIDxnIGlkPSJFbGxpcHNlXzUwNiIgZGF0YS1uYW1lPSJFbGxpcHNlIDUwNiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjIgMjIpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMyI+CiAgICAgICAgICAgIDxjaXJjbGUgY3g9IjgiIGN5PSI4IiByPSI4IiBzdHJva2U9Im5vbmUiLz4KICAgICAgICAgICAgPGNpcmNsZSBjeD0iOCIgY3k9IjgiIHI9IjYuNSIgZmlsbD0ibm9uZSIvPgogICAgICAgICAgPC9nPgogICAgICAgIDwvZz4KICAgICAgPC9nPgogICAgPC9nPgogICAgPHBhdGggaWQ9IlBmYWRfNDAxNCIgZGF0YS1uYW1lPSJQZmFkIDQwMTQiIGQ9Ik0yNy4yNSwxOC4xNTZoMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNzA3MDcwIiBzdHJva2Utd2lkdGg9IjEiLz4KICAgIDxwYXRoIGlkPSJQZmFkXzQwMTUiIGRhdGEtbmFtZT0iUGZhZCA0MDE1IiBkPSJNMjUsMTEuN0gzNWwtMi45MDYsOC45ODQtMi0uMzEyLTIuMDE2LjMxM1oiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLWxpbmVjYXA9InNxdWFyZSIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIxLjQiLz4KICAgIDxwYXRoIGlkPSJQZmFkXzQwMTYiIGRhdGEtbmFtZT0iUGZhZCA0MDE2IiBkPSJNMjUsMTEuN0gzNWwtMi45MDYsOC45ODQtMi0uMzEyLTIuMDE2LjMxM1oiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDYwLjE5NSAwKSByb3RhdGUoOTApIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJzcXVhcmUiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIHN0cm9rZS13aWR0aD0iMS40Ii8+CiAgICA8cGF0aCBpZD0iUGZhZF80MDE3IiBkYXRhLW5hbWU9IlBmYWQgNDAxNyIgZD0iTTI1LDExLjdIMzVsLTIuOTA2LDguOTg0LTItLjMxMi0yLjAxNi4zMTNaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSg2MCA2MC4xOTUpIHJvdGF0ZSgxODApIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJzcXVhcmUiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIHN0cm9rZS13aWR0aD0iMS40Ii8+CiAgICA8cGF0aCBpZD0iUGZhZF80MDE4IiBkYXRhLW5hbWU9IlBmYWQgNDAxOCIgZD0iTTI1LDExLjdIMzVsLTIuOTA2LDguOTg0LTItLjMxMi0yLjAxNi4zMTNaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgtMC4xOTUgNjApIHJvdGF0ZSgtOTApIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJzcXVhcmUiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIHN0cm9rZS13aWR0aD0iMS40Ii8+CiAgICA8cGF0aCBpZD0iUGZhZF80MDE5IiBkYXRhLW5hbWU9IlBmYWQgNDAxOSIgZD0iTTI1LDExLjdIMzVsLTIuOTA2LDguOTg0LTItLjMxMi0yLjAxNi4zMTNaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgtMTIuNDkgMzAuNDg2KSByb3RhdGUoLTQ2KSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2UtbGluZWNhcD0ic3F1YXJlIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBzdHJva2Utd2lkdGg9IjEuNCIvPgogICAgPHBhdGggaWQ9IlBmYWRfNDAyMCIgZGF0YS1uYW1lPSJQZmFkIDQwMjAiIGQ9Ik0yNSwxMS43SDM1bC0yLjkwNiw4Ljk4NC0yLS4zMTItMi4wMTYuMzEzWiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMzAuMjU0IC0xMi40NzUpIHJvdGF0ZSg0NSkiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLWxpbmVjYXA9InNxdWFyZSIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIxLjQiLz4KICAgIDxwYXRoIGlkPSJQZmFkXzQwMjEiIGRhdGEtbmFtZT0iUGZhZCA0MDIxIiBkPSJNMCwwSDEwTDcuMDk1LDguOTg1bC0yLS4zMTMtMi4wMTYuMzEyWiIgdHJhbnNmb3JtPSJtYXRyaXgoLTAuNzE5LCAtMC42OTUsIDAuNjk1LCAtMC43MTksIDIwLjU5MywgNDYuODEpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJzcXVhcmUiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIHN0cm9rZS13aWR0aD0iMS40Ii8+CiAgICA8cGF0aCBpZD0iUGZhZF80MDIyIiBkYXRhLW5hbWU9IlBmYWQgNDAyMiIgZD0iTTAsMEgxMEw3LjA5NSw4Ljk4NWwtMi0uMzEzLTIuMDE2LjMxMloiIHRyYW5zZm9ybT0ibWF0cml4KC0wLjY4MiwgMC43MzEsIC0wLjczMSwgLTAuNjgyLCA0Ni45NTIsIDM4Ljk3NykiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLWxpbmVjYXA9InNxdWFyZSIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIxLjQiLz4KICA8L2c+Cjwvc3ZnPgo="
    elif task == "Info":
        return "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj4KICA8ZyBpZD0iR3J1cHBlXzUwNjkiIGRhdGEtbmFtZT0iR3J1cHBlIDUwNjkiIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0xNDg3IC04ODMpIj4KICAgIDxnIGlkPSJDbGllbnRfVEFGX0luZm8iIGRhdGEtbmFtZT0iQ2xpZW50IFRBRiBJbmZvIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxNDg3IDg4MykiPgogICAgICA8cmVjdCBpZD0iUmVjaHRlY2tfMTE2MyIgZGF0YS1uYW1lPSJSZWNodGVjayAxMTYzIiB3aWR0aD0iNDUiIGhlaWdodD0iNDUiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDcuNDUzIDcuNSkiIGZpbGw9Im5vbmUiLz4KICAgICAgPHBhdGggaWQ9IlBmYWRfMjc2OSIgZGF0YS1uYW1lPSJQZmFkIDI3NjkiIGQ9Ik04LDhoNC40NDdWMTkuMTE2SDhaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxOS41MTYgMTkuNzczKSIgZmlsbD0iI2ZmZiIvPgogICAgICA8cGF0aCBpZD0iUGZhZF8yNzcwIiBkYXRhLW5hbWU9IlBmYWQgMjc3MCIgZD0iTTgsNWg0LjQ0N1Y5LjQ0N0g4WiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTkuNTE2IDE2LjEwNSkiIGZpbGw9IiNmZmYiLz4KICAgICAgPHBhdGggaWQ9IkVsbGlwc2VfNTIwIiBkYXRhLW5hbWU9IkVsbGlwc2UgNTIwIiBkPSJNMTgsMkExNiwxNiwwLDAsMCw2LjY4NiwyOS4zMTQsMTYsMTYsMCwwLDAsMjkuMzE0LDYuNjg2LDE1LjksMTUuOSwwLDAsMCwxOCwybTAtMkExOCwxOCwwLDEsMSwwLDE4LDE4LDE4LDAsMCwxLDE4LDBaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxMiAxMikiIGZpbGw9IiNmZmYiLz4KICAgIDwvZz4KICA8L2c+Cjwvc3ZnPgo="
    elif task == "ChecklistItem":
        return "data:image/svg+xml;base64,PHN2ZyBpZD0iRnJlZV9DaG9pY2UiIGRhdGEtbmFtZT0iRnJlZSBDaG9pY2UiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgd2lkdGg9IjYwIiBoZWlnaHQ9IjYwIiB2aWV3Qm94PSIwIDAgNjAgNjAiPgogIDxnIGlkPSJHcnVwcGVfNDg3OCIgZGF0YS1uYW1lPSJHcnVwcGUgNDg3OCI+CiAgICA8ZyBpZD0iQ2xpZW50X1RBRl9QVEwiIGRhdGEtbmFtZT0iQ2xpZW50IFRBRiBQVEwiPgogICAgICA8ZyBpZD0iR3J1cHBlXzQ5NDYiIGRhdGEtbmFtZT0iR3J1cHBlIDQ5NDYiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDE2Ljc2MiAyNykiPgogICAgICAgIDxnIGlkPSJSZWNodGVja18xNDI0IiBkYXRhLW5hbWU9IlJlY2h0ZWNrIDE0MjQiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDAgLTIwKSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEuMiI+CiAgICAgICAgICA8cmVjdCB3aWR0aD0iMjYuNDc3IiBoZWlnaHQ9IjgiIHJ4PSIxIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICAgIDxyZWN0IHg9IjAuNiIgeT0iMC42IiB3aWR0aD0iMjUuMjc3IiBoZWlnaHQ9IjYuOCIgcng9IjAuNCIgZmlsbD0ibm9uZSIvPgogICAgICAgIDwvZz4KICAgICAgPC9nPgogICAgICA8ZyBpZD0iUmVjaHRlY2tfMTQyNC0yIiBkYXRhLW5hbWU9IlJlY2h0ZWNrIDE0MjQiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDMuOTgyIDI3LjgzMSkiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjIiPgogICAgICAgIDxyZWN0IHdpZHRoPSIxMy4wMzMiIGhlaWdodD0iNi4xMzkiIHJ4PSIxIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cmVjdCB4PSIwLjYiIHk9IjAuNiIgd2lkdGg9IjExLjgzMyIgaGVpZ2h0PSI0LjkzOSIgcng9IjAuNCIgZmlsbD0ibm9uZSIvPgogICAgICA8L2c+CiAgICAgIDxnIGlkPSJSZWNodGVja18xNDI0LTMiIGRhdGEtbmFtZT0iUmVjaHRlY2sgMTQyNCIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMjMuNDgxIDI3LjgzMSkiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjIiPgogICAgICAgIDxyZWN0IHdpZHRoPSIxMy4wMzMiIGhlaWdodD0iNi4xMzkiIHJ4PSIxIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cmVjdCB4PSIwLjYiIHk9IjAuNiIgd2lkdGg9IjExLjgzMyIgaGVpZ2h0PSI0LjkzOSIgcng9IjAuNCIgZmlsbD0ibm9uZSIvPgogICAgICA8L2c+CiAgICAgIDxnIGlkPSJSZWNodGVja18xNDI0LTQiIGRhdGEtbmFtZT0iUmVjaHRlY2sgMTQyNCIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoNDIuOTgyIDI3LjgzMSkiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjIiPgogICAgICAgIDxyZWN0IHdpZHRoPSIxMy4wMzMiIGhlaWdodD0iNi4xMzkiIHJ4PSIxIiBzdHJva2U9Im5vbmUiLz4KICAgICAgICA8cmVjdCB4PSIwLjYiIHk9IjAuNiIgd2lkdGg9IjExLjgzMyIgaGVpZ2h0PSI0LjkzOSIgcng9IjAuNCIgZmlsbD0ibm9uZSIvPgogICAgICA8L2c+CiAgICA8L2c+CiAgPC9nPgogIDxwYXRoIGlkPSJQZmFkXzQwMDIiIGRhdGEtbmFtZT0iUGZhZCA0MDAyIiBkPSJNMTYuOSwxNi43ODJ2LjE2Mkw5Ljc3LDE5LjczNWEuMTIxLjEyMSwwLDAsMS0uMTcyLS4wODFBMTcuMSwxNy4xLDAsMCwwLDguODgsMThhNC4zNTgsNC4zNTgsMCwwLDAtMS43OS0xLjU3N0M1Ljg1NiwxNS43LDQuOTY3LDE0LjQsMy44MTQsMTMuNTY3Yy0uOC0uNTY2LTIuNjU5LTEuNjA4LTIuNzMtMS42MzhBMS42MzgsMS42MzgsMCwwLDEsLjA3Myw5LjkwNywxLjE2MywxLjE2MywwLDAsMSwuNzksOS4zNGgwYTMuMiwzLjIsMCwwLDEsLjM1NC0uMDYxaC4yNDNhMi45MzMsMi45MzMsMCwwLDEsLjk0LjI3M2gwYy45MS40MzUsMS42NzkuOTQsMi41NTgsMS4zNzVhLjEyMS4xMjEsMCwwLDAsLjE3Mi0uMTIxQTEzLjk1OCwxMy45NTgsMCwwLDAsNC42LDkuNDIxTDEuNjgsMS44MDdBMS4zMzUsMS4zMzUsMCwwLDEsMi40NjkuMSwxLjM1NSwxLjM1NSwwLDAsMSw0LjIxOC44MTZsMS44MSw0LjYyMWgwYTEuMzY1LDEuMzY1LDAsMCwxLC45MS0xLjI1NCwxLjM4NSwxLjM4NSwwLDAsMSwxLjcyOS43NzlsLjI0My42ODhoLjA1MWExLjM3NSwxLjM3NSwwLDAsMSwyLjY0OS0uNDE1bC4yMzMuNjc3SDExLjlhMS4zNjUsMS4zNjUsMCwwLDEsLjkzLTEuMTEyLDEuMywxLjMsMCwwLDEsMS42MDguODlzLjIyMi41NTYuNSwxLjMzNS42LDEuNzcuODI5LDIuNjA5YTExLjQwNiwxMS40MDYsMCwwLDEsLjM1NCwyLjAyMiwyMi40OTEsMjIuNDkxLDAsMCwwLS4xLDIuODYyLDguOTA4LDguOTA4LDAsMCwwLC44OCwyLjI2NVoiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDI3LjcwNCAzNC40OTIpIHJvdGF0ZSgyMCkiIGZpbGw9IiNmZmYiLz4KICA8bGluZSBpZD0iTGluaWVfNTUxIiBkYXRhLW5hbWU9IkxpbmllIDU1MSIgeDE9IjUiIHkyPSI4IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxMC41IDE3LjUpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIxLjUiLz4KICA8bGluZSBpZD0iTGluaWVfNTUyIiBkYXRhLW5hbWU9IkxpbmllIDU1MiIgeDI9IjUiIHkyPSI4IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSg0NC41IDE3LjUpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIxLjUiLz4KICA8bGluZSBpZD0iTGluaWVfNTUzIiBkYXRhLW5hbWU9IkxpbmllIDU1MyIgeTI9IjgiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDMwIDE3LjUpIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLXdpZHRoPSIxLjUiLz4KPC9zdmc+Cg=="
    else:
        return "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI1MCIgaGVpZ2h0PSI1MCIgdmlld0JveD0iMCAwIDQwIDQwLjAwMiI+PHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiByeD0iMjAiIGZpbGw9IiNmZmYiLz48cGF0aCBkPSJNMjA2NTUsMjM1OTNhMjAsMjAsMCwxLDEsMjAsMjBBMjAsMjAsMCwwLDEsMjA2NTUsMjM1OTNabTcuOTc3LTEyLjAyM0ExNywxNywwLDEsMCwyMDY3NSwyMzU3NiwxNi45LDE2LjksMCwwLDAsMjA2NjIuOTc5LDIzNTgwLjk3N1ptNy4xMzUsMy41MjUsMTUuMzg1LDguNS0xNS4zODUsOC41WiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTIwNjU1IC0yMzU3MykiIGZpbGw9IiM0ZGExNjciLz48L3N2Zz4=" # Default to Manual


def instruction_advanced_json_2_elam_flowchart_json(instruction_advanced_json_path, elam_json_path):
    print(f"\n### Start converting advanced instruction JSON to ELAM flowchart JSON ###")
    
    with open(instruction_advanced_json_path, 'r') as file:
        instruction_advanced_json = json.load(file)
    print(f"Loaded advanced instruction JSON from {instruction_advanced_json_path}")
    
    
    # Initialize the flowchart JSON structure
    new_flowchart = {
        "shapes": [],
        "connectors": []
    }

    y_step_size = 3000
    
    # Start and end shapes
    start_shape = {
        "key": "0",
        "customData": {"name": "Start"},
        "locked": False,
        "zIndex": 0,
        "type": "start",
        "text": "Start",
        "x": 0,
        "y": 0,
        "width": 300,
        "height": 100
    }
    end_shape = {
        "key": str(len(instruction_advanced_json) + 1),
        "customData": {"name": "End"},
        "locked": False,
        "zIndex": 0,
        "type": "end",
        "text": "End",
        "x": 0,
        "y": y_step_size + (len(instruction_advanced_json)) * y_step_size,
        "width": 300,
        "height": 100
    }

    # Mapping of task types to their required attributes
    task_attributes = {
        "Manual": [],
        "Scan": [],
        "Tightening": ["count", "program"],
        "Rivet": ["count", "program"],
        "Smartlabel": ["durationgui", "targetnumber"],
        "Pick_to_Light": ["count"],
        "SmartTower": ["count"],
        "Info": ["durationgui"],
        "Checklist": ["checklist"]
    }
    
    # Add start shape
    new_flowchart["shapes"].append(start_shape)
    
    # Create shapes for instructions
    y_position = y_step_size
    for idx, instruction in enumerate(instruction_advanced_json):
        task_type = instruction.get("task", "Manual")
        attributes = task_attributes.get(task_type, [])
        
        # Populate only the required attributes in customData
        custom_data = {
            "name": instruction.get("name", None),
            "task": task_type,
            "description": f"<p style=\"text-align: center;\">{instruction.get('description', None)}</p>",
            "imagefilename": instruction.get("image_uri", None)
        }
        for attr in attributes:
            if attr in instruction:  # Add only if the attribute exists in the instruction
                custom_data[attr] = instruction.get(attr, None)
        shape = {
            "key": str(idx + 1),
            "dataKey": None,
            "customData": custom_data,
            "locked": False,
            "zIndex": 0,
            "type": get_type_id(instruction.get("task", "Manual")),
            "text": instruction.get("name", "Unnamed"),
            "imageUrl": get_type_image_url(instruction.get("task", "Manual")),
            "x": 500,
            "y": y_position,
            "width": 300,
            "height": 100
        }
        y_position += y_step_size
        new_flowchart["shapes"].append(shape)
    
    # Add end shape
    new_flowchart["shapes"].append(end_shape)
    
    # Create connectors
    number_of_shapes = len(new_flowchart["shapes"])
    for idx in range(len(new_flowchart["shapes"]) - 1):
        connector = {
            "key": str(number_of_shapes + idx + 1),
            "dataKey": str(idx + 1),
            "customData": {
                "sourceOutcome": "OK",
                "translationKey": "OK"
            },
            "locked": False,
            "zIndex": 0,
            "points": [
                {"x": 650, "y": new_flowchart["shapes"][idx]["y"] + 50},
                {"x": 650, "y": new_flowchart["shapes"][idx + 1]["y"] + 50}
            ],
            "texts": {
                "0.5": "OK"
            },
            "properties": {
                "endLineEnding": 3
            },
            "style": {
                "stroke": "#707070",
                "stroke-width": "1"
            },
            "context": {
                "actualRoutingMode": 0,
                "renderPoints": [
                    {
                        "x": 650,
                        "y": new_flowchart["shapes"][idx]["y"] + 50,
                        "pointIndex": 0,
                        "skipped": False
                    },
                    {
                        "x": 650,
                        "y": new_flowchart["shapes"][idx + 1]["y"] + 50,
                        "pointIndex": 1,
                        "skipped": False
                    }
                ]
            },
            "beginItemKey": new_flowchart["shapes"][idx]["key"],
            "beginConnectionPointIndex": 2,
            "endItemKey": new_flowchart["shapes"][idx + 1]["key"],
            "endConnectionPointIndex": 0
        }
        new_flowchart["connectors"].append(connector)
    
    # Save the new flowchart JSON to a file
    os.makedirs(os.path.dirname(elam_json_path), exist_ok=True)
    with open(elam_json_path, 'w') as file:
        json.dump(new_flowchart, file, indent=4)
    print(f"Saved ELAM flowchart JSON to {elam_json_path}")

def pdf_basic_json_2_instruction_basic_json(pdf_basic_json_path, instruction_basic_json_path):
    print(f"\n### Start converting PDF basic JSON to basic instruction JSON ###")
    # Load the PDF basic JSON
    with open(pdf_basic_json_path, 'r') as file:
        pdf_basic_json = json.load(file)
    print(f"Loaded PDF basic JSON from {pdf_basic_json_path}")

    # Initialize the output JSON
    output_json = {
        "instructions": []
    }


    for page in pdf_basic_json.get('pdf_document', []):
        for instruction in page.get('instructions', []):
            step = instruction.get("step")
            text = instruction.get("text")
            picture_array = instruction.get("pictures_array", [])
            
            # Add the instruction to the output
            output_json["instructions"].append({
                "step": step,
                "text": text,
                "image_uri": picture_array
            })

    # Save the output JSON to a file
    os.makedirs(os.path.dirname(instruction_basic_json_path), exist_ok=True)
    with open(instruction_basic_json_path, 'w') as file:
        json.dump(output_json, file, indent=4)
    print(f"Saved basic instruction JSON to {instruction_basic_json_path}")





