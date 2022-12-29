import win32gui
import cv2

from utils.files.fileWriter import FileWriter
from utils.grabbers.mss import Grabber


class WinHelper:
    @staticmethod
    def GetWindowRect(window_title, subtract_window_border=(16, 39, 16, 0)) -> tuple:
        assert len(window_title)
        assert len(subtract_window_border) == 4

        # search window by it title
        window_handle = win32gui.FindWindow(None, window_title)
        # get window rectangle
        window_rect = list(win32gui.GetWindowRect(window_handle))
        print(window_rect)



        window_rect[2] -= window_rect[0]  # calc width
        window_rect[3] -= window_rect[1]  # calc height
        # print(window_rect)

        if subtract_window_border:
            window_rect[0] += subtract_window_border[0]  # left
            window_rect[1] += subtract_window_border[1]  # top
            window_rect[2] -= subtract_window_border[2]  # right
            window_rect[3] -= subtract_window_border[3]  # bottom
        print(window_rect)

        # grabber = Grabber()
        # img = grabber.get_image(
        #     {"left": int(window_rect[0]), "top": int(window_rect[1]), "width": int(window_rect[2]),
        #      "height": int(window_rect[3])})
        # # cv2.imwrite(r"filename.png", img)
        # img = cv2.resize(img, (1280, 720))
        # cv2.imshow("test", img)
        # cv2.waitKey(0)
        # FileWriter.write(window_rect)
        return tuple(window_rect)
