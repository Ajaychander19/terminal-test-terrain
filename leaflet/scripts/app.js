window.addEventListener('unload', function (e) {
    e.preventDefault();
    $.get('/shutdown', function(){
    });
}, false);



var baselayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
});
    
var darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'	})
    
var baseMaps = {
    "baselayer": baselayer,
    "darkLayer": darkLayer
};



var map = L.map('map',{center:[47.148, 4.474],maxZoom: 17, zoom:6,layers:[baselayer]});


var point = {
    "type": "FeatureCollection",
    "properties":"",
    "features" : []
}

var basemap={"baselayer":baselayer}
var ColorChoice = 0;

var layercontrol = L.control.layers(baseMaps,null,{ collapsed: false }).addTo(map);

var siteserving = L.layerGroup();
var Theory_Cell = L.layerGroup();       // Voronoi cells layer.
var RSRP_offset= L.layerGroup();        // RSRP offset layer
var base_station = L.layerGroup();      // Base station layer.
var Tracking_area=L.layerGroup();
var RSRP = L.layerGroup();              // RSRP hexagonal layer.
var PCI =L.layerGroup();                // PCI GPS points
var hexlayer = L.hexbinLayer(hexbin_style()).hoverHandler(L.HexbinHoverHandler.tooltip()).addTo(map);

var rsrplayer = L.hexbinLayer(hexbin_style(1,
    [
        "black","MidnightBlue","Navy","DarkBlue",
        "MediumBlue","blue","RoyalBlue","DodgerBlue",
        "DeepSkyBlue","LightSkyBlue", "Cyan", "PaleTurquoise",
        "aquamarine","lightgreen","mediumaquamarine","GreenYellow",
        "Lime","chartreuse","yellow","Gold", "orange",
        "DarkOrange", "Coral", "Tomato","Crimson"
    ])).hoverHandler(L.HexbinHoverHandler.tooltip()).addTo(map);

var overlayers={}	
var hexpoints=[]
var rsrpValue_points=[]
var sites={}

var markerObject={}
//==================
function showAlert(message){
    $('#myModal').modal()
    $('.modal-body').html(message);
    $('#myModal').modal('show')
};
// return the style of hexagon correspond for the rsrp checkbox and rsrp offset checkbox.

function hexbin_style(colorDomain,colorRange){
    if (arguments.length===0){
        return{
    
            radius : 12,
            opacity: 0,
            duration: 200,

            colorScaleExtent: [ 1, undefined ],
            radiusScaleExtent: [ 1, undefined ],
            colorDomain: null,
            radiusDomain: null,
            radiusRange: [ 1, 12 ],
            pointerEvents: 'all'
        }
    } else {
        return{
    
            radius : 12,
            opacity: 0,
            duration: 200,

            colorScaleExtent: [ 0, 96 ],
            radiusScaleExtent: [ 1, undefined ],
            colorDomain: "linear",
            radiusDomain: null,
            colorRange:colorRange,
            radiusRange: [ 1, 12 ],
            pointerEvents: 'all'
        }
    }

}

    // get event for the RSRP offset checkbox
$("#RSRP_offset").click(function(event) {
    if(map.hasLayer(RSRP_offset)) {
        hexlayer.data([]);
        hexlayer.redraw()
        map.removeLayer(RSRP_offset);
    } else {
        map.addLayer(RSRP_offset);
        rsrplayer.data([]);
        rsrplayer.redraw()
        hexlayer.opacity(0.8)
        hexlayer.data(hexpoints);
        hexlayer.redraw()
        
    }
});

    // get event for the RSRP checkbox
$("#RSRP").click(function(event) {
    if(map.hasLayer(RSRP)) {
        rsrplayer.data([]);
        rsrplayer.redraw()
        map.removeLayer(RSRP);
    } else {
        map.addLayer(RSRP);
        rsrplayer.opacity(0.8)
        rsrplayer.data([]);
        rsrplayer.redraw()
        rsrplayer.data(rsrpValue_points);
        rsrplayer.redraw()
        
    }
});

    // get event for the Theory cell checkbox
$('#Theory_Cell').change(function() {
    if(map.hasLayer(Theory_Cell)) {
        map.removeLayer(Theory_Cell);
    } else {
        map.addLayer(Theory_Cell);
        
    }
});

