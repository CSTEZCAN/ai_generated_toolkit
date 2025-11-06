import os
import sys
from PIL import Image
# Import the new, recommended library
from pillow_heif import register_heif_opener

# Register the HEIF format handler once
# This allows Pillow's Image.open() to handle .heic files directly
register_heif_opener()

def convert_heic_to_jpg(input_dir, output_dir="jpg_output", quality=85):
    """
    Converts all HEIC/HEIF files in a directory to JPG format, 
    preserving EXIF metadata and setting a custom quality using 
    the integrated pillow-heif opener.
    
    Args:
        input_dir (str): The directory containing HEIC files.
        output_dir (str): The directory where JPG files will be saved.
        quality (int): JPEG quality setting (0 to 100).
    """
    
    # 1. Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    total_converted = 0
    
    # 2. Iterate through all files in the input directory
    for filename in os.listdir(input_dir):
        # Check if the file is a HEIC/HEIF file (case-insensitive)
        if filename.lower().endswith(('.heic', '.heif')):
            input_path = os.path.join(input_dir, filename)
            
            # Create the output filename (e.g., image.heic -> image.jpg)
            base_name = os.path.splitext(filename)[0]
            output_filename = base_name + ".jpg"
            output_path = os.path.join(output_dir, output_filename)

            try:
                # 3. Open the HEIC/HEIF file directly with Pillow
                # The register_heif_opener() call allows this to work
                img = Image.open(input_path)
                
                # 4. Extract EXIF data (if present)
                # Pillow automatically handles the metadata loading via pillow-heif
                exif_dict = img.info.get('exif')

                # 5. Save the image as JPG
                # The 'exif' argument preserves the metadata
                
                # Pillow requires the exif data to be passed as bytes.
                if exif_dict:
                    img.save(
                        output_path, 
                        format="jpeg", 
                        quality=quality, 
                        exif=exif_dict
                    )
                else:
                    img.save(
                        output_path, 
                        format="jpeg", 
                        quality=quality
                    )
                
                print(f"✅ Converted: {filename} -> {output_filename}")
                total_converted += 1

            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                # Print the full exception for debugging
                # import traceback
                # traceback.print_exc() 

    print(f"\n--- Conversion Complete ---")
    print(f"Successfully converted {total_converted} HEIC files to JPG.")
    print(f"Output files saved to: ./{output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python heic_to_jpg_converter.py <input_folder>")
        print("\nExample: python heic_to_jpg_converter.py ~/Desktop/iphone_photos")
        sys.exit(1)

    input_folder = sys.argv[1]
    
    if not os.path.isdir(input_folder):
        print(f"Error: Directory not found at path: {input_folder}")
        sys.exit(1)
        
    # The default output directory is 'jpg_output'
    convert_heic_to_jpg(input_folder, quality=85)