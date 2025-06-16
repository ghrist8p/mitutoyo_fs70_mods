from pypylon import pylon
import time
import urllib.request
import os
import cv2
import numpy as np


#AD7177
x_step_size = 20
x_step_count = 16
y_step_size = 15
y_step_count = 20


# ADA4523
#x_step_size = 20
#x_step_count = 12
#y_step_size = 15
#y_step_count = 11

# ICL7650
#x_step_size = 20
#x_step_count = 12
#y_step_size = 15
#y_step_count = 12

autofocus_range = 200  # Total range (in steps) to search for focus
autofocus_step_size = 20 # Smaller step size for autofocusing

imageWindow = pylon.PylonImageWindow()
imageWindow.Create(1)

img = pylon.PylonImage()

cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

# Register the standard configuration event handler for enabling software triggering.
# The software trigger configuration handler replaces the default configuration
# as all currently registered configuration handlers are removed by setting the registration mode to RegistrationMode_ReplaceAll.
cam.RegisterConfiguration(pylon.SoftwareTriggerConfiguration(), pylon.RegistrationMode_ReplaceAll,
                          pylon.Cleanup_Delete)

cam.Open()
print("Using device ", cam.GetDeviceInfo().GetModelName())


# Set the Exposure Auto auto function to its minimum lower limit
# and its maximum upper limit
#minLowerLimit = cam.AutoExposureTimeLowerLimitRaw.Min
#maxUpperLimit = cam.AutoExposureTimeUpperLimitRaw.Max
#cam.AutoExposureTimeLowerLimitRaw.Value = minLowerLimit
#cam.AutoExposureTimeUpperLimitRaw.Value = maxUpperLimit
# Set the target brightness value to 128
#cam.AutoTargetValue.Value = 128
# Select auto function ROI 1
#cam.AutoFunctionAOISelector.Value = "AOI1"
# Enable the 'Intensity' auto function (Gain Auto + Exposure Auto)
# for the auto function ROI selected
#cam.AutoFunctionAOIUsageIntensity.Value = True
# Enable Exposure Auto by setting the operating mode to Continuous
#cam.ExposureAuto.Value = "Continuous"


# Or better set everything to constant for pano stitching
cam.ExposureAuto.SetValue("Off")
cam.ExposureMode.SetValue("Timed")
cam.ExposureTimeAbs.SetValue(50000)

cam.GainAuto.SetValue("Off")
cam.GainRaw.SetValue(300)




cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)


converter = pylon.ImageFormatConverter()

# converting to opencv bgr format
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned


timestr = time.strftime("%Y%m%d-%H%M%S")
if not os.path.exists(timestr):
    os.makedirs(timestr)

x_dir = -1 # For snake-like back n forth movement
x_coord = 0 # At what step we are for file naming

def variance_of_laplacian(image):
    image_filtered = cv2.medianBlur(image, 1)
    return cv2.Laplacian(image_filtered, cv2.CV_64F).var()
    

