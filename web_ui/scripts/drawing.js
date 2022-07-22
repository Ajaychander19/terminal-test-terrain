const drawing = {

    Map: class {

        #map
        #cellLayer
        #antLayer
        #assocLayer
        
        #tacLayer
        #pciLayer
        
        #servingRSRP
        #servingRSRQ
        #servingRSSI
        #servingCINR
        
        // #rsrpLayer
        // #rsrqLayer
        // #rssiLayer
        // #cinrLayer

        #nonFilteredTAC
        #nonFilteredPCI


        constructor(map) {
            this.#map = map;

            this.#cellLayer = L.layerGroup();
            this.#tacLayer = L.layerGroup();
            this.#pciLayer = L.layerGroup();

            this.#servingRSRP = L.layerGroup();
            this.#servingRSRQ = L.layerGroup();
            this.#servingRSSI = L.layerGroup();
            this.#servingCINR = L.layerGroup();

            this.#nonFilteredTAC = null;
            this.#nonFilteredPCI = null;
        }

        drawCells(voronoi, antFeats, delFeats) {

            // GeoJSON features of Voronoi cells.
            let vorFeats = voronoi.features;
            
            // Creating layers for Voronoi cells and delimiters.
            let vorLayer = L.geoJson(turf.featureCollection(vorFeats), styles.polyStyle(0.1, '000000'));
            let delLayer = L.geoJson(turf.featureCollection(delFeats), styles.STYLE_DELIMITER);
            delLayer.bringToBack();
            
            // Grouping these layers
            vorLayer.addTo(this.#cellLayer);
            delLayer.addTo(this.#cellLayer);

            // Antennas layer (always displayed by default).
            this.#antLayer = L.geoJson(turf.featureCollection(antFeats), styles.STYLE_ANTENNA);
    
        }

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

        drawServingHex(layer, points, valChooser, earfcns, pcis) {

            let hexData = [];

            // Getting EARFCN groups matching with earfcns parameter.

            let earfcnGroups = {};

            if (earfcns) earfcns.forEach((earfcn) => earfcnGroups[earfcn] = points[earfcn]);
            else earfcnGroups = points;

            // For each point group with the same EARFCN...
            for (let e in earfcnGroups) {

                let earfcn = parseInt(e);

                // Current groups of points with the same EARFCN / PCI.
                let pciGroups = earfcnGroups[e];

                for (let p in pciGroups) {

                    let pci = parseInt(p);
                    let pciGroup = pciGroups[pci];

                    let pushToHex = () => hexData.push(...(pciGroup.map((pt) => [pt.lng, pt.lat, valChooser(earfcn, pci, pt)])));

                    if (pcis) { // Getting matching PCIs if pcis is not null.

                        let pciIndexes = utils.indexesOf(pcis, pci);

                        for (let pi in pciIndexes) {

                            let pciIndex = pciIndexes[pi];

                            // If current PCI corresponds to the current EARFCN, add to points to data.
                            if (pciIndex !== -1 && ((earfcns && earfcn === earfcns[pciIndex]) || !earfcns))
                                pushToHex();

                        }

                    } else pushToHex();

                }

            }

            let values = hexData.map((h) => h[2]);

            layer.options.colorScaleExtent = [
                Math.min(...values), Math.max(...values)
            ];

            layer.redraw();

            layer.data(hexData);

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

        drawHex(measurements, earfcns, pcis, tooltip) {

            let result = {};

            // Min and max measurements.
            let minMeas = null;
            let maxMeas = null;

            // For each measurement taken...
            measurements.forEach(
                
                (measObj) => {

                    let meas = measObj.meas;

                    // For each measurement value...
                    for (let i in meas) {

                        let m = meas[i];            // Measurement value.
                        let earfcn = earfcns[i];    // Associated EARFCn.
                        let pci = pcis[i];          // Associated PCI.

                        // Initializing minMeas and maxMeas if not.
                        minMeas || (minMeas = m);
                        maxMeas || (maxMeas = m);

                        // Updating minMeas and maxMeas if necessary.
                        if (minMeas > m) minMeas = m;
                        if (maxMeas < m) maxMeas = m;

                        // Defining resutl[earfcn][pci] if not defined.
                        result[earfcn] || (result[earfcn] = {});
                        result[earfcn][pci] || (result[earfcn][pci] = []);

                        // Adding (lat, lng, measurement value).
                        if (m) result[earfcn][pci].push([measObj.lng, measObj.lat, m]);

                    }

                }
            )

            // Creating hexbinLayers in-place.
            for (let earfcn in result) {

                for (let pci in result[earfcn]) {

                    let hexLayer = drawing.hexBin(tooltip, styles.hexColor(minMeas, maxMeas));
                    hexLayer.data(result[earfcn][pci]);
                    result[earfcn][pci] = hexLayer;

                }

            }

            return result;

        }

        drawTAC(points) { return this.drawPoints(points, (_e, _pc, p) => p.tac, styles.tacColor); }

        drawPCI(points) { return this.drawPoints(points, (_e, pc, _p) => pc, (p) => styles.pciColor(p, 1)); }

        updateTACLayer(points, earfcn=null, pci=null) {
            this.#nonFilteredTAC || (this.#nonFilteredTAC = this.drawTAC(points));
            this.setPointLayer(this.#tacLayer, this.#nonFilteredTAC, earfcn, pci); 
        }

        updatePCILayer(points, earfcn=null, pci=null) {
            this.#nonFilteredPCI || (this.#nonFilteredPCI = this.drawPCI(points));
            this.setPointLayer(this.#pciLayer, this.#nonFilteredPCI, earfcn, pci); 
        }

        setCellLayer(b) { this.#setLayerVisibility(this.#cellLayer, b); }

        setAntLayer(b) { this.#setLayerVisibility(this.#antLayer, b); }

        setTACLayer(b) { this.#setLayerVisibility(this.#tacLayer, b); }

        setPCILayer(b) { this.#setLayerVisibility(this.#pciLayer, b); }

        #setLayerVisibility(layer, b) {
            if (b && !this.#map.hasLayer(layer)) layer.addTo(this.#map);
            else if (!b && this.#map.hasLayer(layer)) layer.removeFrom(this.#map);
        }

    },

    hexBin: function(tooltip, options) {

        let hex = L.hexbinLayer(options);

        let minFunct = function (d) {
            let tempArray = d.map((i) => i.o[2]);
            return Math.min.apply(null, tempArray);
        }

        hex._fn.colorValue = minFunct

        hex.hoverHandler(
            L.HexbinHoverHandler.tooltip({
                tooltipContent: (d) => tooltip + ': ' + minFunct(d)
            })
        )

        return hex;

    }

}