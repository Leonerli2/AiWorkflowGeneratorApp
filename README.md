# AI Workflow Generator

The AI Workflow Generator is a Streamlit-based application designed to automate the generation of workflow documentation from videos or PDFs. It provides tools to process videos and PDFs into flowcharts and JSON-based digital instructions, offering features such as AI-assisted wizardry, interactive simulations, and an easy-to-use interface for video and PDF uploads.

## Features

- **Video Mode**:  
  - Upload or search for videos in the `data/input/videos` directory.
  - Generate flowcharts and instructions using the AI-Wizard.
  - Display the generated flowchart or simulate the workflow interactively with ELAM Simulation.

- **PDF Mode**:  
  - Select PDFs from the `data/input/pdfs` directory.
  - Process PDFs into flowcharts and instructions with the AI-Wizard.
  - Display the flowchart or simulate the workflow interactively with ELAM Simulation.

- **Interactive Features**:  
  - QR code for seamless video upload from a phone on the same Wi-Fi network.
  - Step-by-step navigation of tasks and instructions in the ELAM simulation.

## Installation

### Prerequisites
1. **Python**: Ensure you have Python installed (recommended version: 3.9-3.12).  
2. **FFmpeg**: Install FFmpeg and add it to your system's PATH.
3. **OpenAI API Key**: Add your OpenAI API key as an environment variable (`OPENAI_API_KEY`).
4. Install project dependencies:

        pip install -r requirements.txt

Note: If you encounter issues installing docling, it may be due to an incompatible Python version.

## Usage
### Running the App

1. Clone the repository and navigate to the project directory.
2. Start the Streamlit app:

       streamlit run scripts/AiWorkflowGeneratorApp.py

3. Use the sidebar to select Video or PDF mode.

### Video Workflow

1. Video Upload:
    - Use the "Show QR Code for Video Upload" button to upload videos to `data/input/videos` remotely.
    - Alternatively, place videos directly in the folder with the naming scheme `video<number>.mp4`.

2. AI-Wizard:
    - Select a video, then click "Start AI-Wizard" to process the video into a flowchart and JSON instructions.

3. Flowchart:
    - Use the "Display Flowchart" button to view the generated workflow.

4. ELAM Simulation:
    - Start the interactive simulation by clicking "Start ELAM Sim".

### PDF Workflow

1. PDF Upload:
    - Place PDFs in the ``data/input/pdfs`` folder with the following naming scheme `w<number>.mp4` to select a PDF.

2. AI-Wizard:
    - Click "Start AI-Wizard" to process the PDF into a flowchart and JSON instructions.

3. Flowchart and ELAM Simulation:
    - Display the flowchart or simulate the workflow as in the video mode.

4. ELAM Simulation:
    - Start the interactive simulation by clicking "Start ELAM Sim".

## Folder Structure

    .
    ├── data/
    │   ├── input/
    │   │   ├── videos/       # Store input videos
    │   │   ├── pdfs/         # Store input PDFs
    │   ├── output/
    │       ├── video/        # Generated outputs for videos
    │       ├── pdf/          # Generated outputs for PDFs
    ├── scripts/
    │   ├── AiWorkflowGeneratorApp.py  # Main application
    │   ├── ELAMSimulationApp.py       # Interactive ELAM simulation
    │   ├── VideoUploadApp.py          # QR-based video upload
    │   ├── AiWizzard.py               # Core AI wizard processing
    ├── requirements.txt  # Dependencies

## Demo Videos


## Troubleshooting

- Ensure FFmpeg is properly installed and accessible in your PATH.
- Verify your Python version if dependencies fail to install.
- Check environment variables for OpenAI API key setup.

## Contributing

Contributions to the AI Workflow Generator are highly welcome! Whether it's through filing bugs, suggesting features, or contributing code, we appreciate your efforts to enhance this tool.

## License

This software is proprietary and confidential. It is available for use, reproduction, and distribution solely by authorized individuals and entities. Unauthorized copying of the files, via any medium, is strictly prohibited without prior written consent.

## Authors

- L.N
- S.G.

AI Workflow Generator was developed as part of the ETH Exploration Lab. Both L.N. and S.G. continue to improve and extend its functionalities, driving advancements in AI-based workflow automation.

## Acknowledgments

- Thanks to the ETH Exploration Lab for their support and resources.
- Special thanks to all contributors who have helped refine and enhance the AI Workflow Generator.
