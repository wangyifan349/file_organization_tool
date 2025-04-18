import os
import shutil
import face_recognition
# ----------------- Find Similar Images -----------------
def find_similar_images(reference_image_path, directory_path, threshold=0.6):
    # Load and encode the reference image
    try:
        reference_image = face_recognition.load_image_file(reference_image_path)
    except Exception as e:
        print(f"Error loading the reference image: {e}")
        return []
    # Extract facial encodings from the reference image
    reference_encodings = face_recognition.face_encodings(reference_image)
    # Check if any faces were detected in the reference image
    if not reference_encodings:
        print("No face detected in the reference image.")
        return []
    # List to store paths of similar images
    similar_images = []
    # Traverse the target directory for images
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            # Process only image files
            if not file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                continue
            image_path = os.path.join(root, file)
            # Attempt to load each image file
            try:
                current_image = face_recognition.load_image_file(image_path)
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                continue
            # Extract facial encodings from the current image
            current_encodings = face_recognition.face_encodings(current_image)
            # Skip if no faces are detected in the current image
            if not current_encodings:
                print(f"No face detected in image: {image_path}, skipping.")
                continue
            # Compare each face encoding in the current image to the reference encodings
            for current_encoding in current_encodings:
                for reference_encoding in reference_encodings:
                    # Calculate the Euclidean distance
                    distance = face_recognition.face_distance([reference_encoding], current_encoding)[0]
                    # Record the image if similarity is within the threshold
                    if distance < threshold:
                        similar_images.append(image_path)
                        break
    # Sort images alphabetically for consistency
    similar_images.sort()
    # Output results
    for image_path in similar_images:
        print(f"Similar Image found: {image_path}")
    return similar_images
# ----------------- Move or Copy Images -----------------
def move_or_copy_images_to_directory(image_paths, output_directory, operation='copy'):
    # Create the directory if it does not exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # Move or copy each image to the new directory
    for image_path in image_paths:
        try:
            if operation == 'move':
                shutil.move(image_path, output_directory)
                print(f"Moved {image_path} to {output_directory}")
            elif operation == 'copy':
                shutil.copy(image_path, output_directory)
                print(f"Copied {image_path} to {output_directory}")
        except Exception as e:
            print(f"Error moving/copying {image_path}: {e}")
# ----------------- Example Usage -----------------
reference_image_path = 'path_to_reference_image.jpg'
directory_path = 'path_to_image_directory'
similar_images = find_similar_images(reference_image_path, directory_path)
# Prompt the user to enter a directory to move or copy similar images
if similar_images:
    action = input("Would you like to copy or move these images? (copy/move): ").strip().lower()
    output_directory = input("Please enter the path to the output directory: ").strip()
    move_or_copy_images_to_directory(similar_images, output_directory, operation=action)