// get event for the Alternative Color checkbox
$("#ColorAlt").click(function(event) {

    ColorChoice = 1-ColorChoice;

//			if(map.hasLayer(PCI)) {
//				map.removeLayer(PCI);
//				map.addLayer(PCI);
//			}
});

// get event for the pci checkbox
$("#PCI").click(function(event) {
    


    if(map.hasLayer(PCI)) {
        map.removeLayer(PCI);
    } else {
        map.addLayer(PCI);
        
    }
});

// get event for the Tracking area checkbox
$("#Tracking_area").click(function(event) {
    if(map.hasLayer(Tracking_area)) {
        $(this).removeClass(Tracking_area);
        map.removeLayer(Tracking_area);
    } else {
        map.addLayer(Tracking_area);
    
    }
});

// this fucntion displays the earfcn layer.
$(document).ready(function(){
    $("select").change(function(){
        var selectedEarfcn = $(this).children("option:selected").val();
        if (selectedEarfcn === "All"){
            
            for (var categoryName in overlayers) {
                if (categoryName !== "All"){		
                    overlayers[categoryName].addTo(map);
                }
            }
            
            Object.keys(markerObject).forEach(function(markerID){
                var PCIsvalue=[]
                var title=''
                
                Object.keys(markerObject[markerID]["earfcngroup"]).forEach(function(earfcnItem){
                    PCIsvalue=PCIsvalue.concat(markerObject[markerID]["earfcngroup"][earfcnItem]["object"]["PCIs"]);
                    title=markerObject[markerID]["earfcngroup"][earfcnItem]["object"]["Title"]
                    console.log(markerObject[markerID]["earfcngroup"][earfcnItem]["object"]["PCIs"],"thanh phan")
                })
                
                markerObject[markerID]["layer"]._popup.setContent(loadTemplate('#checkbox_pci',{'Title':title,'PCIs': PCIsvalue,
                'MarkerId':markerObject[markerID]["layer"]._leaflet_id}))
                            
            })
            
            
            
            
        }else if( selectedEarfcn === "None"){
            for (var Name in overlayers) {
                map.removeLayer(overlayers[Name]);
            }
            Object.keys(markerObject).forEach(function(markerID){
                erfcnTemp=Object.keys(markerObject[markerID]["earfcngroup"])[0]
                markerObject[markerID]["layer"]._popup.setContent(loadTemplate('#checkbox_pci',{'Title':markerObject[markerID]
                ["earfcngroup"][erfcnTemp]["object"]["Title"],'MarkerId':markerObject[markerID]["layer"]._leaflet_id}))
            })
            
        }
        else {		
                Object.keys(markerObject).forEach(function(markerID){
                    erfcnTemp=Object.keys(markerObject[markerID]["earfcngroup"])[0]
                    markerObject[markerID]["layer"]._popup.setContent(loadTemplate('#checkbox_pci',{'Title':markerObject[markerID]
                    ["earfcngroup"][erfcnTemp]["object"]["Title"],'MarkerId':markerObject[markerID]["layer"]._leaflet_id}))
                })
        
                for (var Name in overlayers) {
                    if (Name !== selectedEarfcn ){
                            overlayers[Name].clearLayers();
                            map.removeLayer(overlayers[Name]);
                        
                    }else{
                        overlayers[selectedEarfcn].addTo(map);
                        
                        Object.keys(markerObject).forEach(function(markerID){
                            Object.keys(markerObject[markerID]["earfcngroup"]).forEach(function(earfcnItem){
                                if (selectedEarfcn==earfcnItem){
                                    markerObject[markerID]["layer"]._popup.setContent(loadTemplate('#checkbox_pci',
                                        markerObject[markerID]["earfcngroup"][earfcnItem]["object"]))
                                    
                                }
                            })
                        
                        })
                        
                    }
                    
                
                }
            }
    
    });
});

