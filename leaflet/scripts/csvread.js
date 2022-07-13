class CSVReader {

    #file
    #earfcns
    #pcis
    #points
    #freader
    #file_io_hdl
    #rsrps
    #rssis
    #rsrqs

    
    constructor(file, io_error_handler) {
        this.#file = file;
        this.#earfcns = [];
        this.#pcis = [];
        this.#points = [];
        this.#measurements = []
        this.#file_io_hdl = io_error_handler

        this.#freader = new FileReader();

    }



    read_file() {

        let cont = false
        
        let flines = null

        let prom = new Promise((resolve, reject) => {
            this.#freader.onload = (_) => resolve(this.#freader.result);
            this.#freader.onerror = (e) => reject(e);
            this.#freader.readAsText(this.#file);
        })

        prom.then((result) => {
            flines = result.split('\r\n');
            console.log('test');
        }, this.#file_io_hdl);

        let state = 0;
        let meas_lines = false;
        let meas_earfns = false;

        for (let i in flines) {

            let lineNum = i + 1
            let line = flines[i].split('|');
            let llen = line.length;
            
            if (llen === 0) throw new Error('Syntax error : line ' + lineNum + ': empty line.');

            let first = line[0]

            switch (state) {

                case 0:
                    if (first === 'DEFINE') state = 1;
                    break;

                case 1:

                    if (first === 'CONTENT') state = 2;
                    break;

                case 2:

                    switch (first) {

                        case 'MEAS_EARFCNS':

                            if (llen < 6) throw new Error(
                                'Error : line ' + lineNum + ': MEAS_EARFCNS line must contain at least 6 fields.')

                            for (let j = 5; j < llen; j++) this.#earfcns.push(line[j]);
                            meas_earfns = true
                            break;

                        case 'MEAS_PCIS':

                            if (!meas_earfns) throw new Error(
                                'Error : line ' + lineNum + ': no MEAS_EARFCNS line before MEAS_PCIS line.');

                            if (llen < 6) throw new Error(
                                'Error : line ' + lineNum + ': MEAS_PCIS line must contain at least 6 fields.')

                            for (let j = 5; j < llen; j++) this.#pcis.push(line[j]);

                            if (this.#earfcns.length !== this.#pcis.length) throw new Error(
                                'Error : line ' + lineNum + ': EARFCN count is different of PCI count.');

                            meas_lines = true

                            break;

                        case 'MEASUREMENT':
                            if (!meas_lines) throw new Error(
                                'Error : line ' + lineNum + ': missing MEAS_EARFCNS or MEAS_PCIS line before this line.')

                            if (llen != this.#earfcns.length + 5) throw new Error(
                                'Error : line ' + lineNum + ': more measurements than EARFCN / PCI found.')

                                

                    }

                    break;

            }

        }

    }

}