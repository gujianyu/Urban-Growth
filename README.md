# Urban-Growth

## Overview
Compute urban growth in the 148 largest U.S. metropolitan areas between
2000 and 2010 for various population density ranges. For more information, see the project report: http://bit.ly/urban-growth-report

## Main steps
1. Create a new geodatabase to put in it all the outputs for one round of tests.
2. Set up various environment variables and constants, including the threshold values currently tested.
3. Generate the range rasters using map algebra. The output will be one raster for all cells that are within the Very Low Urban density range, one for all cells within the Low Urban density, and one for all cells within the High Urban density. Do this for both year 2000 and 2010 separately. Note that at that stage, I divide each cell value by 4, to go from a population density per square kilometer to a population count per cell of 500 by 500 meters.
4. Since we are at it, compute also a few supplementary range rasters that will come handy: one for all urban density (regardless of whether it is Very Low, Low, or High), one for Rural density, and one for all the cells in the raster. So all in all there are now 6 categories, which, applied to year 2000 and 2010, generates 12 new rasters.
5. Generate zonal statistics for the 12 rasters, using the 148 MA boundaries for the zones, and choosing SUM as the operation [ tool Zonal Statistics as Table]. This will give us the estimated number of people who live in each density category in each MA.This process generates 12 separate tables.
6. Join all 12 tables to the MA boundary layer, and save it as a new feature class.
7. Create several new attributes in the new feature class, putting in it the result of several computations among  existing attributes. Here are the computations:
    * Sum up Very Low Urban, Low Urban, High Urban and Rural density values. This is just a basic check to make sure that the result is equal to the total population in each MA. 
    * Compute the ratio between the estimated population in each density category and the total population in each MA.
    * Compute the difference between 2000 and 2010 for every density category in every MA.
    * Compute the percent of growth compared to 2000 for every density category in every MA.
8. Finally, export the attribute table to a csv file. This enables post processing in a spreadsheet application.
