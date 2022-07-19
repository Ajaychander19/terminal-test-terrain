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

        drawTAC(points) {

            this.#tacLayer = L.layerGroup();

            let tacs = {};

            for (let i in points) {

                let earfcnGr = points[i];

                for (let j in earfcnGr) {

                    earfcnGr[j].forEach((point) => {

                        let latLng = [point.lat, point.lng];
                        let tac = point.tac;

                        if (tacs[tac] === undefined) tacs[tac] = [];

                        tacs[tac].push(latLng);
                        
                    });

                }

            }

            for (let tac in tacs) {

                let tacLayer = new L.GridLayer.MaskCanvas(styles.pointStyle(styles.tacColor(tac)));
                tacLayer.setData(tacs[tac]);
                tacLayer.addTo(this.#tacLayer);

            }

        }

        #drawPoints(points, valChooser, colorChooser) {

            let pointDict = {};

            for (let earfcn in points) {

                let earfcnGr = points[i];

                pointDict[earfcn] || (pointDict[earfcn] = {});

                for (let pci in earfcnGr) {

                    pointDict[earfcn][pci] || (pointDict[earfcn][pci] = {})

                    let points = {}

                    earfcnGr[j].forEach((point) => {

                        let latLng = [point.lat, point.lng];
                        let val = valChooser;

                        points[val] || (points[val] = []);

                        points[val].push(latLng);
                        
                    });

                    // TODO add to point dict

                }

            }

            // for (let earfcn in pointDict) {

            //     for (let pci in pointDict)

            //     let pointLayer = new L.GridLayer.MaskCanvas(styles.pointStyle(colorChooser(tac)));
            //     pointLayer.setData(tacs[tac]);

            // }

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