def autofocus(camera, z_axis_url_base, autofocus_range, autofocus_step_size):
    print("Starting autofocus...")
    best_focus_score = -1
    best_z_pos = 0

    # Store (focus_score, z_position) pairs
    focus_scores_and_positions = []

    # Move to the start of the sweep
    url = f"{z_axis_url_base}?steps={int(autofocus_range/2)}&dir=pos"
    urllib.request.urlopen(url).read()

    # Sweep through the autofocus range
    for z_move in range(int(autofocus_range/autofocus_step_size)):
        url = f"{z_axis_url_base}?steps={autofocus_step_size}&dir=neg"
        with urllib.request.urlopen(url) as response:
            html_content = response.read().decode('utf-8')
        
        # Extract current pos
        start_tag = '<span id="z_pos">'
        end_tag = '</span>'
        start_index = html_content.find(start_tag)
        end_index = html_content.find(end_tag, start_index)
        value_str = html_content[start_index + len(start_tag):end_index]
        current_z_pos = int(value_str)

        # Capture an image
        if camera.WaitForFrameTriggerReady(1000, pylon.TimeoutHandling_ThrowException):
            camera.ExecuteSoftwareTrigger()
            time.sleep(1) # Small delay for camera to capture
            with camera.RetrieveResult(0, pylon.TimeoutHandling_Return) as result:
                imageWindow.SetImage(result)
                imageWindow.Show()
                if result.GrabSucceeded():
                    # Convert Pylon image to OpenCV format
                    image = converter.Convert(result)
                    img_np = image.GetArray()

                    # Calculate focus score
                    focus_score = variance_of_laplacian(img_np)
                    focus_scores_and_positions.append((focus_score, current_z_pos))
                    print(f"Z-pos: {current_z_pos}, Focus Score: {focus_score}")

                    if focus_score > best_focus_score:
                        best_focus_score = focus_score
                        best_z_pos = current_z_pos

    print(f"Autofocus complete. Best focus score: {best_focus_score} at Z-pos: {best_z_pos}")

    # Move to the best focus position
    final_move_steps = best_z_pos - current_z_pos

    if final_move_steps > 0:
        url = f"{z_axis_url_base}?steps={abs(final_move_steps)}&dir=pos"
    elif final_move_steps < 0:
        url = f"{z_axis_url_base}?steps={abs(final_move_steps)}&dir=neg"
    else:
        print("Already at optimal focus position.")
        return best_z_pos

    try:
        urllib.request.urlopen(url).read()
        time.sleep(0.5)
        print(f"Moved Z-axis to optimal position: {best_z_pos}")
    except Exception as e:
        print(f"Error moving Z-axis to optimal position: {e}")
    
    return best_z_pos


def snap(cam, y, x):

    if cam.WaitForFrameTriggerReady(1000, pylon.TimeoutHandling_ThrowException):
        cam.ExecuteSoftwareTrigger()
        time.sleep(0.2)
        if cam.GetGrabResultWaitObject().Wait(0):
            with cam.RetrieveResult(0, pylon.TimeoutHandling_Return) as result:

                # Grab and show image
                imageWindow.SetImage(result)
                imageWindow.Show()

                # Calling AttachGrabResultBuffer creates another reference to the
                # grab result buffer. This prevents the buffer's reuse for grabbing.
                img.AttachGrabResultBuffer(result)

                filename = timestr+"/y"+str(y)+"_x"+str(x)+".png"
                img.Save(pylon.ImageFileFormat_Png, filename)
                img.Release()


current_z_position_steps = 0

# Main loop with autofocus
for y in range(y_step_count):
    print(f"\n--- Starting row {y}, performing autofocus ---")
    current_z_position_steps = autofocus(
        cam,
        "http://192.168.1.70/z_move",
        autofocus_range,
        autofocus_step_size
    )
    print(f"Autofocus completed for row {y}. Current Z-position: {current_z_position_steps}")

    snap(cam, y, x_coord) # Take the first snap after autofocus

    x_dir = x_dir*-1
    for x in range(x_step_count-1):

        x_coord = x_coord + x_dir

        # Advance in x in alternating directions
        if x_dir == 1:
            urllib.request.urlopen("http://192.168.1.70/x_move?steps="+str(x_step_size)+"&dir=pos").read()
        else:
            urllib.request.urlopen("http://192.168.1.70/x_move?steps="+str(x_step_size)+"&dir=neg").read()

        time.sleep(1)
        current_z_position_steps = autofocus(
            cam,
            "http://192.168.1.70/z_move",
            autofocus_range,
            autofocus_step_size
        )
        print(f"Autofocus completed for snap {x}. Current Z-position: {current_z_position_steps}")
        snap(cam, y, x_coord)

    # Advance in y
    urllib.request.urlopen("http://192.168.1.70/y_move?steps="+str(y_step_size)+"&dir=neg").read()


# Cleanup
cam.StopGrabbing()
cam.Close()
