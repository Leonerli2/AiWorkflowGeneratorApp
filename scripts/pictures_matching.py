# pictures_matching.py
import cv2
import os
import numpy as np

def calculate_match_score(img1, img2):
    # Initialize SIFT detector
    sift = cv2.SIFT_create()

    # Detect features and compute descriptors
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # If descriptors are None, return 0 score
    if des1 is None or des2 is None:
        return 0.0

    # Match descriptors using k-NN matcher and Lowe's ratio test
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    # Apply Lowe's ratio test to filter good matches
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    # Check if enough matches are found
    MIN_MATCH_COUNT = 10
    if len(good_matches) > MIN_MATCH_COUNT:
        # Extract location of good matches
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches])
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches])

        # Find homography matrix using RANSAC
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        # Calculate the number of inliers
        inliers = np.sum(mask)
        score = inliers / len(good_matches)
    else:
        score = 0.0

    return score

def fill_match_score_matrix(folder1, folder2):
    # Get image file paths from both folders
    images1 = [os.path.join(folder1, f) for f in os.listdir(folder1)
               if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    images2 = [os.path.join(folder2, f) for f in os.listdir(folder2)
               if f.lower().endswith(('png', 'jpg', 'jpeg'))]

    # Initialize an empty matrix
    match_matrix = np.zeros((len(images1), len(images2)))

    # Iterate over all pairs of images
    for i, img1_path in enumerate(images1):
        img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
        for j, img2_path in enumerate(images2):
            img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
            match_matrix[i, j] = calculate_match_score(img1, img2)

    return match_matrix, images1, images2

# Example usage
folder1 = 'data/output_pictures'
folder2 = 'data/output_docling/pictures'

match_matrix, images1, images2 = fill_match_score_matrix(folder1, folder2)

# Display match matrix
print(match_matrix)
