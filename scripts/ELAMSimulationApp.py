import json
import sys
import streamlit as st
import argparse
import atexit

# Set the Streamlit page configuration to wide mode
st.set_page_config(layout="wide")  # This will make the layout use the entire screen width

# Function to display an instruction in ELAM simulation
def show_instruction(instruction):
    print(f"\n Showing instruction: {instruction}")
    col1, col2 = st.columns([2, 1])  # Adjust column widths to give 2/3 and 1/3 of the window

    with col1:
        if instruction.get("name") == "Start" or instruction.get("name") == "End":
            st.markdown(f"**{instruction.get('name')}**")
        else:
            image_url = instruction.get("imagefilename")
            print(f"Image URL: {image_url}")
            try:
                if image_url:  # Check if the image is not None or empty
                    # Check if the image URL is a list, if so, loop through the list and display each image
                    if isinstance(image_url, list):
                        for url in image_url:
                            st.image(url, use_container_width=True)
                    else:
                        st.image(image_url, use_container_width=True)  # Image takes 2/3 of the window width
                else:
                    st.markdown("**No image available for this step.**")
            except Exception as e:
                st.markdown("**No image available for this step.**")
                # st.error(f"Error loading image: {e}")
                print(f"Error loading image: {e}")

    with col2:
        if instruction.get("name") != "Start" and instruction.get("name") != "End":
            st.markdown(f"**Instruction Type:** {instruction.get('task', 'N/A')}")
            st.markdown(f"**Title:** {instruction.get('name', 'N/A')}")
            description = instruction.get('description', 'N/A')
            # Remove leading <p style=\"text-align: center;\">
            description = description.replace("<p style=\"text-align: center;\">", "")
            # Remove trailing </p>
            description = description.replace("</p>", "")
            st.markdown(f"**Description:** {description}")
            st.markdown(f"**Quantity:** {instruction.get('count', 'N/A')}")

# Function to start the ELAM Simulation
def main(flowchart_path):

    if flowchart_path is None:
        st.error("Please provide a path to the flowchart JSON file.")
        return

    # Load the flowchart and run the simulation
    with open(flowchart_path) as f:
        flowchart_data = json.load(f)
    print(f"Loaded flowchart data from {flowchart_path}")

    instructions = [
        shape["customData"] for shape in flowchart_data.get("shapes", [])
        if "customData" in shape and "name" in shape["customData"]
    ]
    if not instructions:
        st.error("No instructions found.")
        return

    if "current_instruction" not in st.session_state:
        st.session_state.current_instruction = 0

    # Create columns for the buttons and place them at the top of the page
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Previous Instruction"):
            if st.session_state.current_instruction > 0:
                st.session_state.current_instruction -= 1

    with col2:
        if st.button("Next Instruction"):
            if st.session_state.current_instruction < len(instructions) - 1:
                st.session_state.current_instruction += 1

    # Create an empty container for the content (filling screen)
    content = st.empty()

    # Display instruction content
    with content.container():
        show_instruction(instructions[st.session_state.current_instruction])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ELAM Simulation App")
    parser.add_argument("flowchart_path", type=str, help="Path to the flowchart JSON file")
    args = parser.parse_args()
    main(args.flowchart_path)
