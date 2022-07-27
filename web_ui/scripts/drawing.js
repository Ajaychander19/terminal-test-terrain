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
        
        #rsrpLayer
        #rsrqLayer
        #rssiLayer
        #cinrLayer

        #nonFilteredTAC
        #nonFilteredPCI


        constructor(map) {
            this.#map = map;

            this.#cellLayer = L.layerGroup();
            this.#tacLayer = L.layerGroup();
            this.#pciLayer = L.layerGroup();

            this.#servingRSRP = drawing.hexBin('RSRP', styles.hexColor(0, 1));
            this.#servingRSRQ = drawing.hexBin('RSRQ', styles.hexColor(0, 1));
            this.#servingRSSI = drawing.hexBin('RSSI', styles.hexColor(0, 1));
            this.#servingCINR = drawing.hexBin('CINR', styles.hexColor(0, 1));

            this.#rsrpLayer = drawing.hexBin('RSRP', styles.hexColor(0, 1));
            this.#rsrqLayer = drawing.hexBin('RSRQ', styles.hexColor(0, 1));
            this.#rssiLayer = drawing.hexBin('RSSI', styles.hexColor(0, 1));
            this.#cinrLayer = drawing.hexBin('CINR', styles.hexColor(0, 1));

            this.#assocLayer = L.layerGroup();

            this.#nonFilteredTAC = null;
            this.#nonFilteredPCI = null;

        }

        drawCells(voronoi, antFeats, delFeats) {

            this.#cellLayer.clearLayers();

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

        drawServingHex(layer, points, valChooser, min, max, earfcns=null, pcis=null) {

            let hexData = [];

            let baseEarfncs = [];
            let basePcis = [];

            for (let earfcn in points) {

                let pciGroup = points[earfcn];

                for (let pci in pciGroup) {
                    baseEarfncs.push(parseInt(earfcn));
                    basePcis.push(parseInt(pci));
                }


            }

            let earpcis = utils.subEarpci(baseEarfncs, basePcis, earfcns, pcis);
            let filtEarfcns = earpcis.earfcns;
            let filtPcis = earpcis.pcis;

            for (let i in filtEarfcns) {

                let earfcn = filtEarfcns[i];
                let pci = filtPcis[i];

                points[earfcn][pci].forEach(
                    (pt) => {
                        let val = valChooser(earfcn, pci, pt);
                        hexData.push([pt.lng, pt.lat, val]);
                    }
                );

            }

            layer.options.colorScaleExtent = [min, max];

            layer.redraw();

            layer.data(hexData);

        }

        drawAssocs(assocs, antennas, checkEarfcns, checkPcis, earfcns=null, pcis=null) {

            this.#assocLayer.clearLayers();

            for (let cartoNum in assocs) {

                let assoc = assocs[cartoNum];       // Association between current Cartoradio Num. and EARFCN / PCI.
                let ant = antennas[cartoNum];   // Associated antenna

                // Creating the marker object.
                let marker = L.marker([ant.lat, ant.lng], {icon: styles.stationIcon()});

                marker.bindPopup(
                    this.drawAssocPopup(cartoNum, assoc, checkEarfcns, checkPcis, earfcns, pcis),
                    {closeOnClick: false, autoClose: false}
                );
                marker.addTo(this.#assocLayer);

            }


        }

        drawAssocPopup(cartoNum, assoc, checkEarfcns, checkPcis, earfcns=null, pcis=null) {

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

                checkBox.onclick = (evt) => { 
                    
                    if (evt.target.checked) {
                        checkEarfcns.push(earfcn);
                        checkPcis.push(pci);
                    } else utils.removeEarpci(checkEarfcns, checkPcis, earfcn, pci);

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

            // assoc.forEach(
            //     (asc) => {

            //         let earfcn = asc.earfcn;
            //         let pci = asc.pci;

            //         // Checkbox element.
            //         let checkBox = document.createElement('input');
            //         checkBox.setAttribute('type', 'checkbox');
                    
            //         // Identifying the checkbox.
            //         let checkId = 'check' + '-' + cartoNum + '-' + earfcn + '-' + pci;
            //         checkBox.id = checkId;

            //         // Label of the checkbox.
            //         let label = document.createElement('label');
            //         label.setAttribute('for', checkId);
            //         label.innerHTML = earfcn + ' - ' + pci;

            //         // Adding it to the checkboxes container div...
            //         checkDiv.append(...[
            //             checkBox, label, document.createElement('br')
            //         ]);

            //     }
            // );

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

                    // // For each measurement value...
                    // for (let i in meas) {

                    //     let m = meas[i];            // Measurement value.
                    //     let earfcn = earfcns[i];    // Associated EARFCn.
                    //     let pci = pcis[i];          // Associated PCI.

                    //     // // Defining resutl[earfcn][pci] if not defined.
                    //     // result[earfcn] || (result[earfcn] = {});
                    //     // result[earfcn][pci] || (result[earfcn][pci] = []);

                    //     // Adding (lat, lng, measurement value).
                    //     if (m) hexData.push([measObj.lng, measObj.lat, m]);

                    // }

                }
            );

            layer.options.colorScaleExtent = [min, max];
            layer.redraw();
            layer.data(hexData);

        }

        drawTAC(points) { return this.drawPoints(points, (_e, _pc, p) => p.tac, styles.tacColor); }

        drawPCI(points) { return this.drawPoints(points, (_e, pc, _p) => pc, (p) => styles.pciColor(p, 1)); }

        drawServingRSRP(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this.#servingRSRP, points, (_e, _p, pt) => pt.rsrp,
                min, max, earfcns, pcis,
            );
        }

        drawServingRSRQ(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this.#servingRSRQ, points, (_e, _p, pt) => pt.rsrq,
                min, max, earfcns, pcis
            );
        }

        drawServingRSSI(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this.#servingRSSI, points, (_e, _p, pt) => pt.rssi,
                min, max, earfcns, pcis
            );
        }

        drawServingCINR(points, min, max, earfcns=null, pcis=null) {
            this.drawServingHex(
                this.#servingCINR, points, (_e, _p, pt) => pt.cinr,
                min, max, earfcns, pcis
            );
        }

        drawRSRP(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this.#rsrpLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }

        drawRSRQ(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this.#rsrqLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }

        drawRSSI(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this.#rssiLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }

        drawCINR(measurements, earfcns, pcis, min, max, subEarfcns=null, subPcis=null) {
            this.drawHex(this.#cinrLayer, measurements, earfcns, pcis, min, max, subEarfcns, subPcis);
        }

        updateTACLayer(points, earfcn=null, pci=null) {
            this.#nonFilteredTAC = this.drawTAC(points);
            this.setPointLayer(this.#tacLayer, this.#nonFilteredTAC, earfcn, pci); 
        }

        updatePCILayer(points, earfcn=null, pci=null) {
            this.#nonFilteredPCI = this.drawPCI(points);
            this.setPointLayer(this.#pciLayer, this.#nonFilteredPCI, earfcn, pci); 
        }



        setCellLayer(b) { this.#setLayerVisibility(this.#cellLayer, b); }

        setAntLayer(b) { this.#setLayerVisibility(this.#antLayer, b); }

        setTACLayer(b) { this.#setLayerVisibility(this.#tacLayer, b); }

        setPCILayer(b) { this.#setLayerVisibility(this.#pciLayer, b); }

        setAssocLayer(b) { this.#setLayerVisibility(this.#assocLayer, b); }

        setServingRSRP(b) { this.#setLayerVisibility(this.#servingRSRP, b); }

        setServingRSRQ(b) { this.#setLayerVisibility(this.#servingRSRQ, b); }

        setServingRSSI(b) { this.#setLayerVisibility(this.#servingRSSI, b); }

        setServingCINR(b) { this.#setLayerVisibility(this.#servingCINR, b); }

        setRSRP(b) { this.#setLayerVisibility(this.#rsrpLayer, b); }

        setRSRQ(b) { this.#setLayerVisibility(this.#rsrqLayer, b); }

        setRSSI(b) { this.#setLayerVisibility(this.#rssiLayer, b); }

        // setCINR(b) { this.#setLayerVisibility(this.#cinrLayer, b); }

        #setLayerVisibility(layer, b) {
            if (b && !this.#map.hasLayer(layer)) layer.addTo(this.#map);
            else if (!b && this.#map.hasLayer(layer)) layer.removeFrom(this.#map);
        }

        drawSelectors(earfcns, pcis) {


            let pciSelector = document.querySelector('#pci-select');
            let earSelector = document.querySelector('#EARFCN_select');

            earSelector.innerHTML = '<option value="serving-earfcn">Serving EARFCN</option>'
                + '<option value="all-earfcns">All EARFCNs</option>';
            pciSelector.innerHTML = '<option value="serving-pci">Serving PCI</option>'
                + '<option value="all-pcis">All PCIs</option>';

            earfcns.forEach(
                (earfcn) => {

                    if (!document.querySelector('#EARFCN_select option[value="' + earfcn + '"]')) {
                    
                        let option = document.createElement('option');
                        option.setAttribute('value', earfcn);
                        option.innerHTML = earfcn;
                        earSelector.append(option);

                    }

                }
            );

            pcis.forEach(
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
        )

        return hex;

    }

}