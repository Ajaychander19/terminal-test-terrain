/**
 * Contains CSVReader class, used to read input file.
 * 
 * @constructor
 */
var csvread = {

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
            
            // Lines of the file which will be read.
            let flines = null;

            // Reading file...
            let result = await this._promiseFile();

            // Splitting file content by lines...
            flines = result.split(result.includes('\r\n') ? '\r\n' : '\n');

            // FSM state.
            let state = 0;

            // Used to check if MEAS_EARFCNS and MEAS_PCIS are read (in this order).
            let measLines = false;
            let measEarfcns = false;

            // Iterating over lines...
            for (let i in flines) {

                // Line number.
                let lineNum = i + 1

                // Splitting current line...
                let line = flines[i].split('|');

                // Current line length...
                let llen = line.length;
                
                if (llen === 0) throw new Error('Syntax error: line ' + lineNum + ': empty line.');

                let first = line[0]

                switch (state) {

                    case 0:     // Jumping DEFINE part.
                        if (first === 'DEFINE') state = 1;
                        break;

                    case 1:     // Jumping CONTENT part.
                        if (first === 'CONTENT') state = 2;
                        break;

                    case 2:

                        // Reading data...    

                        switch (first) {

                            case 'MEAS_EARFCNS':    // EARFCNS of measurement columns

                                if (llen < 6) throw new Error(
                                    'Error: line ' + lineNum + ': MEAS_EARFCNS line must contain at least 6 fields.')

                                for (let j = 5; j < llen; j++) this._earfcns.push(parseInt(line[j]));
                                measEarfcns = true;
                                break;

                            case 'MEAS_PCIS':   // PCIS of measurement columns.

                                if (!measEarfcns) throw new Error(
                                    'Error: line ' + lineNum + ': no MEAS_EARFCNS line before MEAS_PCIS line.');

                                if (llen < 6) throw new Error(
                                    'Error: line ' + lineNum + ': MEAS_PCIS line must contain at least 6 fields.')

                                for (let j = 5; j < llen; j++) this._pcis.push(parseInt(line[j]));

                                if (this._earfcns.length !== this._pcis.length) throw new Error(
                                    'Error: line ' + lineNum + ': EARFCN count is different of PCI count.');

                                measLines = true;

                                break;
                            case 'MEAS_BEAMS':
                                for (let j = 5; j < llen; j++){
                                    this._beams.push(parseInt(line[j]));
                                }
                                break;
                            case 'MEAS_NB':   // Number of measurement for each (EARFCN, PCI) couple

                                if (llen < 6) throw new Error(
                                    'Error: line ' + lineNum + ': MEAS_PCIS line must contain at least 6 fields.')

                                for (let j = 5; j < llen; j++) this._nbSamples.push(parseInt(line[j]));

                                if (this._nbSamples.length !== this._pcis.length) throw new Error(
                                    'Error: line ' + lineNum + ': NB-of-samples count is different from PCI count.');

                                break;


                            case 'MEASUREMENT':
                                if (!measLines) throw new Error(
                                    'Error: line ' + lineNum + ': missing MEAS_EARFCNS or MEAS_PCIS line before this line.')

                                if (llen != this._earfcns.length + 5) throw new Error(
                                    'Error: line ' + lineNum + ': more measurements than EARFCN / PCI found.')

                                // Choosing in which table measurement will be added...    

                                let toAdd = null
            
                                // Series of measure taken in the same timestamp.
                                let series = {
                                    lat: csvread.parseNum(line[2], lineNum),
                                    lng: csvread.parseNum(line[3], lineNum),
                                    meas: []
                                };


                                // Adding measurements to series...
                                for (let j = 5; j < llen; j++) 
                                    series.meas.push(csvread.parseNum(line[j], lineNum, true));

                                // Minimum and maximum of the series.
                                let localMin = Math.min(...(series.meas.filter((e) => e !== null)));
                                let localMax = Math.max(...(series.meas.filter((e) => e !== null)));

                                // Updating minimum / maximum properties following measurement type.
                                switch (line[4]) {

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

                                break;

                            case 'POINT':   // Serving cell geolocated point.

                                if (llen < 11) throw new Error(
                                    'Error: line ' + lineNum + ': POINT line must contain at least 6 fields.');

                                let earfcn = csvread.parseNum(line[5], lineNum);
                                let pci = csvread.parseNum(line[6], lineNum);
                                let cinr = csvread.parseNum(line[10], lineNum);

                                // Filling serving EARFCN / PCI measurements dictionnary...
                                if (this._points[earfcn] === undefined) this._points[earfcn] = {}
                                if (this._points[earfcn][pci] === undefined) this._points[earfcn][pci] = []

                                // Point to add.
                                let point = {
                                    lat: csvread.parseNum(line[1], lineNum),
                                    lng: csvread.parseNum(line[2], lineNum),
                                    tac: csvread.parseNum(line[3], lineNum),
                                    cid: csvread.parseNum(line[4], lineNum),
                                    rsrp: csvread.parseNum(line[7], lineNum),
                                    rsrq: csvread.parseNum(line[8], lineNum),
                                    rssi: csvread.parseNum(line[9], lineNum),
                                    cinr: cinr,
                                };

                                // Updating max and min CINR properties.
                                this._minCINR || (this._minCINR = cinr);
                                this._maxCINR || (this._maxCINR = cinr);

                                if (this._minCINR > cinr) this._minCINR = cinr;
                                if (this._maxCINR < cinr) this._maxCINR = cinr;

                                this._points[earfcn][pci].push(point);

                                break;

                            case 'DELIMITER':   // Sector delimiter.

                                if (llen < 6) throw new Error(
                                    'Error: line ' + lineNum + ': DELIMITER line must contain at least 6 fields.');

                                // Delimiter data.
                                let cartoNum = csvread.parseNum(line[1], lineNum);
                                let latA = csvread.parseNum(line[2], lineNum);
                                let lngA = csvread.parseNum(line[3], lineNum);

                                // Generating antennas data from deliimters.

                                if (this._antennas[cartoNum] === undefined) 
                                    this._antennas[cartoNum] = {lat: latA, lng: lngA, dels: []};

                                let delVect = {
                                    latB: csvread.parseNum(line[4], lineNum),
                                    lngB: csvread.parseNum(line[5], lineNum)
                                };

                                this._antennas[cartoNum].dels.push(delVect);

                                break;

                            case 'BS_ANT_DIR':  // Antenna direcitvity.

                                if (llen < 7) throw new Error(
                                    'Error: line ' + lineNum + ': BS_ANT_DIR line must contain at least 7 fields.');

                                let antVect = {
                                    cartoNum: csvread.parseNum(line[1], lineNum),
                                    antNum: csvread.parseNum(line[2], lineNum),
                                    latA: csvread.parseNum(line[3], lineNum),
                                    lngA: csvread.parseNum(line[4], lineNum),
                                    latB: csvread.parseNum(line[5], lineNum),
                                    lngB: csvread.parseNum(line[6], lineNum)
                                };

                                this._antDirs.push(antVect);

                                break;

                            case 'ASSOC':   // (EARFCN, PCI) -> Antenna association.

                                if (llen < 7) throw new Error(
                                    'Error: line ' + lineNum + ': ASSOC line must contain at least 7 fields.');

                                let carto = csvread.parseNum(line[1], lineNum);
                                let earfcn_ = csvread.parseNum(line[5], lineNum);
                                let pci_ = csvread.parseNum(line[6], lineNum);

                                this._assocs[carto] || (this._assocs[carto] = []);

                                this._assocs[carto].push({
                                    antNum: csvread.parseNum(line[2], lineNum),
                                    tac: csvread.parseNum(line[3], lineNum),
                                    cid: csvread.parseNum(line[4], lineNum),
                                    earfcn: csvread.parseNum(line[5], lineNum),
                                    pci: csvread.parseNum(line[6], lineNum)
                                });

                                break;

                        }

                        break;

                }

            }

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
    
    },

    /**
     * Parses a given string in an integer.
     * 
     * @param {String} str String to parse. 
     * @param {number} i Line number (used by CSVReader).
     * @param {boolean} nullAllowed if the parsing fails, returns null, throws an Error otherwise.
     * @returns The corresponding number if parsing suceeds, otherwise returns null if nullAllowed
     * is true.
     * @throws {Error} if the parsing fails and nullAllowed is false.
     * 
     * @function
     */
    parseNum: function(str, i, nullAllowed=false) {

        let x = parseFloat(str);

        if (Number.isNaN(x)) {
            if (nullAllowed) return null;
            else throw new Error('Parsing Error: line ' + i + ': Invalid number: ' + str + '.');
        }

        return x;
    }
}