var selectList = document.createElement("select");
var myDiv = document.getElementById("myDiv");
selectList.className = "form-control selectpicker" ;
selectList.id = "EARFCN_select";
myDiv.appendChild(selectList);
var array=[]
array.push("None")
var pathObj={}
//---------------------------------------------------------------------
// this function reads the file from the dialog
function readerAsText(file){

    return new Promise((resolve, reject) => {
        var fr = new FileReader();
        fr.onload = () => {
            resolve(fr.result)
        };
        fr.readAsText(file);
    });
}

//---------------------------------------------------------------------
// this function reads the item in the dialog
function myFunction(){
    var x = document.getElementById("fileElem");
    var txt = "";
    if ('files' in x) {
        
        if (x.files.length == 2) {
            
            for (var i = 0; i < x.files.length; i++) {
                var file = x.files[i];
                
                if ('name' in file) {	
                    if (file.name.split("_")[0] == "sites"){
                    
                        readerAsText(file).then(function(result) {
                            
                            sites_fileName=JSON.parse(result);
                            
                        })
                        
                    }
                    else{
                        
                        readerAsText(file).then(function(result) {
                            
                            cells_fileName=JSON.parse(result);
                            
                        })
                    }
                    
                }
                if (sites_fileName === ""){
                        
                    }
            }
        }else{
            //showAlert("choosing site file and asscociation file")
            showAlert("Please choose a site file and an association file")
            
        }
            
    }
    
}

var sites_fileName=""
var cells_fileName=""
var siteList=[]
var cellList=[]


$('#fileSelect').click(function (e) {
    
    document.getElementById('fileElem').click();
    
});

// get event for the load base stations button
document.getElementById("Base Station").addEventListener("click", function(){
    disabledAllLayer()
    
    readfile(sites_fileName,cells_fileName,map.getBounds(),siteserving,Theory_Cell,RSRP_offset,base_station,
                                    Tracking_area,RSRP,PCI,hexlayer,rsrplayer,overlayers,sites,markerObject)
                        if (map.hasLayer(PCI)) {
                        map.removeLayer(PCI);
        map.addLayer(PCI);
                        }	
})

// get event for the turn_off_serverbutton
document.getElementById("turn_off_server").addEventListener("click", function(){
    $.get('/shutdown', function(){
    });
})

// get event for the clear all button
document.getElementById("Clear All").addEventListener("click", function(){
    disabledAllLayer();
    for (var Name in overlayers) {
        map.removeLayer(overlayers[Name]);
        overlayers[Name].clearLayers();
    }
    
})
    
//---------------------------------------------------------------------	
            // disable all layers except the PCI
function disabledAllLayer(){
    // remove select
    $('#EARFCN_select').empty();
    
    overlayers={}	
    hexpoints=[]
    rsrpValue_points=[]
    array=[]
    array.push("None")					
    ///////////


    hexlayer.data([]);
    hexlayer.redraw();
    $( "#RSRP_offset" ).prop( "checked", false );
    
    rsrplayer.data([]);
    rsrplayer.redraw();
    $( "#RSRP" ).prop( "checked", false );
    map.removeLayer(Theory_Cell);
    Theory_Cell.clearLayers();
    $( "#Theory_Cell" ).prop( "checked", false );
    
    map.removeLayer(siteserving);
    siteserving.clearLayers();
    
    map.removeLayer(Tracking_area);
    Tracking_area.clearLayers();
    $( "#Tracking_area" ).prop( "checked", false );
//  				      map.removeLayer(PCI);
    PCI.clearLayers();
//          				$( "#PCI" ).prop( "checked", false );
    map.removeLayer(siteserving)
    siteserving.clearLayers();
    map.removeLayer(base_station)
    base_station.clearLayers();
}
//---------------------------------------------------------------------
// this function gets the site in the view zone.
//return the list of site in the view zone

