import json
import base64
import subprocess

def extract_metadata_with_exiftool(image_path):
    result = subprocess.run(['exiftool', '-json', image_path], stdout=subprocess.PIPE, text=True)
    metadata = json.loads(result.stdout)
    if metadata:
        image_metadata = metadata[0]
        if 'Chara' in image_metadata:
            return image_metadata['Chara']
        else:
            print("Chara metadata not found.")
    else:
        print("Failed to extract metadata.")
    return None

def parse_character_card(character_card):
    # print(character_card)
    personality = character_card.get("data", "")
    personality = personality['description']
    # personality = character_card.get("description", "")
    instruction = f"Respond as a character with the following personality traits: {personality}."
    return instruction

def main():
    image_path = '../../Downloads/2b56ced8073a1b83c5fc1e638db8bbd3699152cf0c70c582ac10430d35a21180.png'
    chara_data_encoded = extract_metadata_with_exiftool(image_path)
    if chara_data_encoded:
        decoded_data = base64.b64decode(chara_data_encoded)
        character_card = json.loads(decoded_data.decode('utf-8'))
        instruction = parse_character_card(character_card)
        print(instruction)
        # Here, you would integrate with your AI model, passing the instruction along with the user input
    else:
        print("No character card data found.")

if __name__ == "__main__":
    main()
    