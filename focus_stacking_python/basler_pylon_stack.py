from pypylon import pylon
import time
import urllib.request
import os


num_img_to_save = 10
stepper_steps_per = 20


imageWindow = pylon.PylonImageWindow()
imageWindow.Create(1)

img = pylon.PylonImage()
tlf = pylon.TlFactory.GetInstance()

cam = pylon.InstantCamera(tlf.CreateFirstDevice())
cam.Open()
print("Using device ", cam.GetDeviceInfo().GetModelName())



# Set the Exposure Auto auto function to its minimum lower limit
# and its maximum upper limit
minLowerLimit = cam.AutoExposureTimeLowerLimitRaw.Min
maxUpperLimit = cam.AutoExposureTimeUpperLimitRaw.Max
cam.AutoExposureTimeLowerLimitRaw.Value = minLowerLimit
cam.AutoExposureTimeUpperLimitRaw.Value = maxUpperLimit
# Set the target brightness value to 128
cam.AutoTargetValue.Value = 128
# Select auto function ROI 1
cam.AutoFunctionAOISelector.Value = "AOI1"
# Enable the 'Intensity' auto function (Gain Auto + Exposure Auto)
# for the auto function ROI selected
cam.AutoFunctionAOIUsageIntensity.Value = True
# Enable Exposure Auto by setting the operating mode to Continuous
cam.ExposureAuto.Value = "Continuous"




cam.StartGrabbing()

timestr = time.strftime("%Y%m%d-%H%M%S")
if not os.path.exists(timestr):
    os.makedirs(timestr)
    
for i in range(num_img_to_save):
    with cam.RetrieveResult(2000) as result:
    
        imageWindow.SetImage(result)
        imageWindow.Show()
    
        # Calling AttachGrabResultBuffer creates another reference to the
        # grab result buffer. This prevents the buffer's reuse for grabbing.
        img.AttachGrabResultBuffer(result)
        filename = timestr+"/stack_"+str(i)+".png"
        #img.Save(pylon.ImageFileFormat_Tiff, filename)
        img.Save(pylon.ImageFileFormat_Png, filename)
        img.Release()


    urllib.request.urlopen("http://192.168.1.70/z_move?steps="+str(stepper_steps_per)+"&dir=pos").read()
    time.sleep(3)

