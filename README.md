<h1> Simple Computation of Thermal Bridges </h1>

2025-11-08 by Fritz Crusius<br><br>

Project provides a simple method for the computation of temperatures along thermal bridges in buildings.
<br><br>
This project produced images in German blog article on heat bridges
https://energieoekonom.de/das-problem-der-innendaemmung/.

<h2>Producing a Model Image</h2>

Use a grapics program, such as Inkskape, to produce a grayscale PNG image
reflecting the zones and materials of the cross-section forming a thermal
bridge. Export without anti-aliasing to avoid creating additional gray tones
in between zones. In the image, the inner (warm) side maps to the top, and
the outer (cold) side to the bottom. So most cross-sections of heat bridges
need be rotated 90 degrees clockwise.
<br>
Check image in viewer for unwanted gaps or other issues.
<br><br>
Do a test run with the image to check its gray scale values.
<br><br>
Sample command line:<br>
```
$> ./png_model_2d.py -print_values_only=1 -pixel_step 10 svg/bridge_plain.png

Colors and counts in image:
[[     0.     489231.    ]
 [     0.3647  93822.    ]
 [     0.6784 196365.    ]
 [     0.8     31968.    ]
 [     0.902  153822.    ]
 [     1.       1824.    ]]
Colors and counts in pixelmatix:
[[   0.     4894.    ]
 [   0.3647  996.    ]
 [   0.6784 1968.    ]
 [   0.8     300.    ]
 [   0.902  1526.    ]
 [   1.       16.    ]]

```
The output indicates there were six colors from black (0.0) to white (1.0) in 
the image. In the original image, 489231 pixels were black. In the reduced 
image (by factor 10, as indicated by '-pixel_step 10'), there are just 4894 
black pixels. Selecting every 10th pixel in rows and columns thus results in 
a factor 100 size reduction. This is done to obtain a cruder image sample
that's small enough to fit in a matrix defining an equation system.

<h2>Map Heat Conductivities to Graystep Colors</h2>

All materials in the image map to a heat conductivity defined in a .csv file
with the path of the .png image and an extension .csv, as in <br>
```
svg/bridge_plain.png
svg/bridge_plain.png.csv
```

Construction materials, such as brick walls, concrete, or insulation layers 
just have their known heat conductivities assigned. An exception are the 
inner and outer air layers that add R_se and R_si:<br>
```
R_se=0.04 m^2K/W
R_si=0.13 m^2K/W
```
So the inner and outer insulating air layers must have a heat conductivity 
such that the target resistances are met. The spreadsheet <br>
```
svg/bridge_plain.dimensions.xlsx
```
has a sample computation. With a known thickness 36.5 cm of the outer wall,
97 rows in the matrix, and 21 rows for the 36.5 cm, the sheet computes an
overall distance warm -> cold of 1.686 m. With 3 rows in the image matrix 
for R_se and 7 rows for R_si, the sheet then computes conductivities: <br>
```
Lambda_e=1.3036
Lambda_i=0.9359
```
These results complete the gray scale to heat conductivity map. The 1 pixel
insulation layer of conductivity zero is to cut free the modeled area, assuming
no heat flow in the concrete ceiling from this point on. This reflects a modeling 
imperfection due to the limited size of the cross section.<br>
```
svg/bridge_plain.png.csv
```

<h2>Sample Command Lines</h2>

To produce images in the root directory, use the following sample command lines:
```
$> ./png_model_2d.py -pixel_step=10 ./svg/bridge_plain.png
```

To get the CSV formatted dumps of computation results, add -csv_dump=1:
```
$> ./png_model_2d.py -pixel_step=10 -csv_dump=1 ./svg/bridge_plain.png
```