var sites_inZone=[]
function getZones(sitefile, boundMap){
    var minlat=Math.min(boundMap._northEast.lat,boundMap._southWest.lat)
    var maxlat=Math.max(boundMap._northEast.lat,boundMap._southWest.lat)
    var minlng=Math.min(boundMap._northEast.lng,boundMap._southWest.lng)
    var maxlng=Math.max(boundMap._northEast.lng,boundMap._southWest.lng)
    var box_map=turf.bboxPolygon([minlng,minlat,maxlng,maxlat])
    
    var zone=turf.bboxPolygon([parseFloat(sitefile[0].lng),parseFloat(sitefile[0].lat),parseFloat(sitefile[0].lng)+
        parseFloat(sitefile[0].dlng),parseFloat(sitefile[0].lat)+parseFloat(sitefile[0].dlat)])
    
    
    var intersection = turf.intersect(box_map, zone)
    
    if (turf.booleanContains(box_map,zone)){
        sites_inZone=sitefile[0].arrayPoint
    }
    else {
        var sites_tempor=[]
        if (intersection !=null){
            if (sitefile[0].zone.length!=0){
                for (var i=0;i<sitefile[0].zone.length;i++) {
                    getZones(sitefile[0].zone[i], boundMap)
                }
            } else{
                for (var j=0;j<sitefile[0].arrayPoint.length;j++){
                    if (turf.booleanContains(box_map, turf.point([sitefile[0].arrayPoint[j].Longitude, sitefile[0].arrayPoint[j].Latitude]))){


                        sites_tempor.push(sitefile[0].arrayPoint[j])
                    }
                }
            }
        }
        if (sites_tempor.length !=0){
            sites_inZone = sites_tempor
        }
    }	
    return sites_inZone
}

//---------------------------------------------------------------------
//this function get the association cell insie the view zone
//input: the list of site in the view zone and the all the cells processed (in python)
//output: the list of association cells
function getCells(siteList,cellfile){
    site_list=new Set();
    cells=[]
    
    siteList.forEach(function(site){
        
        site_list.add(parseInt(site.Identification_number))
        
    })
    cellfile.forEach(function(cell){
    
        if (site_list.has(parseInt(cell.site))){
        
            cells.push(cell)
        }
        
        if (cell.site=="None"){
            cells.push(cell)
        }
    })
    
    return cells
}

//---------------------------------------------------------------------
// this function process the sitefile and cellfile(from python) and call the function for drawing theory cell, pci, tracking area,...
function readfile(sitefile,cellfile,boundMap,siteserving,Theory_Cell,RSRP_offset,base_station,Tracking_area,RSRP,PCI,hexlayer,rsrplayer,overlayers,sites,markerObject){
    var tacSet={};
    var nbid= new Set();
        
    siteList=getZones(sitefile, boundMap)
    cellList=getCells(siteList,cellfile)
    
    if (siteList.length > 2){
        
        
            
            siteList.forEach(function(item){
                var directionpoint=[]
                var site = new L.LatLng(item.Latitude,item.Longitude);
                if (item.pointDestination.length >=1 ){
                    item.pointDestination.forEach(function(point){
                        var pointB = new L.LatLng(point.lat,point.lng)
                        directionpoint.push([site,pointB])
                    })
                }
                else {
                    cir=L.circle([item.Latitude,item.Longitude], {radius:15,opacity: 1,
                                                    color: 'green',interactive:true}).addTo(base_station)
                }
                station = new L.Polyline(directionpoint, {
                            color: 'green',
                            weight: 4,
                            opacity: 1,
                            smoothFactor: 1
                        });
                station.addTo(base_station)
                sites[item.Identification_number]= {}
                sites[item.Identification_number]["site"]=site
                sites[item.Identification_number]["earfcngroup"]={}
            });
            base_station.addTo(map)
            drawVoronoi(siteList,sites,Theory_Cell);
            
        if (cellList.length > 0){	
            stationProcess(cellList,sites,overlayers,Tracking_area,PCI,nbid,siteserving,tacSet,markerObject);
            drawTA(tacSet,sites,Tracking_area);
            
            associateCells(sites,overlayers,siteserving)
        
        
            
            array = array.concat(Object.keys(overlayers))
            array.push("All")
            
            
            for (var i = 0; i < array.length; i++) {
                var option = document.createElement("option");
                option.value = array[i];
                option.text = array[i];
                selectList.appendChild(option);
            }
        }
        else {
            showAlert("There aren't association cells")
        }
    
    }
    else {
        showAlert("There aren't sites in the region")
    }
    map.addLayer(siteserving);
        
}
    
