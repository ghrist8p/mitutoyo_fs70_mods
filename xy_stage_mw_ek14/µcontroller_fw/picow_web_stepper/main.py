import network
import socket
import time
from machine import Pin

Y_EN_PIN = 26
Y_HOME_PIN = 9
Y_STEP_PIN = 19
Y_HOME_DIR = 0
Y_INVERT = 1
Y_HOME_OFFSET = -2400
Y_MIN = -2400
Y_MAX = 2900

X_EN_PIN = 16
X_HOME_PIN = 5
X_STEP_PIN = 28
X_HOME_DIR = 1
X_INVERT = 0
X_HOME_OFFSET = -3100
X_MIN = -3100
X_MAX = 5900

Z_EN_PIN = 22
Z_HOME_PIN = 10
Z_STEP_PIN = 18
Z_HOME_DIR = 0
Z_INVERT = 0
Z_HOME_OFFSET = 0
Z_MIN = -900000
Z_MAX = 900000

DIR_PIN = 27  # Common direction pin
DELAY_MS = 10 # Delay after changing direction
STEP_LENGTH_MS = 1 # Pulse width for a single step

dir_pin = Pin(DIR_PIN, Pin.OUT)

axes = {
    'x': {
        'en': Pin(X_EN_PIN, Pin.OUT),
        'home_sensor': Pin(X_HOME_PIN, Pin.IN, Pin.PULL_UP),
        'step_pin': Pin(X_STEP_PIN, Pin.OUT),
        'position': 0,
        'zero_offset': X_HOME_OFFSET,
        'home_dir': X_HOME_DIR,
        'invert': X_INVERT,
        'min': X_MIN,
        'max': X_MAX,
        'homing_active': 0
    },
    'y': {
        'en': Pin(Y_EN_PIN, Pin.OUT),
        'home_sensor': Pin(Y_HOME_PIN, Pin.IN, Pin.PULL_UP),
        'step_pin': Pin(Y_STEP_PIN, Pin.OUT),
        'position': 0,
        'zero_offset': Y_HOME_OFFSET,
        'home_dir': Y_HOME_DIR,
        'invert': Y_INVERT,
        'min': Y_MIN,
        'max': Y_MAX,
        'homing_active': 0
    },
    'z': {
        'en': Pin(Z_EN_PIN, Pin.OUT),
        'home_sensor': Pin(Z_HOME_PIN, Pin.IN, Pin.PULL_UP),
        'step_pin': Pin(Z_STEP_PIN, Pin.OUT),
        'position': 0,
        'zero_offset': Z_HOME_OFFSET,
        'home_dir': Z_HOME_DIR,
        'invert': Z_INVERT,
        'min': Z_MIN,
        'max': Z_MAX,
        'homing_active': 0
    }
}

# Initialize enable pins to low (enabled)
for axis in axes.values():
    axis['en'].value(0)


# --- Web Server Setup ---
SSID = 'YOUR_WIFI_SSID'
PASSWORD = 'YOUR_WIFI_PASSWORD'

