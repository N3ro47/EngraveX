#!/bin/env python3
import serial
import time
import argparse

BAUD_RATE = 115200

command_map = {
    "help": None,  # Help command
    "exit": None,  # Exit command
    "init": ["G21", "G90", "M3 S0"],  # Init
    "goto_start": ["G0 X0 Y0"],  # Move to start position
    "pause": ["M0"],  # Pause operation
    "end": ["M2"],  # End and turn off
    "move": lambda args: [f"G1 X{args[0]} Y{args[1]}"],  # Move to specific X, Y coordinates
    "set_power": lambda args: [f"M3 S{args[0]}"],  # Set laser power
    "laser_off": ["M5"],  # Laser off
    "set_feed": lambda args: [f"F{args[0]}"],  # Set laser feed
    "dope_grid_pattern": lambda args: generate_grid_gcode(args),  # Generate grid pattern G-code
}

# Functions
def available_commands():
    print("Available commands and their usage:")
    print("- help            : Display this help message.")
    print("- exit            : Exit the application.")
    print("- init            : Initialize the laser with default settings (G21, G90, M3 S0).")
    print("- goto_start      : Move the laser to the start position (X=0, Y=0).")
    print("- pause           : Pause the operation (M0).")
    print("- end             : End the program and turn off the laser (M2).")
    print("- move <X> <Y>    : Move to specific X, Y coordinates (e.g., move 10 20 -> G1 X10 Y20).")
    print("- set_power P     : Set the laser power (e.g., set_power 500 -> M3 S500).")
    print("- laser_off       : Turn off the laser (M5).")
    print("- set_feed F      : Set the feed rate (e.g., set_feed 500 -> F500).")
    print("- dope_grid_pattern F  : Generate a grid pattern from a rectangle file (e.g., grid_pattern rects.txt).")


def init_parser():
    parser = argparse.ArgumentParser(description="CLI tool for controlling laser with gcode in Serial")
    parser.add_argument("-p", "--port", help="Port file for serial communication", required=False)
    return parser


def log_sent_data(file_path, message):
    with open(file_path, 'a') as file:
        file.write(message + "\n")


def send_gcode(ser, gcode):
    for command in gcode:
        try:
            ser.write(command.encode() + b'\n')
            log_sent_data("sent_data_log.txt", command)
            print(f"Sent: {command}")
            time.sleep(0.1)
        except serial.SerialException as e:
            print(f"Error sending command: {command}. Reason: {e}")


def handle_command(command, args):
    if command in command_map:
        if callable(command_map[command]):
            return command_map[command](args)
        else:
            return command_map[command]
    else:
        return None


def parse_rectangle_file(file_path):
    """
    Parses a rectangle-based file for doping patterns.
    Format:
    RECTANGLE X Y WIDTH HEIGHT SPACING
    """
    rectangles = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith("RECTANGLE"):
                    _, x, y, width, height, spacing = line.split()
                    rectangles.append((float(x), float(y), float(width), float(height), float(spacing)))
    except Exception as e:
        print(f"Error reading rectangle file: {e}")
    return rectangles


def generate_grid_gcode(args):
    if not args:
        print("Error: No file provided for grid pattern generation.")
        return []

    file_path = args[0]
    rectangles = parse_rectangle_file(file_path)

    gcode = []
    for rect in rectangles:
        x, y, width, height, spacing = rect

        current_y = y
        while current_y <= y + height:
            gcode.append("M5")
            gcode.append(f"G1 X{x} Y{current_y}")
            gcode.append("M3 S500")
            gcode.append(f"G1 X{x + width} Y{current_y}")
    
            gcode.append("M5")

            current_y += spacing

    return gcode


def main():
    parser = init_parser()
    args = parser.parse_args()

    ser = serial.Serial(args.port, baudrate=BAUD_RATE, timeout=0)

    print("EngraveX!")

    while True:
        command_input = input("[laser]: ").strip()
        parts = command_input.split()

        command = parts[0]
        command_args = list(parts[1:])

        gcode = handle_command(command, command_args)

        if gcode:
            send_gcode(ser, gcode)
        elif command == "exit":
            print("Exiting EngraveX.")
            break
        elif command == "help":
            available_commands()
        else:
            print(f"Unknown or invalid command: {command}")

    ser.close()


if __name__ == "__main__":
    main()