//---------------------------------------------------------------------		
//this function draws the theory cell
function drawVoronoi(listPointSite,sites,Theory_Cell){
    var listSites=[]
    var SitePoly=[];
    var index=0;
    var checksite= new Set();



    listPointSite.forEach(function(item){

    
        if (!(checksite.has(item.Identification_number))){
            checksite.add(item.Identification_number)
            
            
            //console.log(item.Longitude)
            listSites.push(turf.point([item.Longitude,item.Latitude]))
            var templist=[]
            item.pointZone.forEach(function(element){
                var line= turf.lineString([[item.Longitude,item.Latitude],[element.lng,element.lat]])
                templist.push(line)	
            })
            SitePoly.push({"site":new L.LatLng(item.Latitude,item.Longitude),"zone":templist})
            sites[item.Identification_number]["azimuth"]={}
        }
    })
    var SitesCollection = turf.featureCollection(listSites);
    var box = turf.bbox(SitesCollection);
    
    var voronoiPolygons = turf.voronoi(SitesCollection,{bbox:[box[0]-0.015, box[1]-0.015, box[2]+0.015, box[3]+0.015]});     //lef: increase,
    L.geoJSON([voronoiPolygons],{style: style(0.1,"000000")}).addTo(Theory_Cell)
    
    
    for (index = 0; index < voronoiPolygons.features.length; index++){
        var tempolist=[]
        var polygon = voronoiPolygons.features[index];
        
        SitePoly[index].zone.forEach(function(sitelocation){
            var intersectPoint = (turf.lineIntersect(sitelocation, polygon)).features
                if (intersectPoint.length!=0){
                    var intersection = new L.LatLng(intersectPoint[0].geometry.coordinates[1],intersectPoint[0].geometry.coordinates[0]);
                    tempolist.push([intersection,SitePoly[index].site])	
                
            }
                                
            
        })
        line=new L.Polyline(tempolist, {
                                    color: 'green',
                                    weight: 2,
                                    opacity: 1,
                                    smoothFactor: 1
                                }).addTo(Theory_Cell);
    
    }
    return voronoiPolygons
}
//---------------------------------------------------------------------
// create the landmark symbol for the site
var greenIcon = L.icon({
    iconUrl: 'wifi-zone-marker.png',
    shadowUrl: 'site-shadow.png',
    iconSize:     [32, 32], // size of the icon
    shadowSize:   [25, 40], // size of the shadow
    iconAnchor:   [15,28], // point of the icon which will correspond to marker's location

});

//---------------------------------------------------------------------

function style(opac,rand) {

    return {
    weight: 2,
    opacity: 1,
    color: '#'+ rand,
    dashArray: '5',
    fillOpacity: opac,
    fillColor: '#'+ rand,
    };
}

//---------------------------------------------------------------------
// this function draws the tracking area
function drawTA(tacset,sitelist,Tracking_area){
    
    for(var key in tacset) {
        var polylines=[]
        cellsites=tacset[key].cell_site // danh sach cac cell co cung TAC
        
        for (i = 0; i < cellsites.length-1; i++){
            sitegeo = sitelist[cellsites[i]].site
            
            for (j = i+1; j < cellsites.length; j++){
                //console.log(sitelist,"gia tri sitelist")
                polylines.push([sitegeo,sitelist[cellsites[j]].site])
            }
        }
        
        lines = new L.Polyline(polylines, {
                                    color: 'black',
                                    weight: 2,
                                    opacity: 0.5,
                                    smoothFactor: 1
                                }).addTo(Tracking_area).bindPopup(key);
        
    }
    
}

