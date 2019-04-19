# execfile(r'C:\Users\delph\Desktop\GIS\ArcPy_Scripts\UrbanGrowth4Categories.py')

# Overview: Compute urban growth in the 148 largest U.S. metropolitan areas between
# 2000 and 2010 for various population density ranges. For more information, 
# see the project report: http://bit.ly/urban-growth-report

import arcpy
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')

# *****************************************
# Set up essential constants:
highUrbanThreshold = 2208.7362
mediumUrbanThreshold = 1000
lowUrbanThreshold = 386.10337
# Choose a suffix for the new Geodatabase:
nameSuffix = "1000_2208"
gdbName = "Growth" + nameSuffix + ".gdb"
# List of categories to be computed:
typeList = ["Total","AllUrban", "HighUrban","MediumUrban", "LowUrban", "Rural"]
path = "C:\\Users\\delph\\Desktop\\GIS\\586\\FinalProject\\Data\\"
#Input datasets:
origPopDens2000Raster = "PopDens2000_minus_water_ras_500"
origPopDens2010Raster = "PopDens2010_minus_water_ras_500"
metropolitanZones = "Metropolitan_areas_cities_gt_100k_mainland_lean"

# *****************************************
# Functions

# ********
# Create a new geodatabase and  to put all the output for this batch:
def prepGdb():
    arcpy.CreateFileGDB_management (path, gdbName)
    arcpy.Copy_management (path + "Temp.gdb" + "\\" + origPopDens2000Raster, path + gdbName + "\\" + origPopDens2000Raster )
    arcpy.Copy_management (path + "Temp.gdb" + "\\" + origPopDens2010Raster, path + gdbName + "\\" + origPopDens2010Raster )
    arcpy.Copy_management (path + "Temp.gdb" + "\\" + metropolitanZones, path + gdbName + "\\" + metropolitanZones )

# ********
# Set up the ArcGIS environment variables:
def setupEnv():
    arcpy.env.workspace = path + gdbName
    arcpy.env.overwriteOutput = True
    currentExtent = origPopDens2010Raster
    arcpy.env.mask = currentExtent
    arcpy.env.extent = currentExtent
    arcpy.env.snapraster = currentExtent
    arcpy.env.outputCoordinateSystem = currentExtent
    arcpy.env.cellSize = currentExtent #500

# ********
# Generate diff raster 2010 - 2000
def generateDiffRasters(raster2000, raster2010):
    # We devide the result by 4 to obtain an est. count of residents (instead of a density)
    outDiffRaster = (raster2010 - raster2000)/4
    outDiffRaster.save("PopCountDiff_2010_2000")
# ********
# Generate range rasters for a given year for different levels of density (Total, All urban, High urban, Low urban, and Rural):
def generateRangeRasters(inRaster, year):
    print "Generate range rasters for " + year + " for different levels of density (Total, All urban, High urban, Low urban, and Rural)"
    for type in typeList:
        if type == "Total":
            # We devide InRaster by 4 to obtain an est. count of residents (instead of a density)
            outRaster1 = Con(inRaster != 0, inRaster/4, 0)
        elif type == "AllUrban":
            outRaster1 = Con(inRaster >= lowUrbanThreshold, inRaster/4, 0)
        elif type == "HighUrban":
            outRaster1 = Con(inRaster >= highUrbanThreshold, inRaster/4, 0)
        elif type == "MediumUrban":
            outRaster1 = Con((inRaster >= mediumUrbanThreshold) & (inRaster < highUrbanThreshold), inRaster/4, 0)
        elif type == "LowUrban":
            outRaster1 = Con((inRaster >= lowUrbanThreshold) & (inRaster < mediumUrbanThreshold), inRaster/4, 0)
        elif type == "Rural":
            outRaster1 = Con(inRaster < lowUrbanThreshold, inRaster/4, 0)

        outRaster2 = SetNull(outRaster1 == 0, outRaster1)
        outRaster2.save("PopCount" + year + type)

# ********
# Create zonal statistics tables at the metropolitan area level for every density type for a given year:
def generateZonalStats(year):
    print "Create zonal statistics tables at the metropolitan area level for every density type for " + year
    for type in typeList:
        generateZonalStatsSub(year, type)

# Generate one zonal statistics table at a time:
def generateZonalStatsSub(year, type):
    print "Create zonal statistics table for " + year + " " + type
    rasterForZonalIn = Raster("PopCount" + year + type)
    zonalTableOut = "PopCount" + year + type + "_zonal"
    outZSaT = ZonalStatisticsAsTable(metropolitanZones, "GEOID", rasterForZonalIn,
        zonalTableOut, "DATA", "SUM")
    arcpy.DeleteField_management (zonalTableOut, "ZONE_CODE")

