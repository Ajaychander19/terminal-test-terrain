var csvread = {

    CSVReader: class  {

        // Attributes

        // File reading.
        #file
        #freader

        // Measurements columns.
        #earfcns
        #pcis

        // Points of data
        #points

        // Measurements.
        #rsrps
        #rssis
        #rsrqs

        // Associations
        #assocs

        // Directivity
        #antDirs
        #sectDels

        #antennas

        
        constructor(file) {
            this.#file = file;
            this.#earfcns = [];
            this.#pcis = [];
            this.#points = {};
            this.#rsrps = [];
            this.#rsrqs = [];
            this.#rssis = [];
            this.#rsrqs = [];
            this.#assocs = [];
            this.#antDirs = [];
            this.#sectDels = [];
            this.#antennas = {};

            this.#freader = new FileReader();

        }

        async readFile() {
            
            // Lines of the file which will be read.
            let flines = null;

            // Reading file...
            let result = await this.#promiseFile();

            // Splitting file content by lines...
            flines = result.split('\r\n');

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

                    case 0:
                        if (first === 'DEFINE') state = 1;
                        break;

                    case 1:
                        if (first === 'CONTENT') state = 2;
                        break;

                    case 2:

                        // Reading data...    

                        switch (first) {

                            case 'MEAS_EARFCNS':    // EARFCNS of measurement columns

                                if (llen < 6) throw new Error(
                                    'Error: line ' + lineNum + ': MEAS_EARFCNS line must contain at least 6 fields.')

                                for (let j = 5; j < llen; j++) this.#earfcns.push(line[j]);
                                measEarfcns = true
                                break;

                            case 'MEAS_PCIS':   // PCIS of measurement columns.

                                if (!measEarfcns) throw new Error(
                                    'Error: line ' + lineNum + ': no MEAS_EARFCNS line before MEAS_PCIS line.');

                                if (llen < 6) throw new Error(
                                    'Error: line ' + lineNum + ': MEAS_PCIS line must contain at least 6 fields.')

                                for (let j = 5; j < llen; j++) this.#pcis.push(line[j]);

                                if (this.#earfcns.length !== this.#pcis.length) throw new Error(
                                    'Error: line ' + lineNum + ': EARFCN count is different of PCI count.');

                                measLines = true;

                                break;

                            case 'MEASUREMENT':
                                if (!measLines) throw new Error(
                                    'Error: line ' + lineNum + ': missing MEAS_EARFCNS or MEAS_PCIS line before this line.')

                                if (llen != this.#earfcns.length + 5) throw new Error(
                                    'Error: line ' + lineNum + ': more measurements than EARFCN / PCI found.')

                                // Choosing in which table measurement will be added...    

                                let toAdd = null

                                switch (line[4]) {

                                    case 'RSRP':
                                        toAdd = this.#rsrps;
                                        break;

                                    case 'RSRQ':
                                        toAdd = this.#rsrqs;
                                        break;

                                    case 'RSSI':
                                        toAdd = this.#rssis;
                                        break;

                                }
            
                                // Series of measure taken in the same timestamp.
                                let series = {
                                    lat: csvread.parseNum(line[2], lineNum),
                                    lng: csvread.parseNum(line[3], lineNum),
                                    meas: []
                                };


                                // Adding measurements to series...
                                for (let j = 5; j < llen; j++) 
                                    series.meas.push(csvread.parseNum(line[j], lineNum, true));

                                toAdd.push(series);

                                break;

                            case 'POINT':   // Serving cell geolocated point.

                                if (llen < 11) throw new Error(
                                    'Error: line ' + lineNum + ': POINT line must contain at least 6 fields.');

                                let earfcn = csvread.parseNum(line[5], lineNum);
                                let pci = csvread.parseNum(line[6], lineNum);

                                // Filling serving EARFCN / PCI measurements dictionnary...
                                if (this.#points[earfcn] === undefined) this.#points[earfcn] = {}
                                if (this.#points[earfcn][pci] === undefined) this.#points[earfcn][pci] = []

                                // Point to add.
                                let point = {
                                    lat: csvread.parseNum(line[1], lineNum),
                                    lng: csvread.parseNum(line[2], lineNum),
                                    tac: csvread.parseNum(line[3], lineNum),
                                    cid: csvread.parseNum(line[4], lineNum),
                                    rsrp: csvread.parseNum(line[7], lineNum),
                                    rsrq: csvread.parseNum(line[8], lineNum),
                                    rssi: csvread.parseNum(line[9], lineNum),
                                    cinr: csvread.parseNum(line[10], lineNum),
                                };

                                this.#points[earfcn][pci].push(point);

                                break;

                            case 'DELIMITER':   // Sector delimiter.

                                if (llen < 6) throw new Error(
                                    'Error: line ' + lineNum + ': DELIMITER line must contain at least 6 fields.');

                                let cartoNum = csvread.parseNum(line[1], lineNum);
                                let latA = csvread.parseNum(line[2], lineNum);
                                let lngA = csvread.parseNum(line[3], lineNum);

                                if (this.#antennas[cartoNum] === undefined) 
                                    this.#antennas[cartoNum] = {lat: latA, lng: lngA, dels: []};

                                let delVect = {
                                    latB: csvread.parseNum(line[4], lineNum),
                                    lngB: csvread.parseNum(line[5], lineNum)
                                };

                                this.#antennas[cartoNum].dels.push(delVect);

                                this.#sectDels.push(delVect);

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

                                this.#antDirs.push(antVect);

                                break;

                            case 'ASSOC':   // (EARFCN, PCI) -> Antenna association.

                                if (llen < 7) throw new Error(
                                    'Error: line ' + lineNum + ': ASSOC line must contain at least 7 fields.');

                                let assoc = {
                                    cartoNum: csvread.parseNum(line[1], lineNum),
                                    antNum: csvread.parseNum(line[2], lineNum),
                                    tac: csvread.parseNum(line[3], lineNum),
                                    cid: csvread.parseNum(line[4], lineNum),
                                    earfcn: csvread.parseNum(line[5], lineNum),
                                    pci: csvread.parseNum(line[6], lineNum)
                                };

                                this.#assocs.push(assoc);

                                break;

                        }

                        break;

                }

            }

        }

        #promiseFile() {
            return new Promise((resolve, reject) => {
                this.#freader.onload = (e) => resolve(this.#freader.result);
                this.#freader.onerror = reject;
                this.#freader.readAsText(this.#file);
            })

        }

        get earfcns() { return utils.deepCopy(this.#earfcns); }

        get pcis() { return utils.deepCopy(this.#pcis); }

        get rsrps() { return utils.deepCopy(this.#rsrps); }
        
        get rsrqs() { return utils.deepCopy(this.#rsrqs); }

        get rssis() { return utils.deepCopy(this.#rssis); }

        get points() { return utils.deepCopy(this.#points); }

        get assocs() { return utils.deepCopy(this.#assocs); }

        get sectorDelimiters() { return utils.deepCopy(this.#sectDels); }

        get antennaDirections() { return utils.deepCopy(this.#antDirs); }

        get antennas() { return utils.deepCopy(this.#antennas); }
    
    },

    parseNum: function(str, i, null_allowed=false) {

        let x = parseFloat(str);

        if (Number.isNaN(x)) {
            if (null_allowed) return null;
            else throw new Error('Parsing Error: line ' + i + ': Invalid number: ' + str + '.');
        }

        return x;
    }
}