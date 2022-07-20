const drawing = {

    Map: class {

        #map
        #cellLayer
        #antLayer
        #assocLayer
        #tacLayer
        #pciLayer
        #hexLayers
        // #rsrpLayer
        // #rsrqLayer
        // #rssiLayer
        // #cinrLayer


        constructor(map) {
            this.#map = map;
            this.#cellLayer = L.layerGroup();
            this.#tacLayer = L.layerGroup();
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

        #drawPoints(points, valChooser, colorChooser) {

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

                        let latLng = [point.lat, point.lng];    // Latitude and longitude of the point.
                        let val = valChooser(point);            // Value to associate to the group of the current point.

                        // Creating the group if it does not exists.
                        points[val] || (points[val] = []);

                        // Adding point to the group...
                        points[val].push(latLng);
                        
                    });

                    // Creating layers from group of points.
                    for (let val in points) {

                        let layer = new L.GridLayer.MaskCanvas(styles.pointStyle(colorChooser(val)));
                        layer.setData(points[val]);

                        pointDict[earfcn][pci][val] = layer;

                    }

                }

            }

            return pointDict;

        }

        //drawHex(measurements, )

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