//---------------------------------------------------------------------
//this function map the association cell with correspond site and add to the right earfcn layer
function stationProcess(listpoints,sitesObject,overlayers,Tracking_area,PCI,nbid,siteserving,tacSet,markerObject){
    listpoints.forEach(function(cell){
        TAcolor(cell,Tracking_area)
        PCIcolor(cell,PCI)
        hexpoints = hexpoints.concat(hexbins(cell));
        
        rsrpValue_points = rsrpValue_points.concat(heatpoint(cell))
        if (cell.site!="None"){
        getEarfcnGroup(cell,sitesObject,overlayers);
        //find the TAC and create an object for TAC structure
        
            if (!(tacSet.hasOwnProperty(cell.TAC))){
                tacSet[cell.TAC]= {}//Object.create(Tac)
                tacSet[cell.TAC].tac=cell.TAC
                tacSet[cell.TAC].cell_site=[]
                
                    tacSet[cell.TAC].cell_site.push(cell.site)
                
                
                
                
            }
            
            else{
                if (!tacSet[cell.TAC].cell_site.includes(cell.site)){
                    tacSet[cell.TAC].cell_site.push(cell.site)
                }
                
            }
            
        }
        //----------------------------------------------------
        if (cell.site!="None"){
            if (!(nbid.has(cell.site))){ // marker every site on map
                nbid.add(cell.site);
                //L.marker([sitesObject[cell.site].site.lat,sitesObject[cell.site].site.lng],{icon:greenIcon}).bindPopup((cell.site).toString()).addTo(siteserving)
                var markerPopup= L.marker([sitesObject[cell.site].site.lat,sitesObject[cell.site].site.lng],{icon:greenIcon});
                var markerObj = {'Title': (cell.site).toString(), 'MarkerId': markerPopup._leaflet_id };
                
                
                
                markerPopup.bindPopup(loadTemplate('#checkbox_pci',markerObj),{
                    closeOnClick: false,
                    autoClose: false
                }).addTo(siteserving)
                
                markerObject[markerPopup._leaflet_id]={}
            };
        }
        
    })
}
//---------------------------------------------------------------------
// this function adds the color for the points measured based on the TAC and add these points to a layer
function TAcolor(jsoncell,layer){
    var firstcorlor= jsoncell.TAC.substr(0,2)
    var secondcorlor= jsoncell.TAC.substr(3,5)
    
    var linepoints=[]
    corlor= parseInt(firstcorlor,16).toString(2)+ parseInt(secondcorlor,16).toString(2).substr(6,8)+Array(7).join("0")+ parseInt(secondcorlor,16).toString(2).split("").reverse().join("")
    
    for (var i=0;i<jsoncell.features.length;i++){
        linepoints.push([jsoncell.features[i].lat,jsoncell.features[i].lon])												
    }
    var coverageLayer = new L.GridLayer.MaskCanvas(stylePoints(parseInt(corlor,2).toString(16)));
    coverageLayer.setData(linepoints);
    coverageLayer.addTo(layer)	
}

//---------------------------------------------------------------------
// this function adds the color for the points measured based on the PCI and add these points to a layer
            // PCIPCIPCI
function PCIcolor(jsoncell,layer){
    var linepoints=[]
    var rand = colorNumber(parseTuple(jsoncell.property)[0][1])
    
    for (var j=0; j<jsoncell.features.length; j++) {
        
        linepoints.push([jsoncell.features[j].lat,jsoncell.features[j].lon])												
    }
    
    var PCILayer = new L.GridLayer.MaskCanvas(stylePoints(rand));
    PCILayer.setData(linepoints);
    PCILayer.addTo(layer)	
}
//---------------------------------------------------------------------
// this function returns the style for drawing the points measured
function stylePoints(color){
    return{
        opacity: 1,
        radius: 3,
        color:'#'+ color,
        noMask: true,
        lineColor: '#'+ color,
        useAbsoluteRadius: false
        }
}
//---------------------------------------------------------------------
//This function returns a list of point with the format for drawing rsrp offset hexagon
function hexbins(jsoncell){
    var point=[];
    jsoncell.features.forEach(function(item){
        if (item.RSRP_neighbour>-100 ){
            point.push([item.lon,item.lat,item.RSRP_neighbour])
            
        }
    })
    return point
}

