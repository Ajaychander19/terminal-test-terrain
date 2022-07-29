/**
 * Contains class and methods used to draw data on the Leaflet map.
 * 
 * @namespace
 */
const drawing = {

    /**
     * Wraps the map and the layer state to perform drawing and updating operations on them.
     * 
     * @class
     */
    Map: class {

        _map            // Leaflet Map

        _cellLayer      // Voronoi cell layer.
        _antLayer       // Antennas layer.
        _assocLayer     // Association pin layer.
        
        _tacLayer       // TAC points layer.
        _pciLayer       // PCI Points layer.
        
        _servingRSRP    // Serving RSRP layer
        _servingRSRQ    // Serving RSRQ layer
        _servingRSSI    // Serving RSSI layer
        _servingCINR    // Serving RSRP layer
        
        _rsrpLayer      // Global RSRP layer
        _rsrqLayer      // Global RSRQ layer
        _rssiLayer      // Global RSSI layer
        _cinrLayer      // Global RSRP layer

        _nonFilteredTAC
        _nonFilteredPCI


        /**
         * Class constructor.
         * 
         * @param {L.Map} map Leaflet map to wrap.
         * 
         * @constructor
         */
        constructor(map) {
            this._map = map;

            this._cellLayer = L.layerGroup();
            this._tacLayer = L.layerGroup();
            this._pciLayer = L.layerGroup();

            this._servingRSRP = drawing.hexBin('RSRP', styles.hexColor(0, 1));
            this._servingRSRQ = drawing.hexBin('RSRQ', styles.hexColor(0, 1));
            this._servingRSSI = drawing.hexBin('RSSI', styles.hexColor(0, 1));
            this._servingCINR = drawing.hexBin('CINR', styles.hexColor(0, 1));

            this._rsrpLayer = drawing.hexBin('RSRP', styles.hexColor(0, 1));
            this._rsrqLayer = drawing.hexBin('RSRQ', styles.hexColor(0, 1));
            this._rssiLayer = drawing.hexBin('RSSI', styles.hexColor(0, 1));
            // this._cinrLayer = drawing.hexBin('CINR', styles.hexColor(0, 1));

            this._assocLayer = L.layerGroup();

            this._nonFilteredTAC = null;
            this._nonFilteredPCI = null;

        }

        /**
         * Draws Voronoi cells, delimiters and antennas layers.
         * 
         * @param {*} voronoi Voronoi diagram GeoJSON
         * @param {*} antFeats Antennas directivity lines GeoJSON.
         * @param {*} delFeats Sectors delimiters GeoJSON.
         * 
         * @function
         */
        drawCells(voronoi, antFeats, delFeats) {

            this._cellLayer.clearLayers();

            // GeoJSON features of Voronoi cells.
            let vorFeats = voronoi.features;
            
            // Creating layers for Voronoi cells and delimiters.
            let vorLayer = L.geoJson(turf.featureCollection(vorFeats), styles.polyStyle(0.1, '000000'));
            let delLayer = L.geoJson(turf.featureCollection(delFeats), styles.styleDelimiter());
            delLayer.bringToBack();
            
            // Grouping these layers
            vorLayer.addTo(this._cellLayer);
            delLayer.addTo(this._cellLayer);

            // Antennas layer (always displayed by default).
            this._antLayer = L.geoJson(turf.featureCollection(antFeats), styles.styleAntenna());
    
        }

        /**
         * Draw serving points layer.
         * @param {*} points Points data
         * @param {function} valChooser Function that (earfcn, pci, point) => value which 
         * extracts the value from the point.
         * @param {function} colorChooser Function (value) => color which calculate the point color.
         * 
         * @returns Return an object containing multiple layers associated to EARFCNs / PCIs.
         * 
         * @function
         */
        drawPoints(points, valChooser, colorChooser) {

            // Dictionary which contains point layers associated to EARFCNs/PCIs.
            let pointDict = {};

            // For each EARFCNs found in points.
            for (let earfcn in points) {

                // Group of points with the same EARFCN.
                let earfcnGr = points[earfcn];

                // Adding EARFCN entry in dictionary if not already present.
                pointDict[earfcn] || (pointDict[earfcn] = {});

                // For each PCI associated to the EARFCN...
                for (let pci in earfcnGr) {

                    // Adding PCI entry if not exists.
                    pointDict[earfcn][pci] || (pointDict[earfcn][pci] = {})

                    // Values dictionary.
                    let points = {}

                    // For each point associated to these EARFCN and PCI...
                    earfcnGr[pci].forEach((point) => {

                        let latLng = [point.lat, point.lng];                // Latitude and longitude of the point.
                        let val = valChooser(earfcn, pci, point);           // Value to associate to the group of the current point.

                        // Creating the group if it does not exists.
                        points[val] || (points[val] = []);

                        // Adding point to the group...
                        points[val].push(latLng);
                        
                    });

                    // Creating layers from group of points.
                    for (let val in points) {

                        let layer = new L.GridLayer.MaskCanvas(styles.pointStyle(colorChooser(val)));
                        layer.setData(points[val]);

                        pointDict[earfcn][pci] = layer;

                    }

                }

            }

            return pointDict;

        }

        /**
         * Draws serving measurement heatmap layer.
         * 
         * @param {*} layer Layer to draw on.
         * @param {function} points Serving measurement points.
         * @param {function} valChooser Function that (earfcn, pci, point) => value which 
         * extracts the value from the point.
         * @param {number} min Minimum value (used for the color range).
         * @param {number} max Maximum value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         * 
         * @function
         */
        drawServingHex(layer, points, valChooser, min, max, earfcns=null, pcis=null) {

            // Layer data points;
            let hexData = [];

            // EARFCNs and PCIs amongs input points.
            let baseEarfncs = [];
            let basePcis = [];

            // Iterating over points EARFCNs...
            for (let earfcn in points) {

                let pciGroup = points[earfcn];

                // Over PCIs...
                for (let pci in pciGroup) {
                    baseEarfncs.push(parseInt(earfcn));
                    basePcis.push(parseInt(pci));
                }

            }

            // Filtering EARFCNs and PCIs...
            let earpcis = utils.subEarpci(baseEarfncs, basePcis, earfcns, pcis);
            let filtEarfcns = earpcis.earfcns;
            let filtPcis = earpcis.pcis;

            // For each reamining EARFCNs and PCIs...
            for (let i in filtEarfcns) {

                let earfcn = filtEarfcns[i];
                let pci = filtPcis[i];

                // Pushing asscoiated measurements in hexData...
                points[earfcn][pci].forEach(
                    (pt) => {
                        let val = valChooser(earfcn, pci, pt);
                        hexData.push([pt.lng, pt.lat, val]);
                    }
                );

            }

            // Drawing the layer.
            layer.options.colorScaleExtent = [min, max];
            layer.redraw();

            // Adding data...
            layer.data(hexData);

        }

        /**
         * Draws the pins of the associated pins.
         * 
         * @param {*} assocs Association data.
         * @param {*} antennas Antennas data;
         * @param {*} checkEarfcns Checked EARFCNs (in checkboxes).
         * @param {*} checkPcis Checked PCIs (in checkboxes).
         * @param {*} updateMethod Pins updating () => () function.
         * @param {Array} earfcns Selected EARFCNs (selector)
         * @param {Array} pcis Selected PCIs (selector).
         * 
         * @function
         */
        drawAssocs(assocs, antennas, checkEarfcns, checkPcis, updateMethod, earfcns=null, pcis=null) {

            this._assocLayer.clearLayers();

            for (let cartoNum in assocs) {

                let assoc = assocs[cartoNum];       // Association between current Cartoradio Num. and EARFCN / PCI.
                let ant = antennas[cartoNum];   // Associated antenna

                // Creating the marker object.
                let marker = L.marker([ant.lat, ant.lng], {icon: styles.stationIcon()});

                // Creating popup.
                marker.bindPopup(
                    this.drawAssocPopup(cartoNum, assoc, checkEarfcns, checkPcis, updateMethod, earfcns, pcis),
                    {closeOnClick: false, autoClose: false}
                );
                marker.addTo(this._assocLayer);

            }


        }

        /**
         * 
         * @param {number} cartoNum 
         * @param {*} assoc 
         * @param {*} checkEarfcns 
         * @param {*} checkPcis 
         * @param {*} updateMethod 
         * @param {*} earfcns 
         * @param {*} pcis 
         * @returns 
         */
        drawAssocPopup(cartoNum, assoc, checkEarfcns, checkPcis, updateMethod, earfcns=null, pcis=null) {

            // Content element of the popup.
            let popDiv = document.createElement('div');

            // Popup title.
            popDiv.innerHTML = '<span class="tooltip-title">' + cartoNum + '</span><br>';

            // Checkboxes container element.
            let checkDiv = document.createElement('div');
            checkDiv.classList.add('check-div');

            // Inserting checkboxes for each associated EARFCN / PCI...

            let ascEarfcns = assoc.map((asc) => asc.earfcn);
            let ascPcis = assoc.map((asc) => asc.pci);

            let earpcis = utils.subEarpci(ascEarfcns, ascPcis, earfcns, pcis);

            for (let i in earpcis.earfcns) {

                let earfcn = earpcis.earfcns[i];
                let pci = earpcis.pcis[i];

                // Checkbox element.
                let checkBox = document.createElement('input');
                checkBox.setAttribute('type', 'checkbox');
                
                // Identifying the checkbox.
                let checkId = 'check' + '-' + cartoNum + '-' + earfcn + '-' + pci;
                checkBox.id = checkId;

                // When clicking the checkbox...
                checkBox.onclick = (evt) => { 
                    
                    // ...adding corresponding EARFCN / PCI to checkEARFCN an checkPCI.
                    if (evt.target.checked) {
                        checkEarfcns.push(earfcn);
                        checkPcis.push(pci);
                    } else utils.removeEarpci(checkEarfcns, checkPcis, earfcn, pci);

                    updateMethod();

                };

                if (utils.indexOfEarpci(checkEarfcns, checkPcis, earfcn, pci) !== -1) checkBox.checked = true;

                // Label of the checkbox.
                let label = document.createElement('label');
                label.setAttribute('for', checkId);
                label.innerHTML = earfcn + ' - ' + pci;

                // Adding it to the checkboxes container div...
                checkDiv.append(...[
                    checkBox, label, document.createElement('br')
                ]);


            }

            popDiv.append(checkDiv);

            return popDiv;

        }

        setPointLayer(layer, pointLayers, earfcns=null, pcis=null) {

            // Check if tables have the same length.
            if (earfcns && pcis && earfcns.length !== pcis.length)
                throw new Error('earfncs and pcis should have the same length');
            
            // Clearing point layer.
            layer.clearLayers();

            // Getting layers which correspond to chosen EARFCNs.

            let earfcnLayers = {};
            if (earfcns) earfcns.forEach((earfcn) => earfcnLayers[earfcn] = pointLayers[earfcn]);
            else earfcnLayers = pointLayers;  // All EARFCNs otherwise.

            let layers = [];

            // For each groups of layers with the same EARFCN...
            for (let e in earfcnLayers) {

                    let earfcn = parseInt(e);

                    // Current group of layers with the same EARFCN / PCI.
                    let pciLayers = earfcnLayers[e];

                    // For each group of layer with the same EARFCN / PCI...
                    for (let p in pciLayers) {

                        let pci = parseInt(p);          // Current PCI.
                        let pciLayer = pciLayers[p];    // Layer associated to the PCI.
                        
                        if (pcis) {     // Chose PCIs of pcis param is not null.

                            // PCI indexes in pcis, used to get the associated EARFCN in earfcns param.
                            let pciIndexes = utils.indexesOf(pcis, pci);

                            // For each PCI index...
                            for (let pi in pciIndexes) {

                                let pciIndex = pciIndexes[pi];

                                // If current PCI corresponds to the current EARFCN, add to layers to show.
                                if (pciIndex !== -1 && ((earfcns && earfcn === earfcns[pciIndex]) || !earfcns)) 
                                    layers.push(pciLayer);
                            }

                        } else layers.push(pciLayer);   // Choose all PCIs otherwise...

                    }
                    
            }

            layers.forEach((l) => l.addTo(layer));

        }

        drawHex(layer, measurements, earfcns, pcis, min, max, reqEarfcns=null, reqPcis=null) {

            let hexData = [];

            let earpcis = utils.subEarpci(earfcns, pcis, reqEarfcns, reqPcis);

            // For each measurement taken...
            measurements.forEach(
                
                (measObj) => {

                    let meas = measObj.meas;

                    earpcis.indices.forEach(
                        (i) => {
                            let m = meas[i];
                            if (m) hexData.push([measObj.lng, measObj.lat, m]);
                        }
                    );

                }
            );

            layer.options.colorScaleExtent = [min, max];
            layer.redraw();
            layer.data(hexData);

        }

        drawTAC(points) { return this.drawPoints(points, (_e, _pc, p) => p.tac, styles.tacColor); }

        drawPCI(points, col=1) { return this.drawPoints(points, (_e, pc, _p) => pc, (p) => styles.pciColor(p, col)); }

        drawServingRSRP(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this._servingRSRP, points, (_e, _p, pt) => pt.rsrp,
                min, max, earfcns, pcis,
            );
        }

        drawServingRSRQ(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this._servingRSRQ, points, (_e, _p, pt) => pt.rsrq,
                min, max, earfcns, pcis
            );
        }

        drawServingRSSI(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this._servingRSSI, points, (_e, _p, pt) => pt.rssi,
                min, max, earfcns, pcis
            );
        }

        drawServingCINR(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this._servingCINR, points, (_e, _p, pt) => pt.cinr,
                min, max, earfcns, pcis
            );
        }

        drawRSRP(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this._rsrpLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }

        drawRSRQ(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this._rsrqLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }

        drawRSSI(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this._rssiLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }

        updateTACLayer(points, earfcn=null, pci=null) {
            this._nonFilteredTAC = this.drawTAC(points);
            this.setPointLayer(this._tacLayer, this._nonFilteredTAC, earfcn, pci); 
        }

        updatePCILayer(points, earfcn=null, pci=null, col=1) {
            this._nonFilteredPCI = this.drawPCI(points, col);
            this.setPointLayer(this._pciLayer, this._nonFilteredPCI, earfcn, pci); 
        }



        setCellLayer(b) { this._setLayerVisibility(this._cellLayer, b); }

        setAntLayer(b) { this._setLayerVisibility(this._antLayer, b); }

        setTACLayer(b) { this._setLayerVisibility(this._tacLayer, b); }

        setPCILayer(b) { this._setLayerVisibility(this._pciLayer, b); }

        setAssocLayer(b) { this._setLayerVisibility(this._assocLayer, b); }

        setServingRSRP(b) { this._setLayerVisibility(this._servingRSRP, b); }

        setServingRSRQ(b) { this._setLayerVisibility(this._servingRSRQ, b); }

        setServingRSSI(b) { this._setLayerVisibility(this._servingRSSI, b); }

        setServingCINR(b) { this._setLayerVisibility(this._servingCINR, b); }

        setRSRP(b) { this._setLayerVisibility(this._rsrpLayer, b); }

        setRSRQ(b) { this._setLayerVisibility(this._rsrqLayer, b); }

        setRSSI(b) { this._setLayerVisibility(this._rssiLayer, b); }

        // setCINR(b) { this._setLayerVisibility(this._cinrLayer, b); }

        _setLayerVisibility(layer, b) {
            if (b && !this._map.hasLayer(layer)) layer.addTo(this._map);
            else if (!b && this._map.hasLayer(layer)) layer.removeFrom(this._map);
        }

        drawSelectors(earfcns, pcis) {


            let pciSelector = document.querySelector('#pci-select');
            let earSelector = document.querySelector('#EARFCN_select');

            earSelector.innerHTML = '<option value="serving-earfcn">Serving EARFCN</option>'
                + '<option value="all-earfcns">All EARFCNs</option>';
            pciSelector.innerHTML = '<option value="serving-pci">Serving PCI</option>'
                + '<option value="all-pcis">All PCIs</option>';

            let order = (a, b) => {
                
                let numA = parseInt(a);
                let numB = parseInt(b);

                if (a === b) return 0;
                else if (a < b) return -1;
                else return 1;

            }

            earfcns.sort(order).forEach(
                (earfcn) => {

                    if (!document.querySelector('#EARFCN_select option[value="' + earfcn + '"]')) {
                    
                        let option = document.createElement('option');
                        option.setAttribute('value', earfcn);
                        option.innerHTML = earfcn;
                        earSelector.append(option);

                    }

                }
            );

            pcis.sort(order).forEach(
                (pci) => {

                    if (!document.querySelector('#pci-select option[value="' + pci + '"]')) {
                    
                        let option = document.createElement('option');
                        option.setAttribute('value', pci);
                        option.innerHTML = pci;
                        pciSelector.append(option);

                    }

                }
            )

        }

    },

    hexBin: function (tooltip, options) {

        let hex = L.hexbinLayer(options);

        let minFunct = function (d) {
            let tempArray = d.map((i) => i.o[2]);
            return Math.min.apply(null, tempArray);
        }

        hex._fn.colorValue = minFunct;

        hex.hoverHandler(
            L.HexbinHoverHandler.tooltip({
                tooltipContent: (d) => tooltip + ': ' + minFunct(d)
            })
        );

        return hex;

    }

}