# ********
#Join zonal tables to metropolitanZones feature class for all years:
def joinZonalInfo():
    print "Join zonal tables to metropolitanZones feature class for all years"
    # Try removing metropZoneLayer before creating it,
    # in case it was leftover from a previous process:
    arcpy.Delete_management("metropZoneLayer")
    arcpy.MakeFeatureLayer_management(metropolitanZones, "metropZoneLayer")

    joinZonalInfoSub("2000")
    joinZonalInfoSub("2010")

    print "Save new features class with all the join to *MetropolitanZonesWithInfo*"
    arcpy.CopyFeatures_management("metropZoneLayer", "MetropolitanZonesWithInfo")
    # We don't need "metropZoneLayer" any longer, so we remove it:
    arcpy.Delete_management("metropZoneLayer")

    cleanFields("2000")
    cleanFields("2010")

# Join zonal tables for one given year:
def joinZonalInfoSub(year):
    print  "Join the zonal tables for " + year
    for type in typeList:
        zonalTableOut = "PopCount" + year + type + "_zonal"
        arcpy.AddJoin_management ("metropZoneLayer", "GEOID", zonalTableOut, "GEOID", "KEEP_ALL")

# Create clearly named field in MetropolitanZonesWithInfo for a given year:
def cleanFields(year):
    print "Create clearly named field in MetropolitanZonesWithInfo for " + year
    codeblock = """def handleNull(num):
        if not num:
            return 0
        else:
            return num"""
    for type in typeList:
        arcpy.AddField_management("MetropolitanZonesWithInfo", type + "Count" + year, "DOUBLE")
        arcpy.CalculateField_management("MetropolitanZonesWithInfo", type + "Count" + year, "handleNull(!PopCount" + year + type + "_zonal_SUM!)", "PYTHON_9.3", codeblock)

# ****
# Perform computations between attributes of a same year within MetropolitanZonesWithInfo feature class:
def performComputations(year):
    print "Perform computations between " + year + "-related attributes within MetropolitanZonesWithInfo feature class"
    metropolitanZones = "MetropolitanZonesWithInfo"
    # First, let's create a field to check that our computations so far were correct: Rural + lowUrban + HighUrban
    # Making sure the new field does not already exist:
    if len(arcpy.ListFields(metropolitanZones,"LowPlusHighPlusRural"+ year))<=0:
        arcpy.AddField_management(metropolitanZones, "LowPlusHighPlusRural" + year, "DOUBLE")
    arcpy.CalculateField_management(metropolitanZones, "LowPlusHighPlusRural" + year, "!RuralCount" + year + "! + !LowUrbanCount" + year + "! + !HighUrbanCount" + year +"!", "PYTHON_9.3")

    #Then compute the ratios of each population type to the entire population:
    for type in typeList:
        if len(arcpy.ListFields(metropolitanZones, type + "OverTotal"+ year))<=0:
            arcpy.AddField_management(metropolitanZones,  type + "OverTotal" + year, "DOUBLE")
        arcpy.CalculateField_management(metropolitanZones, type + "OverTotal" + year, "(!" + type + "Count" + year + "! / !TotalCount" + year + "!) * 100", "PYTHON_9.3")

# Compute the difference in population count and % change between 2010 and 2000 for all types:
def performComputationsInterYears():
    print "Compute the difference in population count and % change between 2010 and 2000 for all types"
    metropolitanZones = "MetropolitanZonesWithInfo"
    # Compute the difference in population count between 2010 and 2000 for all types
    # Making sure the new field does not already exist:
    for type in typeList:
        if len(arcpy.ListFields(metropolitanZones,"Diff" + type + "2010_2000"))<=0:
            arcpy.AddField_management(metropolitanZones, "Diff" + type + "2010_2000", "DOUBLE")
        arcpy.CalculateField_management(metropolitanZones,"Diff" + type + "2010_2000", "!" + type + "Count2010! - !"  + type + "Count2000!", "PYTHON_9.3")

    # Compute the % of change for the different types
    for type in typeList:
        if len(arcpy.ListFields(metropolitanZones,"PctGrowth" + type + "2010_2000"))<=0:
            arcpy.AddField_management(metropolitanZones, "PctGrowth" + type + "2010_2000", "DOUBLE")
        arcpy.CalculateField_management(metropolitanZones,"PctGrowth" + type + "2010_2000", "(!Diff" + type + "2010_2000! / !"  + type + "Count2000!)*100", "PYTHON_9.3")


#export the attribute table for MetropolitanZonesWithInfo to CSV for further processing in a spreadsheet program
def export():
    spreadsheetName = "FinalGrowthTable" + nameSuffix + ".csv"
    arcpy.TableToTable_conversion ("MetropolitanZonesWithInfo", path + "\\finalSpreadsheets", spreadsheetName)

# ***************************************
# Begin Main
print "Start Processing"
    prepGdb()
    setupEnv()
    #generateDiffRasters(Raster(origPopDens2000Raster),Raster(origPopDens2010Raster))

    generateRangeRasters(Raster(origPopDens2010Raster), "2010")
    generateRangeRasters(Raster(origPopDens2000Raster), "2000")

    generateZonalStats("2000")
    generateZonalStats("2010")
    joinZonalInfo()

    performComputations("2000")
    performComputations("2010")
    performComputationsInterYears()

    export()

print('Done Processing')