//---------------------------------------------------------------------
//This function returns a list of point with the format for displaying rsrp
function heatpoint(jsoncell){
    var point=[];
    jsoncell.features.forEach(function(item){
        if (item.RSRP>0 ){
            point.push([item.lon,item.lat,item.RSRP-141]) // TRIEU Hoang test color
            //point.push([item.lon,item.lat,item.RSRP])
        }
    })
    return point
}
//---------------------------------------------------------------------
// this function finds the relation of the cells and sector, and stores
function getEarfcnGroup(jsoncell,sitesStation,overlayers){
    var earfcn=parseTuple(jsoncell.property)[0][2]
    
    var Borders=[]
    var Insides=[]
    var concavepoly=[]
    var name= earfcn + " value"
    var mapearfcn= new Set();
    if (!(mapearfcn.has(earfcn))){
        mapearfcn.add(earfcn);
        earfcnlayer = L.layerGroup();
        overlayers[earfcn]=earfcnlayer	
        
    }

    jsoncell.features.forEach(function(item){
    
        if (item.prop == "border"){
            Borders.push(createFeature(item.lat,item.lon,item.RSRP))}
        else if (item.prop == "concave"){
            concavepoly.push(createFeature(item.lat,item.lon,item.RSRP))}
        else {
            Insides.push(createFeature(item.lat,item.lon,item.RSRP))}
        })
    pointconcave=Object.create(point)
    pointInside=Object.create(point)
    pointBorder=Object.create(point)
    pointconcave.properties="concave"
    pointBorder.properties=jsoncell.property
    pointInside.properties=jsoncell.property
    numberidentity=jsoncell.site
    pointconcave.features=concavepoly
    pointBorder.features = Borders
    pointInside.features = Insides
    
    if (!(sitesStation[numberidentity]["earfcngroup"].hasOwnProperty(earfcn))){
        sitesStation[numberidentity]["earfcngroup"][earfcn]={};
        sitesStation[numberidentity]["earfcngroup"][earfcn]["checking"]=false
        sitesStation[numberidentity]["earfcngroup"][earfcn]["cell"]={}
    }
    sitesStation[numberidentity]["earfcngroup"][earfcn]["cell"][jsoncell.property]={"border":pointBorder,"inside":pointInside,"concavepoly":pointconcave,"layer":{}};
}