def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(SSID, PASSWORD)
        max_wait = 10
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)
        if wlan.status() != 3:
            raise RuntimeError('network connection failed')
    print('connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])
    return status[0]

def do_step(axis_obj, direction):
    """Performs a single step."""
    if direction == 1 and axis_obj['position'] < axis_obj['max'] :
        axis_obj['position'] += direction
        axis_obj['step_pin'].value(1)
        time.sleep_ms(STEP_LENGTH_MS)
        axis_obj['step_pin'].value(0)
        time.sleep_ms(STEP_LENGTH_MS)
    elif direction == -1 and axis_obj['position'] > axis_obj['min']:
        axis_obj['position'] += direction
        axis_obj['step_pin'].value(1)
        time.sleep_ms(STEP_LENGTH_MS)
        axis_obj['step_pin'].value(0)
        time.sleep_ms(STEP_LENGTH_MS)
    elif axis_obj['homing_active']:
        axis_obj['step_pin'].value(1)
        time.sleep_ms(STEP_LENGTH_MS)
        axis_obj['step_pin'].value(0)
        time.sleep_ms(STEP_LENGTH_MS)




def move_stepper(axis_name, num_steps):
    """
    Moves the specified stepper motor by a given number of steps.
    num_steps: positive for forward, negative for backward.
    """
    if axis_name not in axes:
        print(f"Error: Axis '{axis_name}' not found.")
        return

    axis = axes[axis_name]
    direction = 1 if num_steps > 0 else -1
    abs_steps = abs(num_steps)

    print(f"Moving {axis_name} axis, {abs_steps} steps in direction: {'+' if direction == 1 else '-'}")

    # Set direction pin
    dirpinval = 1 if direction == -1 else 0
    dir_pin.value(dirpinval ^ axis['invert'])
    time.sleep_ms(DELAY_MS) # Delay after changing direction

    for _ in range(abs_steps):
        do_step(axis, direction)
        # Optional: Add a small delay here if steps are too fast
        # time.sleep_us(100) # Example: 100 microseconds delay between steps

    print(f"{axis_name} final position: {axis['position']}")

def home_axis(axis_name):
    """
    Homes the specified axis by moving towards the home sensor until triggered.
    """
    if axis_name not in axes:
        print(f"Error: Axis '{axis_name}' not found.")
        return

    axis = axes[axis_name]
    print(f"Homing {axis_name} axis...")

    axis['homing_active'] = 1

    # Set direction towards home (usually negative, so DIR_PIN high)
    dir_pin.value(axis['home_dir']) # Assuming negative direction (towards 0 or home) is DIR_PIN high
    time.sleep_ms(DELAY_MS) # Delay after changing direction

    # Move until home sensor is triggered (sensor input goes low)
    while axis['home_sensor'].value() != 0: # 0 means sensor is triggered (pulled low)
        do_step(axis, -1) # Move in the negative direction
        # Optional: Add a small delay between home steps if needed
        # time.sleep_ms(5)

    # snap to nearest full step
    axis['en'].value(1) # Disable driver to allow motor to settle
    time.sleep_ms(DELAY_MS)
    axis['en'].value(0) # Re-enable driver
    time.sleep_ms(DELAY_MS)

    axis['position'] = axis['zero_offset'] # Set current position to zero_offset
    axis['homing_active'] = 0
    print(f"{axis_name} homed. Final position: {axis['position']}")


def web_page():
    # Dynamically get current positions
    x_pos = axes['x']['position']
    y_pos = axes['y']['position']
    z_pos = axes['z']['position']

    html = f"""
    <html>
    <head>
        <title>Pico W Stepper Control</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 20px; }}
            .axis-container {{
                border: 1px solid #ccc;
                padding: 15px;
                margin: 15px auto;
                width: 90%;
                max-width: 400px;
                border-radius: 8px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            }}
            .axis-label {{ font-size: 20px; font-weight: bold; margin-bottom: 10px; }}
            .position-display {{
                font-size: 1.2em;
                margin-bottom: 15px;
                color: #333;
            }}
            .button-group {{ display: flex; justify-content: center; margin-bottom: 10px; }}
            .button {{
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
            }}
            .button.red {{ background-color: #f44336; }}
            .button.blue {{ background-color: #008CBA; }}
            input[type="number"] {{
                width: 80px;
                padding: 8px;
                margin: 0 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>Stepper Motor Control</h1>

        <div class="axis-container">
            <div class="axis-label">X Axis</div>
            <div class="position-display">Position: <span id="x_pos">{x_pos}</span></div>
            <div class="button-group">
                <form action="/x_move" method="get">
                    <input type="number" name="steps" value="100">
                    <button class="button" type="submit" name="dir" value="pos">Move +</button>
                    <button class="button red" type="submit" name="dir" value="neg">Move -</button>
                </form>
            </div>
            <div class="button-group">
                <a href="/x_home"><button class="button blue">Home X</button></a>
            </div>
            <div class="button-group">
                <a href="/x_pos_1"><button class="button">X Step +</button></a>
                <a href="/x_neg_1"><button class="button red">X Step -</button></a>
            </div>
        </div>

        <div class="axis-container">
            <div class="axis-label">Y Axis</div>
            <div class="position-display">Position: <span id="y_pos">{y_pos}</span></div>
            <div class="button-group">
                <form action="/y_move" method="get">
                    <input type="number" name="steps" value="100">
                    <button class="button" type="submit" name="dir" value="pos">Move +</button>
                    <button class="button red" type="submit" name="dir" value="neg">Move -</button>
                </form>
            </div>
            <div class="button-group">
                <a href="/y_home"><button class="button blue">Home Y</button></a>
            </div>
            <div class="button-group">
                <a href="/y_pos_1"><button class="button">Y Step +</button></a>
                <a href="/y_neg_1"><button class="button red">Y Step -</button></a>
            </div>
        </div>

        <div class="axis-container">
            <div class="axis-label">Z Axis</div>
            <div class="position-display">Position: <span id="z_pos">{z_pos}</span></div>
            <div class="button-group">
                <form action="/z_move" method="get">
                    <input type="number" name="steps" value="100">
                    <button class="button" type="submit" name="dir" value="pos">Move +</button>
                    <button class="button red" type="submit" name="dir" value="neg">Move -</button>
                </form>
            </div>
            <div class="button-group">
                <a href="/z_home"><button class="button blue">Home Z</button></a>
            </div>
            <div class="button-group">
                <a href="/z_pos_1"><button class="button">Z Step +</button></a>
                <a href="/z_neg_1"><button class="button red">Z Step -</button></a>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# --- Main Program ---
try:
    ip_address = connect_to_wifi()
except RuntimeError as e:
    print(e)
    # If connection fails, you might want to halt or retry
    while True:
        time.sleep(1) # Halt if connection fails

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

print(f"Web server listening on http://{ip_address}/")

while True:
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    request_line = request.decode('utf-8').split('\r\n')[0]
    print('Request: %s' % request_line)

    # Parse the request URL
    # Example requests:
    # GET /x_pos_1 HTTP/1.1 (for single step)
    # GET /x_move?steps=100&dir=pos HTTP/1.1 (for multiple steps)
    # GET /x_home HTTP/1.1 (for homing)

    parts = request_line.split(' ')
    if len(parts) > 1:
        path = parts[1]
        
        # Handle single step commands
        if path.startswith("/x_pos_"):
            move_stepper('x', 1)
        elif path.startswith("/x_neg_"):
            move_stepper('x', -1)
        elif path.startswith("/y_pos_"):
            move_stepper('y', 1)
        elif path.startswith("/y_neg_"):
            move_stepper('y', -1)
        elif path.startswith("/z_pos_"):
            move_stepper('z', 1)
        elif path.startswith("/z_neg_"):
            move_stepper('z', -1)
        
        # Handle multi-step commands via form submission
        elif path.startswith("/x_move"):
            if 'steps=' in path and 'dir=' in path:
                try:
                    query_params = path.split('?')[1]
                    params = dict(item.split('=') for item in query_params.split('&'))
                    steps = int(params.get('steps', 1))
                    direction = params.get('dir')
                    
                    if direction == 'neg':
                        steps *= -1
                    move_stepper('x', steps)
                except Exception as e:
                    print(f"Error parsing X move request: {e}")
        elif path.startswith("/y_move"):
            if 'steps=' in path and 'dir=' in path:
                try:
                    query_params = path.split('?')[1]
                    params = dict(item.split('=') for item in query_params.split('&'))
                    steps = int(params.get('steps', 1))
                    direction = params.get('dir')
                    
                    if direction == 'neg':
                        steps *= -1
                    move_stepper('y', steps)
                except Exception as e:
                    print(f"Error parsing Y move request: {e}")
        elif path.startswith("/z_move"):
            if 'steps=' in path and 'dir=' in path:
                try:
                    query_params = path.split('?')[1]
                    params = dict(item.split('=') for item in query_params.split('&'))
                    steps = int(params.get('steps', 1))
                    direction = params.get('dir')
                    
                    if direction == 'neg':
                        steps *= -1
                    move_stepper('z', steps)
                except Exception as e:
                    print(f"Error parsing Z move request: {e}")

        # Handle homing commands
        elif path == "/x_home":
            home_axis('x')
        elif path == "/y_home":
            home_axis('y')
        elif path == "/z_home":
            home_axis('z')

    response = web_page() # Generate the page with updated positions

    conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    conn.send(response)
    conn.close()