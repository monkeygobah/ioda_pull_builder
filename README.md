# ioda_pull_builder
Quick front end to build pull requests from IODA ophthalmic database

## Usage
![image](https://github.com/user-attachments/assets/017320ce-343f-4070-9a1d-8c4f945228fc)


1. Select which diseases you want (you can type on the left box and autocomplete will try and kick in)
2. Move them to window on right for easy visibility
3. Select again which diseases from right pane (for some reason script wont work unless they are selected there as well
4. Select which image modalities
5. Click filter to launch scrape

Outputs the number of images for each disease as well as the number of unique MRNs

![image](https://github.com/user-attachments/assets/bd9f28e5-a005-4d48-b5c2-21fa2dfab5aa)

At the bottom, tells you the percentage of images retrieved based on selected imaging modalities

![image](https://github.com/user-attachments/assets/5bf90f88-813f-4e57-87a5-245a3e4f31f1)

Click 'Download Filtered CSV' to download a copy of the results

![image](https://github.com/user-attachments/assets/37e9e086-c642-4caf-9608-ad373d753916)


## Accessing IODA

You will need access to the de_images_diagnosis_joined.csv file. This can be found on IODA and downloaded locally. 2 ways to connect to IODA from Dennis' writing on Confluence


- Browser:
  Navigate to 10.157.80.76/aio
  Log in with your UIC netid 

- Mount (more consistent in my experience):
  Windows, in the explorer window
  \\10.157.80.76\aio

  Mac, in connect to server:
  smb://10.157.80.76/aio

## Grabbing images

To use the ouput to grab the images from IODA, you will have to build the file path from the filtered CSV to get a list of the full paths you want, and then loop over IODA to download locally. For me, this is easiest to do when using IODA on mount. This UI doesn't include this feature, but could in the future...

