const utils = {

    deepCopy: function (obj) { return JSON.parse(JSON.stringify(obj)); },

    indexesOf: function (arr, obj) {

        let result = [];
        for (let i in arr) if (obj === arr[i]) result.push(parseInt(i));
        return result;

    },

    subEarpci: function (earfcns, pcis, reqEarfcns=null, reqPcis=null) {

        let result = {earfcns: [], pcis: [], indices: []};

        let subEarfcnsIdx = [];
        let subPcisIdx = [];

        if (!reqEarfcns) subEarfcnsIdx = earfcns.map((_, i) => parseInt(i));
        else reqEarfcns.forEach(
            (e) => this.interPush(subEarfcnsIdx, this.indexesOf(earfcns, e))
        );

        if (!reqPcis) subPcisIdx = pcis.map((_, i) => parseInt(i));
        else reqPcis.forEach(
            (e) => this.interPush(subPcisIdx, this.indexesOf(pcis, e))
        );

        subEarfcnsIdx.filter((i) => subPcisIdx.includes(i))
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