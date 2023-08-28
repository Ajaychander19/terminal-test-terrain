/**
 * Main application namespace, contains the App class.
 * @namespace
 */
const app = {

    /**
     * Application class, wraps the application state and methods.
     * @class
     */
    App: class {

        _map                        // Leaflet map.
        _drawingMap                 // Map object to wrap the Leaflet map.
        _fileReader                 // CSVReader object.

        _earfcnOnServing = true;    // true if "Serving EARFCN" is selected.
        _pciOnServing = true;       // true if "Serving PCI" is selected.
        _onServing = true;          // true if serving measurement layers must be dispalyed.

        _selEarfcns = null;         // Selected EARFCNs (with drop down menu).
        _selPcis = null;            // Selected PCIs (with drop down menu).
        _selBeams = null;

        _checkEarfcns = [];         // Selected EARFCNs (with sites checkboxes).
        _checkPcis = [];            // Selected PCIs (with sites checkboxes).
        _checkBeams = [];           // Selected Beams for each PCI

        _allSites = true;           // true if "All Sites" is selected in Sites.

        _altCol = 1;                // Alternate PCI color value.

        // Corresponds to layer checkboxes states, true if the checkbox is checked.
        _rsrpChecked = false;
        _rsrqChecked = false;
        _rssiChecked = false;
        _cinrChecked = false;

        /**
         * Application class constructor.
         * @constructor
         */
        constructor() {

            // Background layers of the map.

            let baseMaps = {
                'Base Layer': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }),
                'Dark Layer': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolls/{z}/{x}/{y}{r}.png', {
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                })
            };

            // Creating the map.
            this._map = L.map('map', styles.mapStyle(baseMaps['Base Layer']));

            this.reset();   // Resetting UI.

            // Adding background layers. 
            L.control.layers(baseMaps, null, { collapsed: false }).addTo(this._map);

            // Wrapping the map in a map drawing object.
            this._drawingMap = new drawing.Map(this._map);

            // Setting up UI Events.
            this.attributeEvents();

        }

        /**
         * Updates layers by redrawing them. This function is used to display changes in selected
         * EARFCNs and PCIs.
         * 
         * @function
         */
        update() {
            let points = this._fileReader.points;       // Serving points.
            let earfcns = this._fileReader.earfcns;     // EARFCNs
            let pcis = this._fileReader.pcis;           // PCIs
            let beams = this._fileReader.beams;         // beams
            let selEarfcns = this._selEarfcns;          // EARFCNs selected with drop down menu.
            let selPcis = this._selPcis;                // PCIs selected with drop down menu.
            let selBeams = this._selBeams;
            let checkEarfcns = this._checkEarfcns;      // EARFCNs selected with checkboxes.
            let checkPcis = this._checkPcis;            // PCIs selected with sites checkboxes.
            let checkBeams = this._checkBeams;

            // Extremums
            const RSRP_MIN = -120;
            const RSRP_MAX = -60;

            const RSRQ_MIN = -20;
            const RSRQ_MAX = -3;

            // TODO Deteminate range for RSSI.
            const RSSI_MIN = -120;
            const RSSI_MAX = -30;

            // TODO Determinate range for CINR.
            const CINR_MIN = -20;
            const CINR_MAX = 20;

            // Filtering EARFCNs and PCIs following drop down menus selection.
            let filtEarpcis = utils.subEarpci(earfcns, pcis, beams, selEarfcns, selPcis);

            // Filtering EARFCNs and PCIs using sites checkboxes.
            let onlySitesEarpcis = utils.subEarpci(filtEarpcis.earfcns, filtEarpcis.pcis, filtEarpcis.beams, checkEarfcns, checkPcis);
            
            // Final EARFCNs and PCIs list.
            let finalEarfcns = (this._allSites) ? selEarfcns : onlySitesEarpcis.earfcns;
            let finalPcis = (this._allSites) ? selPcis : onlySitesEarpcis.pcis;
            //let finalBeams = (this._allSites) ? selBeams: onlySitesEarpcis.beams;

            let finalBeams = checkBeams;

            // Updating TAC / PCI layers.
            this._drawingMap.updatePCILayer(points, finalEarfcns, finalPcis, finalBeams, this._altCol);
            this._drawingMap.updateTACLayer(points, finalEarfcns, finalPcis, finalBeams);

            // Updating serving measurement layers.
            this._drawingMap.drawServingRSRP(points, RSRP_MIN, RSRP_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawServingRSRQ(points, RSRQ_MIN, RSRQ_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawServingRSSI(points, RSSI_MIN, RSSI_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawServingCINR(points, CINR_MIN, CINR_MAX, finalEarfcns, finalPcis, finalBeams);
        
            // Updating global measurement layers.
            this._drawingMap.drawRSRP(this._fileReader.rsrps, earfcns, pcis, beams, RSRP_MIN, RSRP_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawRSRQ(this._fileReader.rsrqs, earfcns, pcis, beams, RSRQ_MIN, RSRQ_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawRSSI(this._fileReader.rssis, earfcns, pcis, beams, RSSI_MIN, RSSI_MAX, finalEarfcns, finalPcis, finalBeams);
        
        }

        /**
         * Displays or hides layers following checked checkboxes and selected EARFCNs / PCIs.
         * This function DOES NOT redraws layers.
         * 
         * @function
         */
        updateDisplay() {

            if (this._onServing) {

                // Displaying serving measurement layers.

                this._drawingMap.setServingRSRP(this._rsrpChecked);
                this._drawingMap.setServingRSRQ(this._rsrqChecked);
                this._drawingMap.setServingRSSI(this._rssiChecked);
                this._drawingMap.setServingCINR(this._cinrChecked);

                this._drawingMap.setRSRP(false);
                this._drawingMap.setRSRQ(false);
                this._drawingMap.setRSSI(false);

            } else {

                // Displaying global measurement layers.

                this._drawingMap.setRSRP(this._rsrpChecked);
                this._drawingMap.setRSRQ(this._rsrqChecked);
                this._drawingMap.setRSSI(this._rssiChecked);

                this._drawingMap.setServingRSRP(false);
                this._drawingMap.setServingRSRQ(false);
                this._drawingMap.setServingRSSI(false);
                this._drawingMap.setServingCINR(false);

            }

        }

        /**
         * Update sites pins and their checkboxes, following selected EARFCNs and PCIs.
         * 
         * @function
         */
        updateAssocs() {
            // Getting selected EARFCNS / PCIS.

            let earpcis = this._allSites ? {earfcns: [], pcis: [], beams: {}, indices: []} : utils.subEarpci(this._fileReader.earfcns,
                this._fileReader.pcis, this._fileReader._beams, this._selEarfcns, this._selPcis);

            // Redrawing associated stations pins.
            this._drawingMap.drawAssocs(
                this._fileReader.assocs, this._fileReader.antennas, this._checkEarfcns, this._checkPcis, this._checkBeams,
                () => this.update(), earpcis.earfcns, earpcis.pcis, earpcis.beams);

        }

        /**
         * Resets the state of the app and the UI.
         * 
         * @function
         */
        reset() {

            // Resetting attributes.

            this._earfcnOnServing = true;
            this._pciOnServing = true;
            this._onServing = true;
            this._allSites = true;

            this._selEarfcns = null;
            this._selPcis = null;
            this._selBeams = null;

            this._checkEarfcns = [];
            this._checkPcis = [];
            this._checkBeams = [];

            this._rsrpChecked = false;
            this._rsrqChecked = false;
            this._rssiChecked = false;
            this._cinrChecked = false;

            this._fileReader = null;
            
            this._altCol = 1;

            // Clearing drop down selectors.
            document.querySelectorAll('#EARFCN_select, #pci-select').forEach((elt) => elt.innerHTML = '');
            document.querySelector('#sites-select').value = 'all-sites';

            // Unchecking checkboxes.
            document.querySelectorAll('input[type="checkbox"]').forEach((elt) => elt.checked = false);

            // Locking the UI.
            document.querySelector('#fileSelect').disabled = false;
            this.enableInputs(false);

            // Hiding remaining layers.
            if (this._drawingMap) {
                this.updateDisplay();
                this._drawingMap.setAntLayer(false);
                this._drawingMap.setAssocLayer(false);
                this._drawingMap.setCellLayer(false);
                this._drawingMap.setTACLayer(false);
                this._drawingMap.setPCILayer(false);
            }

        }

        /**
         * Enables or disables inputs.
         * @param {boolean} b true to enable inputs, false otherwise.
         * 
         * @function
         */
        enableInputs(b) {

            let visuInputs = document.querySelectorAll('.visu-params input, .visu-params select, #clear-all');
            
            visuInputs.forEach((input) => input.disabled = !b);

        }

        /**
         * Attributes event handlers to UI components.
         * 
         * @function
         */
        attributeEvents() {

            // Select file button.
            document.querySelector('#fileSelect').onclick = (evt) => {

                let inputElt = document.querySelector('#fileElem');
                inputElt.click();

            };

            // File selector.
            // Asynchronous method due to the asynchronous file reading.
            document.querySelector('#fileElem').onchange = async (evt) => {

                // Reading file.
                let file = evt.target.files[0];
                this._fileReader = new csvreadv2.CSVReader(file);//new csvread.CSVReader(file);//new csvreadv2.CSVReader(file);
                await this._fileReader.readFile();  // Wait for file to be read.

                // Reading antennas data.
                let antennas = this._fileReader.antennas;

                // Processing Voronoi cells, antenna directions and sector delimiters.
                let vor = processing.calcVoronoi(antennas);
                let dels = processing.calcDelimiters(vor, antennas);
                let ants = processing.calcAntennas(this._fileReader.antennaDirections);

                // Reading EARFCNs and PCIs.
                let earfcns = this._fileReader.earfcns;
                let pcis = this._fileReader.pcis;

                // Drawing Voronoi cells.
                this._drawingMap.drawCells(vor, ants, dels);
                this.updateAssocs();

                // Displaying base layers.
                this._drawingMap.setAntLayer(true);
                this._drawingMap.setAssocLayer(true);
                this._drawingMap.drawSelectors(earfcns, pcis);

                // Enabling inputs.
                this.enableInputs(true);

                // Updating the UI.
                this.update();

            };

            // Theoritical cells checkbox.
            document.querySelector('#Theory_Cell').onclick = (evt) => {
                this._drawingMap.setCellLayer(evt.target.checked);
            };

            // TAC checkbox.
            document.querySelector('#Tracking_area').onclick = (evt) => {
                this._drawingMap.setTACLayer(evt.target.checked);
            };

            // PCI checkbox.
            document.querySelector('#PCI').onclick = (evt) => {
                this._drawingMap.setPCILayer(evt.target.checked);
            };

            // RSRP checkbox.
            document.querySelector('#RSRP').onclick = (evt) => {

                this._rsrpChecked = evt.target.checked;
                this.updateDisplay();

            };

            // RSRQ checkbox.
            document.querySelector('#rsrq').onclick = (evt) => {
                
                this._rsrqChecked = evt.target.checked;
                this.updateDisplay();

            };

            // RSSI checkbox.
            document.querySelector('#rssi').onclick = (evt) => {
                
                this._rssiChecked = evt.target.checked;
                this.updateDisplay();

            };

            // CINR checkbox.
            document.querySelector('#cinr').onclick = (evt) => { 
                
                this._cinrChecked = evt.target.checked;
                this.updateDisplay();

            };

            // Sites selector.
            document.querySelector('#sites-select').onchange = (evt) => {

                this._allSites = (evt.target.value === 'all-sites');
                this.update();
                this.updateAssocs();

            }

            // EARFCNs selector.
            document.querySelector('#EARFCN_select').onchange = (evt) => {

                let val = evt.target.value; // Selector value.

                // On serving cell ?
                this._earfcnOnServing = (val === 'serving-earfcn');

                // Choosing EARFCN selection.
                this._selEarfcns = (!this._earfcnOnServing && val !== 'all-earfcns') ? 
                    [parseInt(val)] : null;

                this._onServing = this._earfcnOnServing || this._pciOnServing;

                // Updating UI.
                this.update();
                this.updateDisplay();
                this.updateAssocs();

            }

            // PCIs selector.
            // Same than EARFCNs.
            document.querySelector('#pci-select').onchange = (evt) => {

                let val = evt.target.value;

                this._pciOnServing = (val === 'serving-pci');

                this._selPcis = (!this._pciOnServing && val !== 'all-pcis') ? [parseInt(val)] : null;
                
                this._onServing = this._earfcnOnServing || this._pciOnServing;

                this.update();
                this.updateDisplay();
                this.updateAssocs();

            }

            // "Clear All" button.
            document.querySelector('#clear-all').onclick = (evt) => this.reset();

            // Alternative color button.
            document.querySelector('#ColorAlt').onclick = (evt) => {

                this._altCol = evt.target.checked ? 0 : 1;
                this.update();

            }

        }

    }

};

(function () {
    new app.App();
})();
