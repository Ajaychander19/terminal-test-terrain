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
            let earpcis = utils.subEarpci(baseEarfncs, basePcis, null, earfcns, pcis, null);
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
         * @param {*} checkEarfcns Checked EARFCNs (in checkboxes) array.
         * @param {*} checkPcis Checked PCIs (in checkboxes) array.
         * @param {*} updateMethod Pins updating () => () function.
         * @param {Array} earfcns Selected EARFCNs.
         * @param {Array} pcis Selected PCIs.
         * 
         * @function
         */
        drawAssocs(assocs, antennas, checkEarfcns, checkPcis, checkBeams, updateMethod, earfcns=null, pcis=null, beams=null) {

            this._assocLayer.clearLayers();

            for (let cartoNum in assocs) {

                let assoc = assocs[cartoNum];    // Association between current Cartoradio Num. and EARFCN / PCI.
                let ant = antennas[cartoNum];   // Associated antenna

                // Creating the marker object.
                let marker = L.marker([ant.lat, ant.lng], {icon: styles.stationIcon()});

                // Creating popup.
                marker.bindPopup(
                    this.drawAssocPopup(cartoNum, assoc, checkEarfcns, checkPcis, checkBeams, updateMethod, earfcns, pcis, beams),
                    {closeOnClick: false, autoClose: false}
                );
                marker.addTo(this._assocLayer);

            }


        }

        /**
         * Draw the popup of an associated site.
         * 
         * @param {number} cartoNum Cartoradio number of the site.
         * @param {*} assoc Association data.
         * @param {Array} checkEarfcns List of EARFCNs selected using checkboxes.
         * @param {function} checkPcis List of PCIs selected using checkboxes.
         * @param {function} updateMethod Layer update method.
         * @param {Array} earfcns Selected EARFCNs.
         * @param {Array} pcis  Selected PCIs.
         * @returns The div element of the popup.
         * 
         * @function
         */
        drawAssocPopup(cartoNum, assoc, checkEarfcns, checkPcis, checkBeams=null, updateMethod, earfcns=null, pcis=null, beams=null) {
            let bs;
            for ( var i = 0; i < beams.length; i++){
                bs += '<option value=' + beams[i] + '>'+ beams[i] + '</option>';
            }

            let beam = '<select class="form-control selectpicker" id="beam_select">'
            + '<option value="all-beams">All BEAMs</option>'
            + bs;
            '</select>';

            //let beamSelector = document.querySelector('#beam_select');
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
            let ascBeams = null;
            /*if (checkBeams){

                ascBeams = assoc.map((asc) => asc.beam);

            }*/
            let earpcis = utils.subEarpci(ascEarfcns, ascPcis, null, earfcns, pcis, null);
            //let earpcis = utils.subEarpci(ascEarfcns, ascPcis, ascBeams, earfcns, pcis, beams);
            for (let i in earpcis.earfcns) {
                let earfcn = earpcis.earfcns[i];
                let pci = earpcis.pcis[i];
                //let beam = earpcis.beams[i];
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
                label.innerHTML = earfcn + ' - ' + pci + beam;
                // Adding it to the checkboxes container div...
                checkDiv.append(...[
                    checkBox, label, document.createElement('br')
                ]);
            }
            popDiv.append(checkDiv);
            return popDiv;

        }

        /**
         * Write serving points on a group layer.
         * @param {*} layer Leaflet group layer.
         * @param {*} pointLayers Dictionary of points layers, classed by EARFCN / PCI.
         * @param {*} earfcns Selected EARFCNs.
         * @param {*} pcis  Selected PCIs.
         * 
         * @function
         */
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

        /**
         * Draws a global measurements heatmap layer.
         * @param {*} layer Layer to draw on.
         * @param {*} measurements Global measurement data.
         * @param {Array} earfcns EARFCNs for list of (EARFCN, PCI) pairs.
         * @param {Array} pcis PCIs for list of (EARFCN, PCI) pairs.
         * @param {number} min Minimum value.
         * @param {number} max Maximum value.
         * @param {Array} reqEarfcns Selected EARFCNs
         * @param {Array} reqPcis Selected PCIs.
         * 
         * @function
         */
        drawHex(layer, measurements, earfcns, pcis, min, max, reqEarfcns=null, reqPcis=null) {

            let hexData = [];

            let earpcis = utils.subEarpci(earfcns, pcis, null, reqEarfcns, reqPcis, null);

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

        /**
         * Draw the TAC layer from serving points data.
         * @param {*} points Serving points data.
         * @returns Return an object containing multiple TAC points layers associated to EARFCNs / PCIs.
         * 
         * @function
         */
        drawTAC(points) { return this.drawPoints(points, (_e, _pc, p) => p.tac, styles.tacColor); }

        /**
         * Draw the PCI layer from serving points data.
         * @param {*} points Serving points data.
         * @returns Return an object containing multiple PCI points layers associated to EARFCNs / PCIs.
         * 
         * @function
         */
        drawPCI(points, col=1) { return this.drawPoints(points, (_e, pc, _p) => pc, (p) => styles.pciColor(p, col)); }

        /**
         * Draws the serving RSRP layer.
         * @param {function} points Serving measurement points.
         * @param {number} min Minimum RSRP value (used for the color range).
         * @param {number} max Maximum RSRP value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         * 
         * @function
         */
        drawServingRSRP(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this._servingRSRP, points, (_e, _p, pt) => pt.rsrp,
                min, max, earfcns, pcis,
            );
        }

        /**
         * Draws the serving RSRQ layer.
         * @param {function} points Serving measurement points.
         * @param {number} min Minimum RSRQ value (used for the color range).
         * @param {number} max Maximum RSRQ value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         * 
         * @function
         */
        drawServingRSRQ(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this._servingRSRQ, points, (_e, _p, pt) => pt.rsrq,
                min, max, earfcns, pcis
            );
        }


        /**
         * Draws the serving RSSI layer.
         * @param {function} points Serving measurement points.
         * @param {number} min Minimum RSSI value (used for the color range).
         * @param {number} max Maximum RSSI value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         * 
         * @function
         */
        drawServingRSSI(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this._servingRSSI, points, (_e, _p, pt) => pt.rssi,
                min, max, earfcns, pcis
            );
        }

        /**
         * Draws the serving CINR layer.
         * @param {function} points Serving measurement points.
         * @param {number} min Minimum CINR value (used for the color range).
         * @param {number} max Maximum CINR value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         * 
         * @function
         */
        drawServingCINR(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this._servingCINR, points, (_e, _p, pt) => pt.cinr,
                min, max, earfcns, pcis
            );
        }

        /**
         * Draws the global RSRP layer.
         * 
         * @param {*} measurements Global RSRP measurement data.
         * @param {Array} earfcns EARFCNs for list of (EARFCN, PCI) pairs.
         * @param {Array} pcis PCIs for list of (EARFCN, PCI) pairs.
         * @param {number} min Minimum RSRP value.
         * @param {number} max Maximum RSRP value.
         * @param {Array} reqEarfcns Selected EARFCNs
         * @param {Array} reqPcis Selected PCIs.
         * 
         * @function
         */
        drawRSRP(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this._rsrpLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }

        /**
         * Draws the global RSRQ layer.
         * 
         * @param {*} measurements Global RSRQ measurement data.
         * @param {Array} earfcns EARFCNs for list of (EARFCN, PCI) pairs.
         * @param {Array} pcis PCIs for list of (EARFCN, PCI) pairs.
         * @param {number} min Minimum RSRQ value.
         * @param {number} max Maximum RSRQ value.
         * @param {Array} reqEarfcns Selected EARFCNs
         * @param {Array} reqPcis Selected PCIs.
         * 
         * @function
         */
        drawRSRQ(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this._rsrqLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }

        /**
         * Draws the global RSSI layer.
         * 
         * @param {*} measurements Global RSSI measurement data.
         * @param {Array} earfcns EARFCNs for list of (EARFCN, PCI) pairs.
         * @param {Array} pcis PCIs for list of (EARFCN, PCI) pairs.
         * @param {number} min Minimum RSSI value.
         * @param {number} max Maximum RSSI value.
         * @param {Array} reqEarfcns Selected EARFCNs
         * @param {Array} reqPcis Selected PCIs.
         * 
         * @function
         */
        drawRSSI(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this._rssiLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }
        
        /**
         * Updates the TAC layer.
         * 
         * @param {*} points Serving points data.
         * @param {Array} earfcn Selected EARFCNs.
         * @param {Array} pci  Selected PCIs.
         * 
         * @function
         */
        updateTACLayer(points, earfcn=null, pci=null) {
            this._nonFilteredTAC = this.drawTAC(points);
            this.setPointLayer(this._tacLayer, this._nonFilteredTAC, earfcn, pci); 
        }

        /**
         * Updates the PCI layer.
         * 
         * @param {*} points Serving points data.
         * @param {Array} earfcn Selected EARFCNs.
         * @param {Array} pci  Selected PCIs.
         * 
         * @function
         */
        updatePCILayer(points, earfcn=null, pci=null, col=1) {
            this._nonFilteredPCI = this.drawPCI(points, col);
            this.setPointLayer(this._pciLayer, this._nonFilteredPCI, earfcn, pci); 
        }


        /**
         * Sets Voronoi cells layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setCellLayer(b) { this._setLayerVisibility(this._cellLayer, b); }

        /**
         * Sets antennas layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setAntLayer(b) { this._setLayerVisibility(this._antLayer, b); }

        /**
         * Sets TAC layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setTACLayer(b) { this._setLayerVisibility(this._tacLayer, b); }

        /**
         * Sets PCI layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setPCILayer(b) { this._setLayerVisibility(this._pciLayer, b); }

        /**
         * Sets association layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setAssocLayer(b) { this._setLayerVisibility(this._assocLayer, b); }

        /**
         * Sets serving RSRP layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setServingRSRP(b) { this._setLayerVisibility(this._servingRSRP, b); }

        /**
         * Sets serving RSRQ layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setServingRSRQ(b) { this._setLayerVisibility(this._servingRSRQ, b); }

        /**
         * Sets serving RSSI layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setServingRSSI(b) { this._setLayerVisibility(this._servingRSSI, b); }

        /**
         * Sets serving CINR layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setServingCINR(b) { this._setLayerVisibility(this._servingCINR, b); }

        /**
         * Sets global RSRP layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setRSRP(b) { this._setLayerVisibility(this._rsrpLayer, b); }

        /**
         * Sets global RSRQ layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setRSRQ(b) { this._setLayerVisibility(this._rsrqLayer, b); }

        /**
         * Sets global RSSI layer visibility.
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         */
        setRSSI(b) { this._setLayerVisibility(this._rssiLayer, b); }

        // setCINR(b) { this._setLayerVisibility(this._cinrLayer, b); }


        /**
         * Sets the visibility of a layer.
         * @param {*} layer Layer. 
         * @param {boolean} b true to set the layer visible.
         * 
         * @function
         * @private
         */
        _setLayerVisibility(layer, b) {
            if (b && !this._map.hasLayer(layer)) layer.addTo(this._map);
            else if (!b && this._map.hasLayer(layer)) layer.removeFrom(this._map);
        }

        /**
         * Draws EARFCNs / PCIs selectors.
         * @param {Array} earfcns EARFCNs from (EARFCN, PCI) layer list.
         * @param {Array} pcis PCIs from (EARFCN, PCI) layer list.
         * 
         * @function
         */
        drawSelectors(earfcns, pcis) {

            // Getting selector elements.
            let pciSelector = document.querySelector('#pci-select');
            let earSelector = document.querySelector('#EARFCN_select');

            // Adding "Serving" and "All" options.
            earSelector.innerHTML = '<option value="serving-earfcn">Serving EARFCN</option>'
                + '<option value="all-earfcns">All EARFCNs</option>';
            pciSelector.innerHTML = '<option value="serving-pci">Serving PCI</option>'
                + '<option value="all-pcis">All PCIs</option>';

            // Order relation used to sort EARFCNs and PCIs numbers.
            let order = (a, b) => {
                
                let numA = parseInt(a);
                let numB = parseInt(b);

                if (numA === numB) return 0;
                else if (numA < numB) return -1;
                else return 1;

            }

            // Adding EARFCNs options.
            earfcns.sort(order).forEach(
                (earfcn) => {

                    // Selector used to ensure we add only once time the same option.
                    if (!document.querySelector('#EARFCN_select option[value="' + earfcn + '"]')) {
                    
                        // Creating option element.
                        let option = document.createElement('option');
                        option.setAttribute('value', earfcn);
                        option.innerHTML = earfcn;

                        // Adding it.
                        earSelector.append(option);

                    }

                }
            );

            // Adding PCIs options.
            pcis.sort(order).forEach(
                (pci) => {

                    if (!document.querySelector('#pci-select option[value="' + pci + '"]')) {
                    
                        let option = document.createElement('option');
                        option.setAttribute('value', pci);
                        option.innerHTML = pci;
                        pciSelector.append(option);

                    }

                }
            );

        }

    },

    /**
     * Creates an heatmap layer, with a custom tooltip displayable while hovering the layer.
     * Hexagons on the heatmap represents the minimum data point over this hexagon.
     * 
     * @param {String} tooltip Hover tooltip text.
     * @param {*} options Style of the layer.
     * 
     * @returns The new hex layer.
     * 
     * @function
     */
    hexBin: function (tooltip, options) {

        // Creating the layer with style.
        let hex = L.hexbinLayer(options);

        // Minimum point selection function.
        let minFunct = function (d) {
            let tempArray = d.map((i) => i.o[2]);
            return Math.min.apply(null, tempArray);
        }

        hex._fn.colorValue = minFunct;

        // Handler used to show the tooltip.
        hex.hoverHandler(
            L.HexbinHoverHandler.tooltip({
                tooltipContent: (d) => tooltip + ': ' + minFunct(d)
            })
        );

        return hex;

    }

}