//---------------------------------------------------------------------
function parseTuple(t) {
    stack=[]
    var items = t.replace(/^\(|\)$/g,'').replace(/'/g, '').split("),(");
    items.forEach(function(val, index, array) {
        stack.push( val.split(", "))
    });
    return stack;
}

//---------------------------------------------------------------------
// this function create the geoJson for maping
function createFeature(lat,lon,rsrp){
    var feature={
                "type": "Feature",
                "property": rsrp,
                "geometry": {
                "type": "Point",
                "coordinates": [parseFloat(lon),parseFloat(lat)]
                }
            }
    
    return feature
}		


//---------------------------------------------------------------------
// this function loads the check box template for each site
function loadTemplate(templateID,object){
    $.tmpl($(templateID), object ).appendTo("#tempID");
    var temp = $('#tempID').html();
    $('#tempID').html('');
    
    return temp;
}


//---------------------------------------------------------------------
// check the checkbox inside the site popup for display or remove the cells
// par1 : the numberId of sector
// par2: PCI value
function check_pci($this,par1,par2,earfcns){
    var isChecked=$this.is(':checked');
    $this.attr('data-value', isChecked);
    
    var tempLayer = L.layerGroup();
    var checkidlayer=0
    var points_cells=sites[par1]["earfcngroup"][earfcns]["cell"]
    
    if (isChecked){
        
        for (var cellKey in points_cells) {
                if (par2== parseTuple(cellKey)[0][1]){
                    pointcell=points_cells[cellKey]
                    
                    var polygonconvex=[]
                    var borderconvex=[]
                    var polylist=[]
                    pointcell.concavepoly.features.forEach(function(item){
                        polygonconvex.push([item.geometry.coordinates[0],item.geometry.coordinates[1]])

                        //borderconvex.push([item.geometry.coordinates[0],item.geometry.coordinates[1]])

                        if ($("#toggle_withoutTraces").is(':checked')==true){
                            L.marker([item.geometry.coordinates[1],item.geometry.coordinates[0]])
                            .bindPopup(cellKey +" "+item.property.toString()).addTo(tempLayer);
                        }


                        pointB = new L.LatLng(item.geometry.coordinates[1],item.geometry.coordinates[0])

                        polylist.push([markerObject[$this.attr('data-markerId')]["layer"]._latlng,pointB])
                    })
                    concaves=turf.polygon([polygonconvex])
                    pointcell.border.features.forEach(function(item){	
//                        borderconvex.push([item.geometry.coordinates[0],item.geometry.coordinates[1]])
//
//                        if ($("#toggle_withoutTraces").is(':checked')==true){
//                            L.marker([item.geometry.coordinates[1],item.geometry.coordinates[0]])
//                            .bindPopup(cellKey +" "+item.property.toString()).addTo(tempLayer);
//                        }
//
//
//                        pointB = new L.LatLng(item.geometry.coordinates[1],item.geometry.coordinates[0])
//
//                        polylist.push([markerObject[$this.attr('data-markerId')]["layer"]._latlng,pointB])
                        
                    })
                    
                    console.log("markerID",$this.attr('data-markerId'))
                    
                    var rand= colorNumber(parseTuple(pointcell.inside.properties)[0][1])
                    
                    
                    var geoJsonLayer = L.geoJSON([concaves],{
                    style: style(0.2,rand)
                    });
                    line = new L.Polyline(polylist, {
                        color: 'blue',
                        weight: 2,
                        opacity: 0.5,
                        smoothFactor: 1
                    });
                //inside
                
                    geoJsonLayer.addTo(tempLayer)
                    pointcell.inside.features.forEach(function(item){	
                    
                        if ($("#toggle_withoutTraces").is(':checked')==true){
                            drawcircle(item,rand,tempLayer)
                        }
                    
                    })
                    
                    line.addTo(tempLayer)
                    tempLayer.addTo(overlayers[earfcns])
                }
        
            points_cells[cellKey]["layer"][par1+"_"+par2]=tempLayer._leaflet_id
        }
        
    } 				
                            
    else{
        for (var cellKey in points_cells) {
            if (par2== parseTuple(cellKey)[0][1]){	
                    overlayers[earfcns].removeLayer(points_cells[cellKey]["layer"][par1+"_"+par2]);
                    
            }
        }
    }
    
    var markerId = $this.attr('data-markerId');
    siteserving._layers[markerId]._popup.setContent()
    
}


//---------------------------------------------------------------------
// Add the cell information into the site check box
function associateCells(sites,overlayers,siteserving){
    siteserving.eachLayer(function(marker) {
    
        if (Object.keys(markerObject).includes((marker._leaflet_id).toString())){
            var doc = $.parseHTML(marker._popup._content);
            numberId =$('span[name="title"]', doc).attr('data-value').toString()
            markerObject[marker._leaflet_id]["layer"]=marker
            markerObject[marker._leaflet_id]["earfcngroup"]={}
            Object.keys(sites[numberId]["earfcngroup"]).forEach(function(earfcnkey){
            
                
                var points_cells= sites[numberId]["earfcngroup"][earfcnkey]["cell"]
                PCIS=[]
                EARFCNs=[]
                for (var cellKey in points_cells) {
                    PCIS.push({ 'pcis': parseTuple(cellKey)[0][1], 'earfcn' : parseTuple(cellKey)[0][2]});
                }
                markerObject[marker._leaflet_id]["earfcngroup"][earfcnkey]={'object':{
                    'Title': numberId,
                    'PCIs': PCIS,
                    'MarkerId':marker._leaflet_id
                }}
            })		
    
        }	
    });
        
}

//---------------------------------------------------------------------
//process the PCI value for generating the code color
function colorNumber(val){
                    console.log(val);
    pci=parseInt(val,10);  // PCI is between 0 and 508, we consider it is coded on 9 bits and we split into 3 parts, each one over 3 bits

                    ValTestee = (pci%9)*57+ Math.trunc(pci/9)+ColorChoice;
                    if (ColorChoice!=0) {
                            ValTestee = (pci%3)*170+ Math.trunc(pci/3)+ColorChoice;
                            }
                    ValCouleur = 10+ValTestee*32895
                    Couleur = ValCouleur.toString(16);
                    console.log(Couleur);
            return Couleur
}
//---------------------------------------------------------------------
// this function creates the circle for the point measured
function drawcircle(item,rand,layer){
    circle=L.circle([item.geometry.coordinates[1],item.geometry.coordinates[0]], {radius:1,opacity: 1,
                                            color: '#'+rand,interactive:true}).addTo(layer)
    circle.bringToFront().bindPopup(item.property.toString());							
}