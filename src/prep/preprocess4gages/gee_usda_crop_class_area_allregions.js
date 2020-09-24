var gagesMxWdShld = ee.FeatureCollection("users/wenyu_ouyang/bas_nonref_MxWdShld"),
    usda_crop = ee.ImageCollection("USDA/NASS/CDL"),
    gagesEastHghlnds = ee.FeatureCollection("users/wenyu_ouyang/bas_nonref_EastHghlnds"),
    gagesCntlPlains = ee.FeatureCollection("users/wenyu_ouyang/bas_nonref_CntlPlains"),
    gagesNorthEast = ee.FeatureCollection("users/wenyu_ouyang/bas_nonref_NorthEast"),
    gagesSECstPlain = ee.FeatureCollection("users/wenyu_ouyang/bas_nonref_SECstPlain"),
    gagesSEPlains = ee.FeatureCollection("users/wenyu_ouyang/bas_nonref_SEPlains"),
    gagesWestMnts = ee.FeatureCollection("users/wenyu_ouyang/bas_nonref_WestMnts"),
    gagesWestPlains = ee.FeatureCollection("users/wenyu_ouyang/bas_nonref_WestPlains"),
    gagesWestXeric = ee.FeatureCollection("users/wenyu_ouyang/bas_nonref_WestXeric"),
    allref_shp = ee.FeatureCollection("users/wenyu_ouyang/bas_ref_all");
var year_start = 2009;
var year_end = 2010;

var str_allref = "allref";
var CntlPlains = "CntlPlains";
var EastHghlnds = "EastHghlnds";
var MxWdShld = "MxWdShld";
var NorthEast = "NorthEast";
var SECstPlain = "SECstPlain";
var SEPlains = "SEPlains";
var WestMnts = "WestMnts";
var WestPlains = "WestPlains";
var WestXeric = "WestXeric";

function calculateClassesArea(year_num, region_name, region_shape) {
    var year = ee.Number(year_num);
    var month = ee.Number(1);
    var day = ee.Number(1);
    var start_date = ee.Date.fromYMD(year, month, day);
    var end_date = start_date.advance(1, 'year');
    print(end_date);

    // get Imagecollection and filter, firstly choose one image to calculate
    var usda_crop_scene = usda_crop.filter(ee.Filter.date(start_date, end_date)).first();
    var cropLandcover = usda_crop_scene.select('cropland');
    Map.setCenter(-85.55, 45.71, 4);
    // Map.addLayer(cropLandcover, {}, 'Crop Landcover');
    print(cropLandcover);
    print(region_name, region_shape.limit(5));
    // Map.addLayer(region_shape, {color: 'purple'},region_name+' basins');


    // Area Calculation by Class by basins

    // We saw how we can calculate areas by class for the whole region
    // What if we wanted to know the breakup of these class areas by each basin?
    // This requires one more level of processing.
    // We can apply a similar computation as above, but
    // by applying .map() on the Feature Collection to obtain the values by each district geometies

    var calculateClassArea = function (feature) {
        var areas = ee.Image.pixelArea().addBands(cropLandcover).reduceRegion({
            reducer: ee.Reducer.sum().group({
                groupField: 1,
                groupName: 'class',
            }),
            geometry: feature.geometry(),
            scale: 30,
            maxPixels: 1e10
        });
        var classAreas = ee.List(areas.get('groups'));
        var classAreaLists = classAreas.map(function (item) {
            var areaDict = ee.Dictionary(item);
            var classNumber = ee.Number(areaDict.get('class')).format();
            var area = ee.Number(areaDict.get('sum')).round();
            return ee.List([classNumber, area]);
        });
        var result = ee.Dictionary(classAreaLists.flatten());
        // The result dictionary has area for all the classes
        // We add the district name to the dictionary and create a feature
        var district = feature.get('GAGE_ID');
        return ee.Feature(feature.geometry(), result.set('GAGE_ID', district));
    };

    var districtAreas = region_shape.map(calculateClassArea);

    // One thing to note is that each district may or may not have all
    // of the 17 classes present. So each feature will have different
    // number of attributes depending on which classes are present.
    // We can explicitly set the expected fields in the output
    // so we get a homogeneous table with all classes
    var classes = ee.List.sequence(0, 255);
    // As we need to use the list of output fields in the Export function
    // we have to call .getInfo() to get the list values on the client-side
    // this will be the clolumn names
    var outputFields = ee.List(['GAGE_ID']).cat(classes).getInfo();

    // Export the results as a CSV file

    Export.table.toDrive({
        collection: districtAreas,
        description: 'class_area_by_basins_of_' + region_name + "_" + year_num,
        folder: 'USDA',
        fileNamePrefix: 'class_area_by_basins_of_' + region_name + "_" + year_num,
        fileFormat: 'CSV',
        selectors: outputFields
    });
    return 0;
}

var year_num;
for (year_num = year_start; year_num < year_end; year_num++) {
    calculateClassesArea(year_num, str_allref, allref_shp);
    calculateClassesArea(year_num, CntlPlains, gagesCntlPlains);
    calculateClassesArea(year_num, EastHghlnds, gagesEastHghlnds);
    calculateClassesArea(year_num, MxWdShld, gagesMxWdShld);
    calculateClassesArea(year_num, NorthEast, gagesNorthEast);
    calculateClassesArea(year_num, SECstPlain, gagesSECstPlain);
    calculateClassesArea(year_num, SEPlains, gagesSEPlains);
    calculateClassesArea(year_num, WestMnts, gagesWestMnts);
    calculateClassesArea(year_num, WestPlains, gagesWestPlains);
    calculateClassesArea(year_num, WestXeric, gagesWestXeric);
}