import pyautogui
import time

def execute_command(cmd):
    parts = cmd.strip().split()
    if not parts:
        return

    action = parts[0].upper()

    if action == "CLICK":
        x, y = int(parts[1]), int(parts[2])
        pyautogui.moveTo(x, y)
        pyautogui.click()
    elif action == "TYPE":
        message = " ".join(parts[1:])
        pyautogui.write(message, interval=0.1)
    elif action == "WAIT":
        seconds = float(parts[1])
        time.sleep(seconds)

# Read and execute commands
with open("commands.txt", "r") as f:
    for line in f:
        execute_command(line)