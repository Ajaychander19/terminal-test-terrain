const utils = {

    deepCopy: function (obj) { return JSON.parse(JSON.stringify(obj)); },

    indexesOf: function (arr, obj) {

        let result = [];
        for (let i in arr) if (obj === arr[i]) result.push(parseInt(i));
        return result;

    },

    indexOfEarpci: function (earfcns, pcis, earfcn, pci) {

        let earfcnIdx = utils.indexesOf(earfcns, earfcn);
        let pcisIdx = utils.indexesOf(pcis, pci);

        let inter = earfcnIdx.filter((e) => pcisIdx.includes(e))

        return inter.length !== 0 ? inter[0] : -1;

    },

    removeEarpci: function (earfcns, pcis, earfcn, pci) {
        
        let i = utils.indexOfEarpci(earfcns, pcis, earfcn, pci);

        if (i !== -1) {
            earfcns.splice(i, 1);
            pcis.splice(i, 1);
        }

    },

    subEarpci: function (earfcns, pcis, reqEarfcns=null, reqPcis=null) {

        let result = {earfcns: [], pcis: [], indices: []};

        let subEarfcnsIdx = [];
        let subPcisIdx = [];

        if (!reqEarfcns) subEarfcnsIdx = earfcns.map((_, i) => parseInt(i));
        else reqEarfcns.forEach(
            (e) => utils.interPush(subEarfcnsIdx, utils.indexesOf(earfcns, e))
        );

        if (!reqPcis) subPcisIdx = pcis.map((_, i) => parseInt(i));
        else reqPcis.forEach(
            (e) => utils.interPush(subPcisIdx, utils.indexesOf(pcis, e))
        );

        subEarfcnsIdx.filter((i, j) => {
            let e = earfcns[i];
            let p = pcis[i];
            let sameIndex = (reqEarfcns && reqPcis) ? utils.indexesOf(reqEarfcns, e).filter((ear) => utils.indexesOf(reqPcis, p).includes(ear)).length !== 0  : true
            return subPcisIdx.includes(i) && sameIndex;
        })
                     .forEach(
                        (i) => {
                            result.earfcns.push(earfcns[i]);
                            result.pcis.push(pcis[i]);
                            result.indices.push(i);
                        }
                     );

        return result;

    },

    interPush: function (arrayA, arrayB) {
        arrayB.forEach(
            (elt) => { if (!arrayA.includes(elt)) arrayA.push(elt); }
        )
    }

}