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
            let pointDict = {};
            for (let earfcn in points) {
                pointDict[earfcn] = {};
                let earfcnGr = points[earfcn];
                for (let pci in earfcnGr) {
                    pointDict[earfcn][pci] = {};
                    let pciGr = earfcnGr[pci];
                    for (let beam in pciGr) {
                        let pointsDict = {};
                        let pointsArr = pciGr[beam];
                        pointsArr.forEach((point) => {
                            let latLng = [point.lat, point.lng];
                            let val = valChooser(earfcn, pci, point);
                            pointsDict[val] = pointsDict[val] || [];
                            pointsDict[val].push(latLng);
                        });
                        for (let val in pointsDict) {
                            let layer = new L.GridLayer.MaskCanvas(styles.pointStyle(colorChooser(val)));
                            layer.setData(pointsDict[val]);
                            pointDict[earfcn][pci][beam] = layer;
                        }
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
        drawServingHex(layer, points, valChooser, min, max, earfcns = null, pcis = null, beams = null) {
            // Layer data points;
            let hexData = [];
            // EARFCNs and PCIs amongs input points.
            let baseEarfncs = [];
            let basePcis = [];
            let baseBeams = [];
            // Iterating over points EARFCNs...
            for (let earfcn in points) {
                let pciGroup = points[earfcn];
                // Over PCIs...
                for (let pci in pciGroup) {
                    let beamGroup = points[earfcn][pci];
                    for (let beam in beamGroup) {
                        baseEarfncs.push(parseInt(earfcn));
                        basePcis.push(parseInt(pci));
                        baseBeams.push(parseInt(beam));
                    }
                }
            }
            // Filtering EARFCNs and PCIs...
            let earpcis = utils.subEarpci(baseEarfncs, basePcis, baseBeams, earfcns, pcis);
            let filtEarfcns = earpcis.earfcns;
            let filtPcis = earpcis.pcis;
            let filtBeams = earpcis.beams;
            // For each reamining EARFCNs and PCIs...
            for (let i in filtEarfcns) {
                let earfcn = filtEarfcns[i];
                let pci = filtPcis[i];
                let beamList = filtBeams[pci];
                if (beams[pci]) {
                    // Pushing asscoiated measurements in hexData...
                    for (let b in beamList) {
                        // if all beams are selected then add all points for each beam in the list
                        if (beams[pci].includes("all")) {
                            points[earfcn][pci][b].forEach(
                                (pt) => {
                                    let val = valChooser(earfcn, pci, pt);
                                    hexData.push([pt.lng, pt.lat, val]);
                                }
                            );
                        }
                        // if the beam 'b' is selected then add all points of beam 'b'
                        else if (beams[pci].includes(b)) {
                            points[earfcn][pci][b].forEach(
                                (pt) => {
                                    let val = valChooser(earfcn, pci, pt);
                                    hexData.push([pt.lng, pt.lat, val]);
                                }
                            );
                        }
                    }
                } else {
                    // if no beams are selected then add all the existing measurements for an EARFCN/PCI couple
                    for (var e = 0; e < beamList.length; e++) {
                        var be = beamList[e];
                        if (!isNaN(be)) {
                            if (points[earfcn][pci][be]) {
                                points[earfcn][pci][be].forEach(
                                    (pt) => {
                                        let val = valChooser(earfcn, pci, pt);
                                        hexData.push([pt.lng, pt.lat, val]);
                                    }
                                );
                            }
                        }
                    }
                }
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
        drawAssocs(assocs, antennas, checkEarfcns, checkPcis, checkBeams, updateMethod, earfcns = null, pcis = null, beams = null) {
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
        drawAssocPopup(cartoNum, assoc, checkEarfcns, checkPcis, checkBeams, updateMethod, earfcns = null, pcis = null, beams = null) {
            // Content element of the popup.
            let popDiv = document.createElement('div');
            // Popup title.
            popDiv.innerHTML = '<span class="tooltip-title">' + '<a href=\"https://www.cartoradio.fr\">' + cartoNum + '</a></span><br>';
            // Checkboxes container element.
            let checkDiv = document.createElement('div');
            checkDiv.classList.add('check-div');
            // Inserting checkboxes for each associated EARFCN / PCI...
            let ascEarfcns = assoc.map((asc) => asc.earfcn);
            let ascPcis = assoc.map((asc) => asc.pci);
            let earpcis = utils.subEarpci(ascEarfcns, ascPcis, beams, earfcns, pcis);
            for (let i in earpcis.earfcns) {
                let earfcn = earpcis.earfcns[i];
                let pci = earpcis.pcis[i];
                checkBeams[pci] = ["all"];
                let bs;
                let beam;
                let select_beams;
                if (pcis != null && earfcns != null) {
                    let current_beams = beams[pci].sort();
                    current_beams = current_beams.filter((item, index) => current_beams.indexOf(item) === index);
                    select_beams = document.createElement('select');
                    select_beams.text = 'Select Beams';
                    //all beams default
                    let option = document.createElement('option');
                    option.text = "All beams";
                    option.value = "all";
                    select_beams.add(option);
                    for (var j = 0; j < current_beams.length; j++) {
                        let option = document.createElement('option');
                        option.text = current_beams[j];
                        option.value = current_beams[j];
                        select_beams.add(option);
                    }
                    select_beams.addEventListener('change', function () {
                        checkBeams[pci].pop();
                        let selectedValue = select_beams.value;
                        checkBeams[pci].push(selectedValue);
                        updateMethod();
                    });
                }
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
                label.innerHTML = earfcn + ' - ' + pci /*+ beam*/;
                // Adding it to the checkboxes container div...
                checkDiv.append(...[
                    checkBox, label, select_beams, document.createElement('br')
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
        setPointLayer(layer, pointLayers, earfcns = null, pcis = null, beams = null) {
            if (earfcns && pcis && earfcns.length !== pcis.length)
                throw new Error('earfncs and pcis should have the same length');
            layer.clearLayers();
            const earfcnLayers = earfcns ? earfcns.reduce((obj, earfcn) => {
                obj[earfcn] = pointLayers[earfcn];
                return obj;
            }, {}) : {...pointLayers};
            const layers = [];
            for (const earfcn in earfcnLayers) {
                const earfcnInt = parseInt(earfcn);
                const pciLayers = earfcnLayers[earfcn];
                for (const pci in pciLayers) {
                    const pciInt = parseInt(pci);
                    const beamsLayers = pciLayers[pci];
                    if (pcis) {
                        const pciIndexes = utils.indexesOf(pcis, pciInt);
                        pciIndexes.forEach((pciIndex) => {
                            if (
                                pciIndex !== -1 &&
                                ((earfcns && earfcnInt === earfcns[pciIndex]) || !earfcns)
                            ) {
                                for (const beam in beamsLayers) {
                                    const beamLayer = beamsLayers[beam];
                                    if (beams[pciInt]) {
                                        if (beams[pciInt].includes("all")) {
                                            layers.push(beamLayer);
                                        } else {
                                            const beamIndexes = utils.indexesOf(beams[pciInt], beam);
                                            beamIndexes.forEach((beamIndex) => {
                                                if (beamIndex !== -1) {
                                                    layers.push(beamLayer);
                                                }
                                            });
                                        }
                                    } else {
                                        layers.push(beamLayer);
                                    }
                                }
                            }
                        });
                    } else {
                        for (const beam in beamsLayers) {
                            const beamLayer = beamsLayers[beam];
                            layers.push(beamLayer);
                        }
                    }
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
        drawHex(layer, measurements, earfcns, pcis, beams, min, max, reqEarfcns = null, reqPcis = null, reqBeams = null) {
            let hexData = [];

            // all measurements requested by EARFCNs/PCIs/BEAMs
            let earpcis = utils.subEarpci(earfcns, pcis, beams, reqEarfcns, reqPcis, reqBeams);

            // For each measurement object in the list (corresponds to a line 'MEASUREMENT')
            measurements.forEach(
                (measObj) => {
                    let meas = measObj.meas;
                    // indexes of selected measurements at the same timestamp
                    earpcis.indices.forEach(
                        (i) => {
                            let m = meas[i];
                            if (m) {
                                hexData.push([measObj.lng, measObj.lat, m]);
                            }
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
        drawTAC(points) {
            return this.drawPoints(points, (_e, _pc, p) => p.tac, styles.tacColor);
        }
        /**
         * Draw the PCI layer from serving points data.
         * @param {*} points Serving points data.
         * @returns Return an object containing multiple PCI points layers associated to EARFCNs / PCIs.
         *
         * @function
         */
        drawPCI(points, col = 1) {
            return this.drawPoints(points, (_e, pc, _p) => pc, (p) => styles.pciColor(p, col));
        }
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
        drawServingRSRP(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingRSRP, points, (_e, _p, pt) => pt.rsrp,
                min, max, earfcns, pcis, beams,
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
        drawServingRSRQ(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingRSRQ, points, (_e, _p, pt) => pt.rsrq,
                min, max, earfcns, pcis, beams
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
        drawServingRSSI(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingRSSI, points, (_e, _p, pt) => pt.rssi,
                min, max, earfcns, pcis, beams
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
        drawServingCINR(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingCINR, points, (_e, _p, pt) => pt.cinr,
                min, max, earfcns, pcis, beams
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
        drawRSRP(measurements, earfcns, pcis, beams, min, max, subEarfcns = null, subPcis = null, subBeams = null) {
            this.drawHex(this._rsrpLayer, measurements, earfcns, pcis, beams, min, max, subEarfcns, subPcis, subBeams);
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
        drawRSRQ(measurements, earfcns, pcis, beams, min, max, subEarfcns = null, subPcis = null, subBeams = null) {
            this.drawHex(this._rsrqLayer, measurements, earfcns, pcis, beams, min, max, subEarfcns, subPcis, subBeams);
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
        drawRSSI(measurements, earfcns, pcis, beams, min, max, subEarfcns = null, subPcis = null, subBeams = null) {
            this.drawHex(this._rssiLayer, measurements, earfcns, pcis, beams, min, max, subEarfcns, subPcis, subBeams);
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
        updateTACLayer(points, earfcn = null, pci = null, beam = null) {
            this._nonFilteredTAC = this.drawTAC(points);
            this.setPointLayer(this._tacLayer, this._nonFilteredTAC, earfcn, pci, beam);
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
        updatePCILayer(points, earfcn = null, pci = null, beam = null, col = 1) {
            this._nonFilteredPCI = this.drawPCI(points, col);
            this.setPointLayer(this._pciLayer, this._nonFilteredPCI, earfcn, pci, beam);
        }
        /**
         * Sets Voronoi cells layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setCellLayer(b) {
            this._setLayerVisibility(this._cellLayer, b);
        }
        /**
         * Sets antennas layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setAntLayer(b) {
            this._setLayerVisibility(this._antLayer, b);
        }
        /**
         * Sets TAC layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setTACLayer(b) {
            this._setLayerVisibility(this._tacLayer, b);
        }
        /**
         * Sets PCI layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setPCILayer(b) {
            this._setLayerVisibility(this._pciLayer, b);
        }
        /**
         * Sets association layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setAssocLayer(b) {
            this._setLayerVisibility(this._assocLayer, b);
        }
        /**
         * Sets serving RSRP layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setServingRSRP(b) {
            this._setLayerVisibility(this._servingRSRP, b);
        }
        /**
         * Sets serving RSRQ layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setServingRSRQ(b) {
            this._setLayerVisibility(this._servingRSRQ, b);
        }
        /**
         * Sets serving RSSI layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setServingRSSI(b) {
            this._setLayerVisibility(this._servingRSSI, b);
        }
        /**
         * Sets serving CINR layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setServingCINR(b) {
            this._setLayerVisibility(this._servingCINR, b);
        }
        /**
         * Sets global RSRP layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setRSRP(b) {
            this._setLayerVisibility(this._rsrpLayer, b);
        }
        /**
         * Sets global RSRQ layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setRSRQ(b) {
            this._setLayerVisibility(this._rsrqLayer, b);
        }
        /**
         * Sets global RSSI layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setRSSI(b) {
            this._setLayerVisibility(this._rssiLayer, b);
        }
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