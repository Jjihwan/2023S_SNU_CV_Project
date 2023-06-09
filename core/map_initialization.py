import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
from numpy.linalg import svd, pinv, norm


class Map:
    def __init__(self, X_3D_0):
        self.X_3D_0 = X_3D_0
        self.normal_vector = np.zeros((4, 1))
        self.X_2D_ref = np.zeros((2, 1))
        self.X_3D_ref = np.zeros((8, 3))


def load_images(path1="./data/desk1.png", path2="./data/desk2.png"):
    """_summary_

    Args:
        path1 (str, optional): path for first image. Defaults to "./data/img1.png".
        path2 (str, optional): path for second image. Defaults to "./data/img2.png".

    Returns:
        array: images
    """
    print("map_initialization.py : Load images in", path1, "and", path2, "...")
    img1 = cv.imread(path1)
    img1 = cv.cvtColor(img1, cv.COLOR_BGR2RGB)
    img2 = cv.imread(path2)
    img2 = cv.cvtColor(img2, cv.COLOR_BGR2RGB)

    return img1, img2


def get_matching(img1, img2, NNDR_RATIO=0.7, C=None, recons=False):
    """_summary_
    Get matching points in image 1 and 2 using ORB feature detection & Nearest Neighbor Distance Ratio method
    Args:
        img1 : first image
        img2 : second image

    Returns:
        X1 (np.ndarray): (# of mathced points) * 2, Matched points (x, y)s in first image
        X2 (np.ndarray): (# of mathced points) * 2, Matched points (x, y)s in second image
    """
    MAX_TRANSLATION_RATIO = 20
    print("map_initialization.py : Mathcing the ORB features using NNDR RATIO =",
          NNDR_RATIO, "...")
    print("map_initialization.py : Map reconstructing ...")

    X = img1.shape[1]

    # ORB Feature Detection
    detector = cv.ORB_create()
    kp1, des1 = detector.detectAndCompute(img1, None)
    kp2, des2 = detector.detectAndCompute(img2, None)

    # To implement Nearest Neighbor Distance Ratio method, we used KNN to find the 2 nearest matches
    matcher = cv.BFMatcher_create(cv.NORM_HAMMING)
    matches = matcher.knnMatch(des1, des2, 2)

    # Lists only for plots
    good_mathches = []
    good_kp1s = []
    good_kp2s = []

    for m in matches:
        if m[0].distance < NNDR_RATIO * m[1].distance:
            # Find on right window
            if recons:
                x1 = np.array(kp1[m[0].queryIdx].pt)
                x2 = np.array(kp2[m[0].trainIdx].pt)
                if norm(x1-x2) < 200:
                    good_mathches.append(m[0])
                    x1 = x1[None, :]
                    x2 = x2[None, :]

                    if len(good_mathches) == 1:
                        X1 = x1
                        X2 = x2
                    else:
                        X1 = np.concatenate((X1, x1), axis=0)
                        X2 = np.concatenate((X2, x2), axis=0)

                    good_kp1s.append(kp1[m[0].queryIdx])
                    good_kp2s.append(kp2[m[0].trainIdx])
            else:
                if kp1[m[0].queryIdx].pt[0] > kp2[m[0].trainIdx].pt[0]:
                    if abs(kp1[m[0].queryIdx].pt[1] - kp2[m[0].trainIdx].pt[1]) < X/MAX_TRANSLATION_RATIO:
                        good_mathches.append(m[0])

                        x1 = np.array(kp1[m[0].queryIdx].pt)
                        x2 = np.array(kp2[m[0].trainIdx].pt)

                        x1 = x1[None, :]
                        x2 = x2[None, :]

                        if len(good_mathches) == 1:
                            X1 = x1
                            X2 = x2
                        else:
                            X1 = np.concatenate((X1, x1), axis=0)
                            X2 = np.concatenate((X2, x2), axis=0)

                        good_kp1s.append(kp1[m[0].queryIdx])
                        good_kp2s.append(kp2[m[0].trainIdx])

    print("map_initialization.py : Total ", len(
        good_mathches), "points are matched!!!")

    # To see the keypoints & descriptors in images, uncomment the following code

    # res = cv.drawMatches(img1, kp1, img2, kp2, good_mathches, None, flags=2)

    # img1_ = cv.drawKeypoints(img1, good_kp1s, None, color=(0, 0, 255), flags=0)
    # img2_ = cv.drawKeypoints(img2, good_kp2s, None, color=(0, 0, 255), flags=0)

    # img1_ = cv.cvtColor(img1_, cv.COLOR_BGR2RGB)
    # img2_ = cv.cvtColor(img2_, cv.COLOR_BGR2RGB)

    # plt.imshow(res)
    # plt.axis("off")
    # plt.show()
    # plt.figure(figsize=(14, 8))
    # plt.subplot(1, 2, 1)
    # plt.axis("off")
    # plt.imshow(img1_)
    # plt.subplot(1, 2, 2)
    # plt.axis("off")
    # plt.imshow(img2_)
    # plt.show()

    return X1, X2


