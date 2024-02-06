from PIL import Image
import json
import base64
import subprocess

def extract_metadata_with_exiftool(image_path):
    # Run exiftool, capturing output
    result = subprocess.run(['exiftool', '-json', image_path], stdout=subprocess.PIPE, text=True)
    # Parse JSON output from exiftool
    metadata = json.loads(result.stdout)
    
    # Assuming there's only one image and thus one metadata entry
    if metadata:
        image_metadata = metadata[0]
        if 'Chara' in image_metadata:
            chara_data = image_metadata['Chara']
            return chara_data
        else:
            print("Chara metadata not found.")
            return None
    else:
        print("Failed to extract metadata.")
        return None

# Example usage
image_path = '../../Downloads/2b56ced8073a1b83c5fc1e638db8bbd3699152cf0c70c582ac10430d35a21180.png'
chara_data = extract_metadata_with_exiftool(image_path)

print(chara_data)
if chara_data:
    # Process the chara data (assuming it's a JSON string)
    decoded_data = base64.b64decode(chara_data)
    decoded_string = decoded_data.decode('utf-8')
    chara_json = json.loads(decoded_string)
    print('full data: ', chara_json)

    print('part: ', chara_json['data']) # there might be no data then it is version1
    