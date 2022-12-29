import cv2

from utils.grabbers.mss import Grabber


class FileWriter:
    @staticmethod
    def write(window_rect, filename=r"screenshot.png", show=False):
        grabber = Grabber()
        img = grabber.get_image(
            {"left": int(window_rect[0]), "top": int(window_rect[1]), "width": int(window_rect[2]),
             "height": int(window_rect[3])})
        cv2.imwrite(filename, img)
        if show:
            img = cv2.resize(img, (1280, 720))
            cv2.imshow("test", img)
            cv2.waitKey(0)

    @staticmethod
    def write_img(img, filename=r"screenshot.png", show=False):
        cv2.imwrite(filename, img)

        if show:
            img = cv2.resize(img, (1280, 720))
            cv2.imshow("test", img)
            cv2.waitKey(0)