def get3Dfrom2D(X1, X2, K, C=None, recons=False):
    """_summary_
    Find 3D coordinates on first image from matching points
    B = (# of mathced points)
    Args:
        X1 (np.ndarray): B * 2, Matched points (x, y)s in first image
        X2 (np.ndarray): B * 2, Matched points (x, y)s in second image
    Returns:
        X3D (np.ndarray): B * 3, 3D coordinates relative to second camera
    """
    print("map_initialization.py : Calculating an initial map...")

    c = np.array([K[0][2], K[1][2]])
    f = np.array([K[0][0], K[1][1]])
    X1_norImg = (X1-c)/f
    X2_norImg = (X2-c)/f

    B = X1.shape[0]
    if recons:
        P = C.motion
    else:
        R = np.eye(3)
        t = np.array([[-10], [0], [0]])
        P = np.concatenate((R, t), axis=1)

    A = np.zeros((B, 4, 4))

    # fill first 2 rows
    A[:, 0, 0] = 1
    A[:, 1, 1] = 1
    A[:, :2, 2] = -X1_norImg

    # fill last 2 rows
    p2 = np.tile(P[2], (B, 2, 1))
    p = np.tile(P[:2], (B, 1, 1))
    A[:, 2:, :] = p2*X2_norImg[:, :, None]-p

    U, S, VT = svd(A)

    X3D = VT[:, 3, :3] / VT[:, 3, 3, None]
    print("map_initialization.py : All done!!! Map size =", X3D.shape)

    # To verify the X3D, reconstruct 2D coordinates from 3D coordinates(Works quite well)
    # To see the results, uncomment the following code

    # recons = X3D[:, :2]/X3D[:, [2]]*f+c
    # idx = recons[:, 0].argsort()
    # recons1 = recons[idx, :]
    # X1_1 = X1[X1[:, 0].argsort(), :]
    # print(np.concatenate((recons1, X1_1), axis=1))

    # Drawing XYZ plot of X3D
    # To see the results, uncomment the following code

    # fig = plt.figure(figsize=(10, 10))
    # ax = fig.add_subplot(111, projection="3d")
    # ax.set_title("XYZ coordinates relative to first camera")
    # ax.set_xlabel("x")
    # # ax.set_xlim(0, 50)
    # ax.set_ylabel("y")
    # # ax.set_ylim(0, 40)
    # ax.set_zlabel("z")
    # # ax.set_zlim(0, 0.02)
    # ax.scatter(X3D[:, 0], X3D[:, 1], X3D[:, 2], marker='o', s=15)
    # plt.show()

    return X3D


def map_init_from_path(path1, path2, NNDR_RATIO, K):
    img1, img2 = load_images(path1, path2)
    X1, X2 = get_matching(img1, img2, NNDR_RATIO)

    X3D = get3Dfrom2D(X1, X2, K)

    return img1, X1, X2, X3D


def map_init_from_frames(F1, F2, NNDR_RATIO, K):
    X1, X2 = get_matching(F1, F2, NNDR_RATIO)

    X3D = get3Dfrom2D(X1, X2, K)

    M = Map(X3D)

    return M


def map_reconstruction_from_frames(F1, F2, NNDR_RATIO, C, FP):
    X1, X2 = get_matching(F1, F2, NNDR_RATIO, C, True)

    X_3D_i = get3Dfrom2D(X1, X2, C.K, C, True)

    X_3D_i_h = np.concatenate((X_3D_i, np.ones((X_3D_i.shape[0], 1))), 1)

    X_3D_i_to_0_h = X_3D_i_h @ C.motion.T @ pinv(C.pose).T
    X_3D_i_to_0 = X_3D_i_to_0_h[:, :3] / X_3D_i_to_0_h[:, [3]]

    FP.X_3D_0 = np.concatenate(
        (FP.X_3D_0, X_3D_i_to_0), 0)

    return FP
