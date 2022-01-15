from PIL import Image
from io import BytesIO
import numpy as np
import cv2
import time

from browser_handler import BrowserHandler


def concat_vertically(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def FindMatches(BaseImage, SecImage):
    Sift = cv2.SIFT_create()
    BaseImage_kp, BaseImage_des = Sift.detectAndCompute(cv2.cvtColor(BaseImage, cv2.COLOR_BGR2GRAY), None)
    SecImage_kp, SecImage_des = Sift.detectAndCompute(cv2.cvtColor(SecImage, cv2.COLOR_BGR2GRAY), None)
    BF_Matcher = cv2.BFMatcher()
    InitialMatches = BF_Matcher.knnMatch(BaseImage_des, SecImage_des, k=2)
    GoodMatches = []
    for m, n in InitialMatches:
        if m.distance < 0.75 * n.distance:
            GoodMatches.append([m])

    return GoodMatches, BaseImage_kp, SecImage_kp


def FindHomography(Matches, BaseImage_kp, SecImage_kp):
    BaseImage_pts = []
    SecImage_pts = []
    for Match in Matches:
        BaseImage_pts.append(BaseImage_kp[Match[0].queryIdx].pt)
        SecImage_pts.append(SecImage_kp[Match[0].trainIdx].pt)
    BaseImage_pts = np.float32(BaseImage_pts)
    SecImage_pts = np.float32(SecImage_pts)
    (HomographyMatrix, Status) = cv2.findHomography(SecImage_pts, BaseImage_pts, cv2.RANSAC, 4.0)

    return HomographyMatrix, Status


def GetNewFrameSizeAndMatrix(HomographyMatrix, Sec_ImageShape, Base_ImageShape):
    (Height, Width) = Sec_ImageShape

    InitialMatrix = np.array([[0, Width - 1, Width - 1, 0],
                              [0, 0, Height - 1, Height - 1],
                              [1, 1, 1, 1]])

    FinalMatrix = np.dot(HomographyMatrix, InitialMatrix)

    [x, y, c] = FinalMatrix
    x = np.divide(x, c)
    y = np.divide(y, c)

    min_x, max_x = int(round(min(x))), int(round(max(x)))
    min_y, max_y = int(round(min(y))), int(round(max(y)))

    New_Width = max_x
    New_Height = max_y
    Correction = [0, 0]
    if min_x < 0:
        New_Width -= min_x
        Correction[0] = abs(min_x)
    if min_y < 0:
        New_Height -= min_y
        Correction[1] = abs(min_y)

    if New_Width < Base_ImageShape[1] + Correction[0]:
        New_Width = Base_ImageShape[1] + Correction[0]
    if New_Height < Base_ImageShape[0] + Correction[1]:
        New_Height = Base_ImageShape[0] + Correction[1]

    x = np.add(x, Correction[0])
    y = np.add(y, Correction[1])
    OldInitialPoints = np.float32([[0, 0],
                                   [Width - 1, 0],
                                   [Width - 1, Height - 1],
                                   [0, Height - 1]])
    NewFinalPonts = np.float32(np.array([x, y]).transpose())

    HomographyMatrix = cv2.getPerspectiveTransform(OldInitialPoints, NewFinalPonts)

    return [New_Height, New_Width], Correction, HomographyMatrix


def StitchImages(BaseImage, SecImage):
    Matches, BaseImage_kp, SecImage_kp = FindMatches(BaseImage, SecImage)
    HomographyMatrix, Status = FindHomography(Matches, BaseImage_kp, SecImage_kp)
    NewFrameSize, Correction, HomographyMatrix = GetNewFrameSizeAndMatrix(HomographyMatrix, SecImage.shape[:2],
                                                                          BaseImage.shape[:2])
    StitchedImage = cv2.warpPerspective(SecImage, HomographyMatrix, (NewFrameSize[1], NewFrameSize[0]))
    StitchedImage[Correction[1]:Correction[1] + BaseImage.shape[0],
    Correction[0]:Correction[0] + BaseImage.shape[1]] = BaseImage

    return StitchedImage


def save_screenshot(driver, file_name):
    total_height, viewport_height, viewport_width, imgs, y = scroll_down(driver)
    img1 = Image.open(BytesIO(imgs[0]))
    StitchedImage = None
    for i in range(1, len(imgs)):
        if i < len(imgs) - 1:
            img1 = concat_vertically(img1, Image.open(BytesIO(imgs[i])))
        else:
            cv_image = np.array(img1.convert("RGB"))
            Image1 = cv_image[:, :, ::-1].copy()
            cv_image_2 = np.array(Image.open(BytesIO(imgs[i])).convert("RGB"))
            Image2 = cv_image_2[:, :, ::-1].copy()

            # Calling function for stitching images.
            StitchedImage = StitchImages(Image1, Image2)

    if StitchedImage is not None:
        cv2.imwrite(file_name, StitchedImage)
    else:
        img1.save(file_name)


def scroll_down(driver):
    # start on top
    driver.execute_script("window.scrollTo(0, 0)")
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    viewport_width = driver.execute_script("return document.body.clientWidth")

    imgs = []
    y = total_height
    while True:
        if y > viewport_height:
            imgs.append(driver.get_screenshot_as_png())
            y = y - viewport_height
            driver.execute_script("window.scrollBy(0, window.innerHeight)")
            time.sleep(0.5)
        else:
            imgs.append(driver.get_screenshot_as_png())
            break
    return (total_height, viewport_height, viewport_width, imgs, y)

def get_full_page_screenshot() -> None:
    link = "https://markellisreviews.medium.com/"

    browser_handler = BrowserHandler(True)
    browser_handler.set_driver()
    browser_handler.get_url(link)
    time.sleep(1)

    save_screenshot(browser_handler.get_driver, "full_page.png")

    browser_handler.quit_driver()

if __name__ == '__main__':
    get_full_page_screenshot()