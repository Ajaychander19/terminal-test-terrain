const app = {
    
    // Model: class {

    //     constructor() {

    //     }

    // },

    // Controller: class {

    //     constructor() {

    //     }

    // },

    // View: class {

    //     constructor(map) {

    //     }

    // },

    App: class {

        #map
        #drawingMap
        #fileReader

        #earfcnOnServing = true;
        #pciOnServing = true;
        #onServing = true;

        #selEarfcns = null;
        #selPcis = null;

        #rsrpChecked = false;
        #rsrqChecked = false;
        #rssiChecked = false;
        #cinrChecked = false;

        constructor() {

            // Background layers of the map.

            let baseMaps = {
                'Base Layer': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }),
                'Dark Layer': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                })
            };

            // Creating the map.
            this.#map = L.map('map', styles.mapStyle(baseMaps['Base Layer']));

            this.reset();

            // Adding background layers. 
            L.control.layers(baseMaps, null, { collapsed: false }).addTo(this.#map);

            this.#drawingMap = new drawing.Map(this.#map);

            // Setting up UI Events.

            document.querySelector('#fileSelect').onclick = (_) => {

                let inputElt = document.querySelector('#fileElem');
                inputElt.click();

            };

            document.querySelector('#fileElem').onchange = async (evt) => {

                let file = evt.srcElement.files[0];
                this.#fileReader = new csvread.CSVReader(file);
                await this.#fileReader.readFile();

                let antennas = this.#fileReader.antennas;

                let vor = processing.calcVoronoi(antennas);
                let dels = processing.calcDelimiters(vor, antennas);
                let ants = processing.calcAntennas(this.#fileReader.antennaDirections);

                let earfcns = this.#fileReader.earfcns;
                let pcis = this.#fileReader.pcis;

                this.#drawingMap.drawCells(vor, ants, dels);
                this.#drawingMap.drawAssocs(this.#fileReader.assocs, antennas);

                this.#drawingMap.setAntLayer(true);

                this.#drawingMap.setAssocLayer(true);

                this.#drawingMap.drawSelectors(earfcns, pcis);

                this.enableInputs(true);

                this.update();

            };

            document.querySelector('#Theory_Cell').onclick = (evt) => {
                this.#drawingMap.setCellLayer(evt.srcElement.checked);
            };

            document.querySelector('#sites-select').onchange = (evt) => {

                let onlySitesSel = evt.srcElement.value === 'only-sites';

                // if (onlySitesSel) $('.check-div').show();
                // else $('.check-div').hide();

            };

            document.querySelector('#Tracking_area').onclick = (evt) => {
                this.#drawingMap.setTACLayer(evt.srcElement.checked);
            };

            document.querySelector('#PCI').onclick = (evt) => {
                this.#drawingMap.setPCILayer(evt.srcElement.checked);
            };

            document.querySelector('#RSRP').onclick = (evt) => {

                this.#rsrpChecked = evt.srcElement.checked;
                this.updateDisplay();

            };

            document.querySelector('#rsrq').onclick = (evt) => {
                
                this.#rsrqChecked = evt.srcElement.checked;
                this.updateDisplay();

            };

            document.querySelector('#rssi').onclick = (evt) => {
                
                this.#rssiChecked = evt.srcElement.checked;
                this.updateDisplay();

            };

            document.querySelector('#cinr').onclick = (evt) => { 
                
                this.#cinrChecked = evt.srcElement.checked;
                this.updateDisplay();

            };

            document.querySelector('#EARFCN_select').onchange = (evt) => {

                let val = evt.srcElement.value;

                this.#earfcnOnServing = (val === 'serving-earfcn');

                this.#selEarfcns = (!this.#earfcnOnServing && val !== 'all-earfcns') ? 
                    [parseInt(val)] : null;

                this.#onServing = this.#earfcnOnServing || this.#pciOnServing;

                this.update();
                this.updateDisplay();

            }

            document.querySelector('#pci-select').onchange = (evt) => {

                let val = evt.srcElement.value;

                this.#pciOnServing = (val === 'serving-pci');

                this.#selPcis = (!this.#pciOnServing && val !== 'all-pcis') ? [parseInt(val)] : null;
                
                this.#onServing = this.#earfcnOnServing || this.#pciOnServing;

                this.update();
                this.updateDisplay();

            }

            document.querySelector('#clear-all').onclick = (evt) => this.reset();

        }

        update() {

            let points = this.#fileReader.points;
            let earfcns = this.#fileReader.earfcns;
            let pcis = this.#fileReader.pcis;
            let selEarfcns = this.#selEarfcns;
            let selPcis = this.#selPcis;
            let extr = this.#fileReader.extremas;

            this.#drawingMap.updatePCILayer(points, selEarfcns, selPcis);
            this.#drawingMap.updateTACLayer(points, selEarfcns, selPcis);

            this.#drawingMap.drawServingRSRP(points, extr.minRSRP, extr.maxRSRP, selEarfcns, selPcis);
            this.#drawingMap.drawServingRSRQ(points, extr.minRSRQ, extr.maxRSRQ, selEarfcns, selPcis);
            this.#drawingMap.drawServingRSSI(points, extr.minRSSI, extr.maxRSSI, selEarfcns, selPcis);
            this.#drawingMap.drawServingCINR(points, extr.minCINR, extr.maxCINR, selEarfcns, selPcis);
        
            this.#drawingMap.drawRSRP(this.#fileReader.rsrps, earfcns, pcis, extr.minRSRP, extr.maxRSRP, selEarfcns, selPcis);
            this.#drawingMap.drawRSRQ(this.#fileReader.rsrqs, earfcns, pcis, extr.minRSRQ, extr.maxRSRQ, selEarfcns, selPcis);
            this.#drawingMap.drawRSSI(this.#fileReader.rssis, earfcns, pcis, extr.minRSSI, extr.maxRSSI, selEarfcns, selPcis);
        
        }

        updateDisplay() {

            if (this.#onServing) {

                this.#drawingMap.setServingRSRP(this.#rsrpChecked);
                this.#drawingMap.setServingRSRQ(this.#rsrqChecked);
                this.#drawingMap.setServingRSSI(this.#rssiChecked);
                this.#drawingMap.setServingCINR(this.#cinrChecked);

                this.#drawingMap.setRSRP(false);
                this.#drawingMap.setRSRQ(false);
                this.#drawingMap.setRSSI(false);

            } else {

                this.#drawingMap.setRSRP(this.#rsrpChecked);
                this.#drawingMap.setRSRQ(this.#rsrqChecked);
                this.#drawingMap.setRSSI(this.#rssiChecked);

                this.#drawingMap.setServingRSRP(false);
                this.#drawingMap.setServingRSRQ(false);
                this.#drawingMap.setServingRSSI(false);
                this.#drawingMap.setServingCINR(false);

            }

        }

        reset() {

            console.log('reset');

            this.#earfcnOnServing = true;
            this.#pciOnServing = true;
            this.#onServing = true;

            this.#selEarfcns = null;
            this.#selPcis = null;

            this.#rsrpChecked = false;
            this.#rsrqChecked = false;
            this.#rssiChecked = false;
            this.#cinrChecked = false;

            this.#fileReader = null;

            document.querySelectorAll('select').forEach((elt) => elt.innerHTML = '');
            document.querySelectorAll('input[type="checkbox"]').forEach((elt) => elt.checked = false);

            this.enableInputs(false);

            if (this.#drawingMap) {
                this.updateDisplay();
                this.#drawingMap.setAntLayer(false);
                this.#drawingMap.setAssocLayer(false);
                this.#drawingMap.setCellLayer(false);
                this.#drawingMap.setTACLayer(false);
                this.#drawingMap.setPCILayer(false);
            }

        }

        enableInputs(b) {

            let visuInputs = document.querySelectorAll('.visu-params input, .visu-params select');
            
            visuInputs.forEach((input) => input.disabled = !b);

        }

    }

};

(function () {
    new app.App();
})();