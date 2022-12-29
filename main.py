import math
import os
import glob

from utils.files.fileWriter import FileWriter
from utils.grabbers.mss import Grabber
from utils.fps import FPS

# computer vision (OpenCV)
import cv2

import multiprocessing
import numpy as np
from utils.nms import non_max_suppression_fast
from utils.cv2 import filter_rectangles

from utils.controls.mouse.win32 import MouseControls
from utils.win32 import WinHelper
import keyboard

import time
from utils.time import sleep

from screen_to_world import get_move_angle, get_move_angle_my

# config
# Push CAPS-LOOK for run bot
# https://snipp.ru/handbk/scan-codes
ACTIVATION_HOTKEY = 58  # 58 = CAPS-LOCK
EXIT_HOTKEY = 69  # Escape
MOVELEFT_HOTKEY = 79
MOVERIGHT_HOTKEY = 80
MOVEUP_HOTKEY = 72
MOVEDOWN_HOTKEY = 76
AUTO_DEACTIVATE_AFTER = 60  # seconds or None (default Aim Lab map time is 60 seconds)
SCREENSHOTS_FOLDER = r"./screenshots"
# always True
_shoot = True
# show rectangles for sphere online
_show_cv2 = False
_write_cv2 = False
_show_fps = False

# the bigger these values, the more accurate and fail-safe bot will behave
# minimum interval after move hover to target
# PAUSE BEFORE SHOT
_pause = 0.047
# minimum interval between shoots
_shoot_interval = 0.047 # seconds

# used by the script
# left, top, width, height
# in windows we have shadow for window 8 pixel for each side
# location +8 + 30 size -16 -38 - 8
# 22+8 (header +shadow)
game_window_rect = WinHelper.GetWindowRect("aimlab_tb", (8, 30, 16, 38))  # cut the borders
print(game_window_rect)
_ret = None

# shoot mode now or not
_aim = False
# start shoot mode time
_activation_time = 0

files = glob.glob(f'{SCREENSHOTS_FOLDER}/*')
for f in files:
    os.remove(f)


def grab_process(q):
    grabber = Grabber()

    while True:
        img = grabber.get_image(
            {"left": int(game_window_rect[0]), "top": int(game_window_rect[1]), "width": int(game_window_rect[2]),
             "height": int(game_window_rect[3])})

        if img is None:
            continue

        # FileWriter.write_img(img, rf"{SCREENSHOTS_FOLDER}\{time.time()}_1_grabbed.jpg")
        # throw screenshot to opencv
        q.put_nowait(img)
        q.join()


