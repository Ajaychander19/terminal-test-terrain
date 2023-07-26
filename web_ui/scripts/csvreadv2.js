/**
 * Contains CSVReader class, used to read input file.
 *
 * @constructor
 */
var csvreadv2 = {

    /**
     * CSV input file reading class.
     * Recognizes the input CSV file using a finite state machine,
     * then store data of the file.
     *
     * @constructor
     */
    CSVReader: class  {

        // Attributes

        // File reading.
        _file
        _freader

        // Measurements columns.
        _earfcns
        _pcis
        _beams

        // Points of data
        _points

        // Measurements.
        _rsrps
        _rssis
        _rsrqs
        _cinrs

        // Associations
        _assocs

        // Directivity
        _antDirs
        _sectDels

        _antennas

        // Minimum / maximums.
        _minRSRP
        _minRSRQ
        _minRSSI
        _minCINR

        _maxRSRP
        _maxRSRQ
        _maxRSSI
        _maxCINR


        /**
         * Class constructor.
         *
         * @param {File} File to read.
         *
         * @constructor
         */
        constructor(file) {
            this._file = file;
            this._earfcns = [];
            this._pcis = [];
            this._beams = [];
            this._nbSamples = [];
            this._points = {};
            this._rsrps = [];
            this._rsrqs = [];
            this._rssis = [];
            this._cinrs = [];
            this._assocs = {};
            this._antDirs = [];
            this._sectDels = [];
            this._antennas = {};

            this._minRSRP = null;
            this._minRSRQ = null;
            this._minRSSI = null;
            this._minCINR = null;

            this._maxRSRP = null;
            this._maxRSRQ = null;
            this._maxRSSI = null;
            this._maxCINR = null;

            this._freader = new FileReader();

        }

        /**
         * Initiates the reading of the input file.
         *
         * This function is asynchronous, and may require to use await keyword to ensure file
         * has been entierly read before continuing script execution.
         *
         * @async
         * @function
         */
        async readFile() {
            let result = await this._promiseFile();

            const parsedData = Papa.parse(result, {
                delimiter: "|",
                header: false,
                dynamicTyping: true,
            });

            const parsedResult = this.parseCSVDataByHeaders(parsedData.data);

            parsedResult.MEAS_EARFCNS.forEach((line) => {
                for (const key in line) {
                    if(key !== "MEAS_EARFCNS" && key !== "NA"){
                        if (Object.prototype.hasOwnProperty.call(line, key)) {
                            const value = line[key];
                            if(Array.isArray(value)){
                                for (const element of value) {
                                    this._earfcns.push(+element);
                                }
                            }
                            else{
                                this._earfcns.push(+value);
                            }
                        }
                    }
                }
            });

            parsedResult.MEAS_PCIS.forEach((line) => {
                  for (const key in line) {
                  if(key !== "MEAS_PCIS" && key !== "NA"){
                        if (Object.prototype.hasOwnProperty.call(line, key)) {
                            const value = line[key];
                            if(Array.isArray(value)){
                                for (const element of value) {
                                    this._pcis.push(+element);
                                }
                            }
                            else{
                                this._pcis.push(+value);
                            }
                        }
                  }
                }
            });

            parsedResult.MEAS_BEAMS.forEach((line) => {
                for (const key in line) {
                    if(key !== "MEAS_BEAMS" && key !== "NA"){
                        if (Object.prototype.hasOwnProperty.call(line, key)) {
                            const value = line[key];
                            if(Array.isArray(value)){
                                for (const element of value) {
                                    this._beams.push(+element);
                                }
                            }
                            else{
                                this._beams.push(+value);
                            }
                        }
                    }
                }
            });

            parsedResult.MEAS_NB.forEach((line) => {
                for (let j = 5; j < line.length; j++) this._nbSamples.push(parseInt(line[j]));
            });

            parsedResult.MEASUREMENT.forEach((line) => {
                // Choosing in which table measurement will be added...

                let toAdd = null

                // Series of measure taken in the same timestamp.
                let series = {
                    lat: +line['Lat'],
                    lng: +line['Lng'],
                    meas: []
                };


                // Adding measurements to series...
                for (let j = 5; j < line.length; j++)
                    series.meas.push(+line[j]);

                // Minimum and maximum of the series.
                let localMin = Math.min(...(series.meas.filter((e) => e !== null)));
                let localMax = Math.max(...(series.meas.filter((e) => e !== null)));

                // Updating minimum / maximum properties following measurement type.
                switch (line['Measurement_Name']) {

                    case 'RSRP':
                        toAdd = this._rsrps;

                        this._minRSRP || (this._minRSRP = localMin);
                        this._maxRSRP || (this._maxRSRP = localMax);

                        if (this._minRSRP > localMin) this._minRSRP = localMin;
                        if (this._maxRSRP < localMax) this._maxRSRP = localMax;

                        break;

                    case 'RSRQ':
                        toAdd = this._rsrqs;

                        this._minRSRQ || (this._minRSRQ = localMin);
                        this._maxRSRQ || (this._maxRSRQ = localMax);

                        if (this._minRSRQ > localMin) this._minRSRQ = localMin;
                        if (this._maxRSRQ < localMax) this._maxRSRQ = localMax;

                        break;

                    case 'RSSI':
                        toAdd = this._rssis;


                        this._minRSSI || (this._minRSSI = localMin);
                        this._maxRSSI || (this._maxRSSI = localMax);

                        if (this._minRSSI > localMin) this._minRSSI = localMin;
                        if (this._maxRSSI < localMax) this._maxRSSI = localMax;

                        break;

                }

                toAdd.push(series);

            });

            parsedResult.DELIMITER.forEach((line)  => {
                // Delimiter data.
                let cartoNum = +line['Cartoradio_Number'];
                let latA = +line['Support_Lat'];
                let lngA = +line['Support_Lng'];


                // Generating antennas data from deliimters.

                if (this._antennas[cartoNum] === undefined)
                    this._antennas[cartoNum] = {lat: latA, lng: lngA, dels: []};

                let delVect = {
                    latB: +line['Del_Lat'],
                    lngB: +line['Del_Lng']
                };

                this._antennas[cartoNum].dels.push(delVect);

            });

            parsedResult.BS_ANT_DIR.forEach((line) => {
                let antVect = {
                    cartoNum: +line['Cartoradio_Number'],
                    antNum: +line['Ant_Number'],
                    latA: +line['Support_Lat'],
                    lngA: +line['Support_Lng'],
                    latB: +line['Dest_Lng'],
                    lngB: +line['Dest_Lat']
                };

                this._antDirs.push(antVect);
            });

            parsedResult.ASSOC.forEach((line) =>{
                let carto = +line['Cartoradio_Number'];
                let earfcn_ = +line['EARFCN'];
                let pci_ = +line['PCI'];

                this._assocs[carto] || (this._assocs[carto] = []);

                this._assocs[carto].push({
                    antNum: +line['Ant_Number'],
                    tac: +line['TAC'],
                    cid: +line['CID'],
                    earfcn: +line['EARFCN'],
                    pci: +line['PCI']
                });
            });

            parsedResult.POINT.forEach((line) =>{
                    let earfcn = +line['EARFCN'];
                    let pci = +line['PCI'];
                    let beam = +line['BEAM'];
                    let cinr = +line['CINR'];

                    // Filling serving EARFCN / PCI measurements dictionnary...
                    if (this._points[earfcn] === undefined) this._points[earfcn] = {}
                    if (this._points[earfcn][pci] === undefined) this._points[earfcn][pci] = {}
                    if (this._points[earfcn][pci][beam] === undefined) this._points[earfcn][pci][beam] = []

                    // Point to add.
                    let point = {
                        lat: +line['Lat'],
                        lng: +line['Lng'],
                        tac: +line['TAC'],
                        cid: +line['CID'],
                        rsrp: +line['RSRP'],
                        rsrq: +line['RSRQ'],
                        rssi: +line['RSSI'],
                        cinr: cinr,
                    };

                    // Updating max and min CINR properties.
                    this._minCINR || (this._minCINR = cinr);
                    this._maxCINR || (this._maxCINR = cinr);

                    if (this._minCINR > cinr) this._minCINR = cinr;
                    if (this._maxCINR < cinr) this._maxCINR = cinr;

                    this._points[earfcn][pci][beam].push(point);
            });
        }
        _promiseFile() {
            return new Promise((resolve, reject) => {
                this._freader.onload = (e) => resolve(this._freader.result);
                this._freader.onerror = reject;
                this._freader.readAsText(this._file);
            })
        }

        /**
         * @returns List of EARFCNs from (EARFCN, PCI) pairs.
         *
         * @function
         */
        get earfcns() { return utils.deepCopy(this._earfcns); }

        /**
         * @returns List of PCIs from (EARFCN, PCI) pairs.
         *
         * @function
         */
        get pcis() { return utils.deepCopy(this._pcis); }

        get beams() {return utils.deepCopy(this._beams); }

        /**
         * @returns List of global RSRPs.
         *
         * @function
         */
        get rsrps() { return utils.deepCopy(this._rsrps); }

        /**
         * @returns List of global RSRQs.
         *
         * @function
         */
        get rsrqs() { return utils.deepCopy(this._rsrqs); }

        /**
         * @returns List of global RSSIs.
         *
         * @function
         */
        get rssis() { return utils.deepCopy(this._rssis); }

        /**
         * @returns List of global CINRs.
         *
         * @function
         */
        get cinrs() { return utils.deepCopy(this._cinrs); }

        /**
         * @returns Serving measurements points, classed by EARFCN and PCI, containing TAC,
         * CID, and serving measurements.
         *
         * @function
         */
        get points() { return utils.deepCopy(this._points); }

        /**
         * @returns Associations between cartoradio number and
         * antennas (ant. number, TAC, CID, EARFCN, PCI).
         *
         * @function
         */
        get assocs() { return utils.deepCopy(this._assocs); }

        /**
         * @returns Antenna directivity data
         *
         * @function
         */
        get antennaDirections() { return utils.deepCopy(this._antDirs); }

        /**
         * @return Antennas data, and sector delimiters data.
         *
         * @function
         */
        get antennas() { return utils.deepCopy(this._antennas); }

        /**
         * @return Global measurements minimum and maximums.
         *
         * @function
         * @deprecated
         */
        get extremas() {

            return {
                minRSRP: this._minRSRP,
                maxRSRP: this._maxRSRP,
                minRSRQ: this._minRSRQ,
                maxRSRQ: this._maxRSRQ,
                minRSSI: this._minRSSI,
                maxRSSI: this._maxRSSI,
                minCINR: this._minCINR,
                maxCINR: this._maxCINR,
            };

        }

        parseCSVDataByHeaders(data) {
            const parsedData = {
                measEarfcn: [],
                measPci: [],
                measBeams: [],
                measNb: [],
                delimiter: [],
                point: [],
                measurement: [],
                bsAntDir: [],
                assoc:[],
            };

            let currentHeaderType = null;

            data.forEach((line) => {
                if (line[0] === 'MEAS_EARFCNS') {
                    currentHeaderType = 'measEarfcn';
                } else if (line[0] === 'MEAS_PCIS') {
                    currentHeaderType = 'measPci';
                } else if (line[0] === 'MEAS_BEAMS') {
                    currentHeaderType = 'measBeams';
                } else if (line[0] === 'MEAS_NB') {
                    currentHeaderType = 'measNb';
                } else if (line[0] === 'DELIMITER') {
                    currentHeaderType = 'delimiter';
                } else if (line[0] === 'BS_ANT_DIR') {
                    currentHeaderType = 'bsAntDir';
                } else if (line[0] === 'MEASUREMENT') {
                    currentHeaderType = 'measurement';
                } else if (line[0] === 'ASSOC') {
                    currentHeaderType = 'assoc';
                } else if (line[0] === 'POINT') {
                    currentHeaderType = 'point';
                }
                // Push the line data into the appropriate array based on the current header type
                if (currentHeaderType !== null) {
                    parsedData[currentHeaderType].push(line);
                }
            });

            // Use papaparse to parse each type of lines separately with the appropriate headers
            const parsedMeasEarfcn = Papa.parse(parsedData.measEarfcn.join('\n'), { header: true });
            const parsedMeasPci = Papa.parse(parsedData.measPci.join('\n'), { header: true });
            const parsedMeasBeams = Papa.parse(parsedData.measBeams.join('\n'), { header: true });
            const parsedMeasNb = Papa.parse(parsedData.measNb.join('\n'), { header: true });
            const parsedBsAntDir = Papa.parse(parsedData.bsAntDir.join('\n'), { header: true });
            const parsedPoint = Papa.parse(parsedData.point.join('\n'), { header: true });
            const parsedMeasurement = Papa.parse(parsedData.measurement.join('\n'), { header: true });
            const parsedDelimiter = Papa.parse(parsedData.delimiter.join('\n'), { header: true });
            const parsedAssoc = Papa.parse(parsedData.assoc.join('\n'), { header: true });

            return {
                MEAS_EARFCNS: parsedMeasEarfcn.data,
                MEAS_PCIS: parsedMeasPci.data,
                MEAS_BEAMS: parsedMeasBeams.data,
                MEAS_NB: parsedMeasNb.data,
                MEASUREMENT: parsedMeasurement.data,
                POINT: parsedPoint.data,
                ASSOC: parsedAssoc.data,
                DELIMITER : parsedDelimiter.data,
                BS_ANT_DIR : parsedBsAntDir.data
            };
        }

    }
}