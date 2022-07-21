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

        drawServingHex(points, valChooser) {



        }

        setPointLayer(layer, pointLayers, earfcns=null, pcis=null) {

            if (earfcns && pcis && earfcns.length !== pcis.length)
                throw new Error('earfncs and pcis should have the same length');
            
            layer.clearLayers();

            let earfcnLayers = {};
            if (earfcns) {
                for (let e in earfcns) {
                    let earfcn = earfcns[e];
                    earfcnLayers[earfcn] = pointLayers[earfcn];
                }
            } else earfcnLayers = pointLayers;

            let layers = [];

            for (let e in earfcnLayers) {

                    let earfcn = parseInt(e);
                    let pciLayers = earfcnLayers[e];

                    for (let p in pciLayers) {

                        let pci = parseInt(p);
                        let pciLayer = pciLayers[p];
                        
                        if (pcis) {


                            let pciIndexes = utils.indexesOf(pcis, pci);

                            for (let pi in pciIndexes) {

                                let pciIndex = pciIndexes[pi];

                                if (pciIndex !== -1 && ((earfcns && earfcn === earfcns[pciIndex]) || !earfcns)) 
                                    layers.push(pciLayer);
                            }

                        } else layers.push(pciLayer);

                    }
                    
            }

            layers.forEach((l) => l.addTo(layer));

        }

        drawHex(measurements, earfcns, pcis) {

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
                        result[earfcn][pci].push([meas.lat, meas.lng, m]);

                    }

                }
            )

            // Creating hexbinLayers in-place.
            for (let earfcn in result) {

                for (let pci in result[earfcn]) {

                    let hexLayer = L.hexbinLayer(styles.hexColor(minMeas, maxMeas))
                                    .hoverHandler(L.HexbinHoverHandler.tooltip());
                    result[earfcn][pci] = hexLayer.data(result[earfcn, pci]);

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

    }

}