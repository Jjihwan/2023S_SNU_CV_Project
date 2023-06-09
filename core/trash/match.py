import numpy as np
import cv2
import descriptor

img1 = cv2.imread('/Users/hojjunekim/Desktop/컴비기/term_Project/2023S_SNU_CV_Project/core/data/all1.jpeg')
img2 = cv2.imread('/Users/hojjunekim/Desktop/컴비기/term_Project/2023S_SNU_CV_Project/core/data/all2.jpeg')
gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

kp1, kp2, good_matches = descriptor.ORB(gray1, gray2)

match_img = cv2.drawMatches(img1, kp1, img2, kp2, good_matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
for match in good_matches:
    
    pt1 = kp1[match.queryIdx].pt
    pt2 = kp2[match.trainIdx].pt
    pt1 = (int(pt1[0]), int(pt1[1]))
    pt2 = (int(pt2[0]+np.shape(img1)[1]), int(pt2[1]))
    match_img = cv2.line(match_img, pt1, pt2, (0, 255, 0), thickness=3)
# Display image
cv2.imshow('Matches', match_img)
cv2.waitKey(0)
cv2.destroyAllWindows()