def cv2_process():
    global _aim, _shoot, _ret, _pause, _shoot_interval, _show_cv2, _write_cv2, _show_fps, game_window_rect, _activation_time

    fps = FPS()
    font = cv2.FONT_HERSHEY_SIMPLEX
    _last_shoot = None
    grabber = Grabber()

    mouse = MouseControls()

    mistake_movies = 0
    # angle of view
    fov = [106.26, 73.74, 113.66]  # horizontal, vertical, depth

    x360 = 8182 * 2  # x value to rotate on 360 degrees
    x1 = x360 / 360
    x_full_hor = x1 * fov[0]

    # 2420 = 53.13 grads
    # 360 grads = 16,400 # 16364

    # if we target ball, ball on center screnn, cut 6x6 square on center, if hue color we target right
    def check_dot(hue_point):

        dot_img = grabber.get_image({"left": game_window_rect[0] + (game_window_rect[2] // 2) - 3,
                                     "top":
                                         game_window_rect[1] + (game_window_rect[3] // 2) - 3,
                                     "width": 6,
                                     "height": 6})

        dot_img = cv2.cvtColor(dot_img, cv2.COLOR_BGR2HSV)
        # print(dot_img)
        avg_color_per_row = np.average(dot_img, axis=0)
        # print(avg_color_per_row)
        avg_color = np.average(avg_color_per_row, axis=0)
        print("AVG COLOR: ", avg_color, " hue: ", hue_point)
        print(hue_point - 10 < avg_color[0] < hue_point + 20)

        return (hue_point - 10 < avg_color[0] < hue_point + 20) and (avg_color[1] > 120) and (avg_color[2] > 100)

    while True:
        # if we have screenshots
        img = grabber.get_image(
            {"left": int(game_window_rect[0]), "top": int(game_window_rect[1]), "width": int(game_window_rect[2]),
             "height": int(game_window_rect[3])})
        if img is None:
            continue

        if True:
            # img = q.get_nowait()
            # q.task_done()

            img_time = time.time()

            # if _ret is not None:
            #     # return the mouse to base position and proceed again
            #     mouse.move_relative(int(_ret[0]), int(_ret[1]))
            #     _ret = None
            #     # sleep(_pause)
            #     continue

            # some processing code
            # OpenCV HSV Scale (H: 0-179, S: 0-255, V: 0-255)
            hue_point = 87
            sphere_color = ((hue_point, 100, 100), (hue_point + 20, 255, 255))  # HSV
            min_target_size = (40, 40)
            max_target_size = (150, 150)

            # convert bgr to hsv image
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # create mask from color to color
            mask = cv2.inRange(hsv, np.array(sphere_color[0], dtype=np.uint8),
                               np.array(sphere_color[1], dtype=np.uint8))

            if _write_cv2:
                FileWriter.write_img(mask, rf"{SCREENSHOTS_FOLDER}\{img_time}_2_mask.jpg")

            # https://robotclass.ru/tutorials/opencv-python-find-contours/
            # https://medium.com/analytics-vidhya/opencv-findcontours-detailed-guide-692ee19eeb18
            #
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            rectangles = []

            for cnt in contours:
                # wrap contour to rectangle
                x, y, w, h = cv2.boundingRect(cnt)
                if (w >= min_target_size[0] and h >= min_target_size[1]) \
                        and (w <= max_target_size[0] and h <= max_target_size[1]):
                    rectangles.append((int(x), int(y), int(w), int(h)))

            # if not rectangles go to next screenshot
            if not rectangles:
                continue
            # print(rectangles)
            if _show_cv2:
                for idx, rect in enumerate(rectangles):
                    # print(idx)
                    x, y, w, h = rect
                    cv2.rectangle(img, (x, y), (x + w, y + h), [255, 0, 0], 6)
                    img = cv2.putText(img, f"{(x + w, y + h)}", (x, y - 10), font,
                                      .5, (0, 255, 0), 1, cv2.LINE_AA)
            if _write_cv2:
                FileWriter.write_img(img, rf"{SCREENSHOTS_FOLDER}\{img_time}_3_img.jpg")

            # max targets count is 1, everything else is considered FP
            rectangles = rectangles
            targets_count = len(rectangles)

            # Apply NMS
            rectangles = np.array(non_max_suppression_fast(np.array(rectangles), overlapThresh=0.3))

            # Filter rectangles (join intersections)
            rectangles = filter_rectangles(rectangles.tolist())

            # detect closest target
            closest = 1000000
            aim_rect = None
            for rect in rectangles:
                x, y, w, h = rect
                mid_x = int((x + (x + w)) / 2)
                mid_y = int((y + (y + h)) / 2)
                dist = math.dist([960, 540], [mid_x, mid_y])

                if dist < closest:
                    closest = dist
                    aim_rect = rect

            rectangles = [aim_rect]
            for rect in rectangles:
                x, y, w, h = rect
                if _show_cv2:
                    # draw rectangle
                    cv2.rectangle(img, (x, y), (x + w, y + h), [0, 255, 0], 2)

                # shoot
                mid_x = int((x + (x + w)) / 2)
                mid_y = int((y + (y + h)) / 2)
                # -1 fill circle
                if _show_cv2:
                    cv2.circle(img, (mid_x, mid_y), 10, (0, 0, 255), -1)

                if _write_cv2:
                    FileWriter.write_img(img, rf"{SCREENSHOTS_FOLDER}\{img_time}_4_dot.jpg")
                if _aim:
                    if _last_shoot is None or time.perf_counter() > (_last_shoot + _shoot_interval):
                        if _show_cv2:
                            game_window_rect__center = (game_window_rect[2] // 2, game_window_rect[3] // 2)
                            # print(game_window_rect__center)
                            cv2.circle(img, game_window_rect__center, 10, (0, 255, 255), -1)
                        if _write_cv2:
                            FileWriter.write_img(img, rf"{SCREENSHOTS_FOLDER}\{img_time}_5_center.jpg")

                        # rel_diff = get_move_angle((mid_x, mid_y), game_window_rect, x1, fov)
                        rel_diff = get_move_angle_my((mid_x, mid_y), game_window_rect, x1, fov)

                        # move the mouse
                        mouse.move_relative(int(rel_diff[0]), int(rel_diff[1]))

                        sleep(_pause)
                        img = grabber.get_image(
                            {"left": int(game_window_rect[0]), "top": int(game_window_rect[1]),
                             "width": int(game_window_rect[2]),
                             "height": int(game_window_rect[3])})
                        if _show_cv2:
                            game_window_rect__center = (game_window_rect[2] // 2, game_window_rect[3] // 2)
                            # print(game_window_rect__center)
                            cv2.circle(img, game_window_rect__center, 5, (255, 255, 0), -1)
                        if _write_cv2:
                            FileWriter.write_img(img, rf"{SCREENSHOTS_FOLDER}\{img_time}_6_moved.jpg")

                        print("moved")
                        if _shoot:
                            # detect if aiming the target (more accurate)

                            if _write_cv2:
                                dot_img = grabber.get_image(
                                    {"left": game_window_rect[0] + (game_window_rect[2] // 2) - 3,
                                     "top":
                                         game_window_rect[1] + (game_window_rect[3] // 2) - 3,
                                     "width": 6,
                                     "height": 6})
                                FileWriter.write_img(dot_img, rf"{SCREENSHOTS_FOLDER}\{img_time}_61_square.jpg")
                                dot_img = grabber.get_image(
                                    {"left": game_window_rect[0] + (game_window_rect[2] // 2) - 10,
                                     "top":
                                         game_window_rect[1] + (game_window_rect[3] // 2) - 10,
                                     "width": 20,
                                     "height": 20})
                                FileWriter.write_img(dot_img, rf"{SCREENSHOTS_FOLDER}\{img_time}_62_full.jpg")
                            if check_dot(hue_point):
                                # click
                                mouse.hold_mouse()
                                sleep(0.001)
                                mouse.release_mouse()
                                sleep(0.001)

                                img = grabber.get_image(
                                    {"left": int(game_window_rect[0]), "top": int(game_window_rect[1]),
                                     "width": int(game_window_rect[2]),
                                     "height": int(game_window_rect[3])})
                                if _show_cv2:
                                    game_window_rect__center = (game_window_rect[2] // 2, game_window_rect[3] // 2)
                                    # print(game_window_rect__center)
                                    cv2.circle(img, game_window_rect__center, 5, (255, 255, 0), -1)
                                if _write_cv2:
                                    FileWriter.write_img(img, rf"{SCREENSHOTS_FOLDER}\{img_time}_7_shoot.jpg")
                                print("shoot")
                                _last_shoot = time.perf_counter()
                                break
                            else:
                                img = grabber.get_image(
                                    {"left": int(game_window_rect[0]), "top": int(game_window_rect[1]),
                                     "width": int(game_window_rect[2]),
                                     "height": int(game_window_rect[3])})
                                if _show_cv2:
                                    game_window_rect__center = (game_window_rect[2] // 2, game_window_rect[3] // 2)
                                    # print(game_window_rect__center)
                                    cv2.circle(img, game_window_rect__center, 5, (255, 255, 0), -1)
                                if _write_cv2:
                                    FileWriter.write_img(img, rf"{SCREENSHOTS_FOLDER}\{img_time}_8_mistake.jpg")
                                print("mistake")
                                mistake_movies = mistake_movies + 1
                        else:
                            # Aim only once if shoot is disabled
                            _aim = False

                    # Auto deactivate aiming and/or shooting after N seconds
                    if AUTO_DEACTIVATE_AFTER is not None:
                        if _activation_time + AUTO_DEACTIVATE_AFTER < time.perf_counter():
                            _aim = False

            # cv stuff
            # img = mask

            # if _show_cv2:
            #     img = cv2.putText(img, f"{fps():.2f} | targets = {targets_count}", (20, 120), font,
            #                       1.7, (0, 255, 0), 7, cv2.LINE_AA)
            #     img = cv2.resize(img, (1280, 720))
            #     # cv2.imshow("test", cv2.cvtColor(img, cv2.COLOR_RGB2BGRA))
            #     # mask = cv2.resize(mask, (1280, 720))
            #     cv2.imshow("test", img)
            #     # show img 1 ms
            #     cv2.waitKey(1)
            if _show_fps:
                print(f"FPS: {fps():.2f} | mistakes movies: {mistake_movies}")


def move_left():
    mouse = MouseControls()
    print("rotate left")
    rel_diff = [0, 0]
    # angle of view
    fov = [106.26, 73.74]  # horizontal, vertical

    x360 = 5000  # x value to rotate on 360 degrees (see in aimlab controls settings)
    x1 = x360 / 360
    x_full_hor = x1 * fov[0]
    rel_diff[0] = -int(x360 / 2)
    # mouse.move_relative(-int(51.955*26.2534888*2*3), int(rel_diff[1]))
    mouse.move_relative(-int(8182), int(rel_diff[1]))
    # mouse.move(int(rel_diff[0]), int(rel_diff[1]))


def move_right():
    mouse = MouseControls()
    print("rotate right")
    rel_diff = [0, 0]
    # angle of view
    fov = [106.26, 73.74]  # horizontal, vertical

    x360 = 5000  # x value to rotate on 360 degrees (see in aimlab controls settings)
    x1 = x360 / 360
    x_full_hor = x1 * fov[0]
    rel_diff[0] = -int(x360 / 2)
    # mouse.move_relative(int(51.955*26.2534888*2*3), int(rel_diff[1]))
    mouse.move_relative(int(8182), int(rel_diff[1]))


def move_up():
    mouse = MouseControls()
    print("rotate")
    rel_diff = [0, 0]
    # angle of view
    fov = [106.26, 73.74]  # horizontal, vertical

    x360 = 5000  # x value to rotate on 360 degrees (see in aimlab controls settings)
    x1 = x360 / 360
    x_full_hor = x1 * fov[0]
    # rel_diff[0] = -int(x360/2)
    # mouse.move_relative(int(51.955*26.2534888*2*3), int(rel_diff[1]))
    mouse.move_relative(int(rel_diff[0]), -int((8182*2/360)*fov[1]/2))


def move_down():
    mouse = MouseControls()
    print("rotate")
    rel_diff = [0, 0]
    # angle of view
    fov = [106.26, 73.74]  # horizontal, vertical

    x360 = 5000  # x value to rotate on 360 degrees (see in aimlab controls settings)
    x1 = x360 / 360
    x_full_hor = x1 * fov[0]
    # rel_diff[0] = -int(x360/2)
    # mouse.move_relative(int(51.955*26.2534888*2*3), int(rel_diff[1]))
    mouse.move_relative(int(rel_diff[0]),  int((8182*2/360)*fov[1]/2))


def switch_shoot_state(triggered, hotkey):
    print("switch")
    global _aim, _ret, _activation_time
    _aim = not _aim  # inverse value

    if not _aim:
        _ret = None
    else:
        # run timer
        _activation_time = time.perf_counter()


def exit_app(processes):
    # print(processes)
    # for p in processes:
    #     p.kill()
    exit(0)


# on push ACTIVATION_HOTKEY RUN switch_shoot_state(...args)
keyboard.add_hotkey(ACTIVATION_HOTKEY, switch_shoot_state, args=('triggered', 'hotkey'))

if __name__ == "__main__":
    # q = multiprocessing.JoinableQueue()
    #
    # p1 = multiprocessing.Process(target=grab_process, args=(q,))
    # p2 = multiprocessing.Process(target=cv2_process, args=(q,))

    # p1.start()
    # p2.start()
    cv2_process()
    keyboard.add_hotkey(MOVELEFT_HOTKEY, move_left)
    keyboard.add_hotkey(MOVERIGHT_HOTKEY, move_right)
    keyboard.add_hotkey(MOVEUP_HOTKEY, move_up)
    keyboard.add_hotkey(MOVEDOWN_HOTKEY, move_down)
    keyboard.add_hotkey(EXIT_HOTKEY, exit_app, args=[])
