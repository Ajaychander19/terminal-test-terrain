const drawing = {

    Map: class {

        #map
        #cellLayer
        #antLayer
        #assocLayer
        #pointLayers
        // #tacLayer
        // #pciLayer
        #hexLayers
        // #rsrpLayer
        // #rsrqLayer
        // #rssiLayer
        // #cinrLayer


        constructor(map) {
            this.#map = map;
        }

        drawCells(voronoi, antFeats, delFeats) {

            let vorFeats = voronoi.features;
            
            let features = vorFeats.concat(vorFeats)
                                   .concat(delFeats);
            
            this.#cellLayer = L.geoJson(turf.featureCollection(features));
            this.#antLayer = L.geoJson(turf.featureCollection(antFeats));
    
        }

        setCellLayer(b) { this.#setLayerVisibility(this.#cellLayer, b); }

        setAntLayer(b) { this.#setLayerVisibility(this.#antLayer, b); }

        #setLayerVisibility(layer, b) {
            if (b && !this.#map.hasLayer(layer)) layer.addTo(this.#map);
            else if (!b && this.#map.hasLayer(layer)) layer.removeFrom(this.#map);
        }

    }

}