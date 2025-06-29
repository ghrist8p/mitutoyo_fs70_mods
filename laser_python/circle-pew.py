# Ai-generated and reps-tweaked, double-check and use with caution!

import requests
import math
import time
from balor.sender import Sender



pew_time_in_tens_of_µs = 50

sender = Sender()
sender.open()
sender.raw_fiber_open_mo(1,0)

job = sender.job()
#job.raw_fiber_ylpmp_pulse_width(14)
job.set_power(10)
job.raw_q_switch_period(10)
job.raw_laser_on_point(pew_time_in_tens_of_µs)
job.raw_end_of_list()

BASE_URL = "http://192.168.1.70"
RADIUS = 100
NUM_POINTS = 360
CIRCLE_ITERATION_DELAY_SECONDS = 0.1


def move_axis_absolute(axis: str, position: int):
    """
    Sends an absolute move command to the specified axis of the stepper motor.
    This function will block until the HTTP GET request returns

    Args:
        axis (str): The axis to move ('x' or 'y').
        position (int): The absolute position in steps to move to.
    """
    if axis not in ['x', 'y']:
        print(f"Error: Invalid axis '{axis}'. Must be 'x' or 'y'.")
        return

    url = f"{BASE_URL}/{axis}_move?absolute={position}"
    try:
        response = requests.get(url, timeout=5) # Add a timeout for the request
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        print(f"Moved {axis} to {position}. Response: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"Error: Request to {url} timed out. Check connection or device.")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {BASE_URL}. Is the device on and IP correct?")
    except requests.exceptions.HTTPError as err:
        print(f"Error: HTTP error occurred: {err} from {url}")
    except Exception as e:
        print(f"An unexpected error occurred: {e} while trying to reach {url}")

# --- Main script execution ---
def drive_in_circle(radius: int, num_points: int):
    """
    Drives the stepper motor in a circle. Each axis movement waits for the
    HTTP response from the motor driver, assuming the response indicates
    completion of the movement.

    Args:
        radius (int): The radius of the circle in steps.
        num_points (int): The number of points to approximate the circle.
    """
    print(f"\n--- Starting circular motion with radius {radius} steps ---")
    print(f"Approximating circle with {num_points} points.")
    print(f"Ensure your motor driver is at {BASE_URL} and connected.")

    # Store the current position to manage movements
    current_x = 0
    current_y = 0

    try:
        # Move to the origin (0,0) first for a consistent start
        #print("Moving to origin (0,0) first...")
        #move_axis_absolute('x', 0)
        #move_axis_absolute('y', 0)
        # Give motor time to settle at origin before starting the circular path
        time.sleep(CIRCLE_ITERATION_DELAY_SECONDS)

        print(f"Moving to initial point ({radius}, 0) for the circle...")
        move_axis_absolute('x', radius)
        move_axis_absolute('y', 0)


        for i in range(num_points + 1): # +1 to include the very last point to close the circle
            angle = 2 * math.pi * i / num_points # Angle in radians

            # Calculate absolute x and y coordinates for the point on the circle
            # Using round() to ensure integer steps, as motors use discrete steps
            target_x = round(radius * math.cos(angle))
            target_y = round(radius * math.sin(angle))

            print(f"Moving to point {i+1}/{num_points}: (X={target_x}, Y={target_y})")

            # Move X-axis only if the target X is different from current X
            if target_x != current_x:
                move_axis_absolute('x', target_x)
                current_x = target_x

            # Move Y-axis only if the target Y is different from current Y
            if target_y != current_y:
                move_axis_absolute('y', target_y)
                current_y = target_y
            
            
            #pew pew
            time.sleep(0.1)
            job.execute(1)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nCircular motion interrupted by user. Attempting to return to origin...")
    #finally:
        # Always try to return to origin (0,0) at the end, regardless of interruption
        #print("\nReturning to origin (0,0)...")
        #move_axis_absolute('x', 0)
        #move_axis_absolute('y', 0)
        #print("Motion complete or interrupted. Stepper motor returned to origin.")


# --- Run the circle movement ---
if __name__ == "__main__":
    drive_in_circle(RADIUS, NUM_POINTS)
    sender.raw_fiber_open_mo(0,0)
    #sender.light_on()
    sender.close()

