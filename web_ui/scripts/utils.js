/**
 * Contains general-purpose function for program.
 * 
 * @namespace
 */
const utils = {

    /**
     * Deep-copies an object (copy of the object and its childs), 
     * by serializing it in JSON then decoding this JSON.
     * 
     * @param {*} obj Object to deep-copy.
     * @returns A deep-copy of obj.
     * 
     * @function
     */
    deepCopy: function (obj) { return JSON.parse(JSON.stringify(obj)); },

    /**
     * Finds the indexes of occurences of a given value in an array.
     * 
     * @param {Array} arr Array to search in. 
     * @param {*} obj Object to search. 
     * @returns An Array of indexes of obj occurences.
     * 
     * @function
     */
    indexesOf: function (arr, obj) {

        let result = [];
        for (let i in arr) if (obj === arr[i]) result.push(parseInt(i));
        return result;

    },

    /**
     * Searches an EARFCN and PCI pair amongs EARFCN / PCI lists.
     * 
     * @param {Array} earfcns EARFCN list to search in.
     * @param {Array} pcis PCI list to search in.
     * @param {number} earfcn EARFCN to search.
     * @param {number} pci PCI to search.
     * @returns The index of the pair in earfcns and pcis if found, -1 otherwise.
     * 
     * @function
     */
    indexOfEarpci: function (earfcns, pcis, earfcn, pci) {

        let earfcnIdx = utils.indexesOf(earfcns, earfcn);
        let pcisIdx = utils.indexesOf(pcis, pci);

        let inter = earfcnIdx.filter((e) => pcisIdx.includes(e))

        return inter.length !== 0 ? inter[0] : -1;

    },

    /**
     * Remove an EARFCN / PCI pair from lists of EARFCN / PCI.
     * 
     * @param {Array} earfcns EARFCN list.
     * @param {Array} pcis PCI list.
     * @param {number} earfcn EARFCN to remove from list.
     * @param {number} pci PCI to remove from list.
     * 
     * @function
     */
    removeEarpci: function (earfcns, pcis, earfcn, pci) {
        
        let i = utils.indexOfEarpci(earfcns, pcis, earfcn, pci);

        if (i !== -1) {
            earfcns.splice(i, 1);
            pcis.splice(i, 1);
        }

    },

    /**
     * Filters EARFCN / PCIS from a superset list, using a subset list.
     * 
     * @param {Array} earfcns Superset of EARFCNs 
     * @param {Array} pcis Superset of PCIs
     * @param {Array} reqEarfcns Subset of EARFCNs (if null, represents all EARFCNs from the superset).
     * @param {Array} reqPcis Subset of PCIs (if null, represents all PCIs from the superset).
     * @returns Object which contains lists of filtered EARFCNs / PCIs, and list of indexes of EARFCNs / PCIs
     * pairs in the superset.
     * 
     * @function 
     */
    subEarpci: function (earfcns, pcis, /*beams=null,*/ reqEarfcns=null, reqPcis=null/*, reqBeams=null*/) {

        // Result object.
        let result = {earfcns: [], pcis: []/*, beams: [],*/, indices: []};

        // Indexes of EARFCNs / PCIs of the subset.
        let subEarfcnsIdx = [];
        let subPcisIdx = [];
        //let subBeamsIdx = [];

        // Filling subEarfcnsIdx.
        if (!reqEarfcns) subEarfcnsIdx = earfcns.map((_, i) => parseInt(i));    // If null : all elements.
        else reqEarfcns.forEach(
            (e) => utils.interPush(subEarfcnsIdx, utils.indexesOf(earfcns, e))
        );

        // Filling subPcisIdx.
        if (!reqPcis) subPcisIdx = pcis.map((_, i) => parseInt(i));             // If null : all elements.
        else reqPcis.forEach(
            (e) => utils.interPush(subPcisIdx, utils.indexesOf(pcis, e))
        );

        // Filling subBeamsIdx.
        /*if (beams){
            if (!reqBeams) subBeamsIdx = beams.map((_, i) => parseInt(i));
            else reqBeams.forEach(
                (e) => utils.interPush(subBeamsIdx, utils.indexesOf(beams, e))
            );
        }*/


        subEarfcnsIdx.filter((i) => {    // Filtering over indexes.

            let e = earfcns[i];     // EARFCN associated to the current index.
            let p = pcis[i];        // PCI associated to the current index.
            /*let b;
            if(beams){
                b = beams[i];
            }*/

            // Searching (e, p) pair in reqEarfcn and reqPcis if possible, evaluating in null otherwise.
            let inter = (reqEarfcns && reqPcis) ?
                utils.indexesOf(reqEarfcns, e).filter(
                    (ear) => utils.indexesOf(reqPcis, p).includes(ear))/*.filter((pci) => utils.indexesOf(reqBeams, b).includes(pci))*/
                : null;

            // Pair found or not possible to find the pair.
            let sameIndex = (inter) ? inter.length !== 0  : true

            // If pair found (if possible), and PCi found.
            return subPcisIdx.includes(i) && sameIndex;

        }).forEach( // Filling result.
            (i) => {
                result.earfcns.push(earfcns[i]);
                result.pcis.push(pcis[i]);
                result.indices.push(i);
                /*if(beams){
                    result.beams.push(beams[i]);
                }*/
            }
        );

        return result;

    },

    /**
     * Pushes elements of arrayB in arrayA if not already in arrayA.
     * 
     * @param {Array} arrayA Array where arrayB elements will be inserted.
     * @param {Array} arrayB Array of elements to be inserted into arrayA.
     */
    interPush: function (arrayA, arrayB) {
        arrayB.forEach(
            (elt) => { if (!arrayA.includes(elt)) arrayA.push(elt); }
        )
    }

}