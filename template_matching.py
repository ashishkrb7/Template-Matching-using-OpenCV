# import the necessary packages
import numpy as np
import cv2
import argparse
import json


def resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)

    # return the resized image
    return resized


def run(sourceimg, templateimg, outputfilename):
    # reading template image
    template = cv2.imread(templateimg, 0)

    # applying laplacian transformation to the template
    template = cv2.Laplacian(template, cv2.CV_64F)
    template = np.float32(template)
    # th and tw are the height and width of the template
    (tH, tW) = template.shape[:2]

    # reads image
    image = cv2.imread(sourceimg)

    # converts image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # applies gaussian blur with kernel size of 3 on the image
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    gray = cv2.Laplacian(blur, cv2.CV_64F)
    gray = np.float32(gray)
    found = None
    # loop over the scales of the image
    for scale in np.linspace(0.5, 2, 30):
        # resize the image according to the scale, and keep track of the ratio of the resizing

        resized = resize(gray, width=int(gray.shape[1] * scale))
        r = gray.shape[1] / float(resized.shape[1])

        # if the resized image is smaller than the template, then break from the loop
        if resized.shape[0] < tH or resized.shape[1] < tW:
            break

        # matching to find the template in the image
        # edged = cv2.Canny(resized, 50, 200)
        result = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF)
        (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)

        # if we have found a new maximum correlation value, then update found
        if found is None or maxVal > found[0]:
            found = (maxVal, maxLoc, r)
            (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
            (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))

    # unpack the bookkeeping varaible and compute the (x, y) coordinates of the bounding box based on the resized ratio
    if found is not None:
        # draw a bounding box around the detected result and display the image
        (maxVal, maxLoc, r) = found
        if maxVal > 350000:
            (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
            (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))
            cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
            cv2.imwrite(f"{outputfilename}.png", image)

            out = {"startX": startX, "startY": startY, "endX": endX, "endY": endY}
            print(out)
            with open(f"{outputfilename}.json", "w") as outfile:
                json.dump(out, outfile)
            return out
        else:
            print(sourceimg, "Cursor not detected")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Script for Template extraction")

    parser.add_argument(
        "-s",
        "--source",
        help="Source image",
        type=str,
        default="source.png",
        required=False,
    )

    parser.add_argument(
        "-t",
        "--template",
        help="Templace image (i.e. that you want to search) Note: Please make sure that the template image is smaller than the source image.",
        type=str,
        default="template.png",
        required=False,
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Name of output file",
        type=str,
        default="output",
        required=False,
    )

    args = parser.parse_args()

    run(sourceimg=args.source, templateimg=args.template, outputfilename=args.output)
