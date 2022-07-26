const utils = {

    deepCopy: function (obj) { return JSON.parse(JSON.stringify(obj)); },

    indexesOf: function (arr, obj) {

        let result = [];
        for (let i in arr) if (obj === arr[i]) result.push(i);
        return result;

    },

    subEarpci: function (earfcns, pcis, reqEarfcns=null, reqPcis=null) {

        let result = {earfcns: [], pcis: []};

        let subEarfcnsIdx = [];
        let subPcisIdx = [];

        if (!reqEarfcns) subEarfcnsIdx = earfcns.map((_, i) => i);
        else reqEarfcns.forEach(
            (e) => interPush(subEarfcnsIndx, this.indexesOf(earfcns, e))
        );

        if (!reqPcis) subPcisIdx = earfcns.map((_, i) => i);
        else reqEarfcns.forEach(
            (e) => interPush(subPcisIdx, this.indexesOf(earfcns, e))
        );

        subEarfcnsIdx.filter((i) => subPcisIdx.contains(i))
                     .forEach(
                        (i) => {
                            result.earfcns.push(earfcns[i]);
                            result.pcis.push(pcis[i]);
                        }
                     );

        return result;

    },

    interPush: function (arrayA, arrayB) {
        arrayB.forEach(
            (elt) => { if (!arrayA.contains(elt)) arrayA.push(elt); }
        )
    }

}