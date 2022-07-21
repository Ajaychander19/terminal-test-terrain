const utils = {

    deepCopy: function (obj) { return JSON.parse(JSON.stringify(obj)); },

    indexesOf: function (arr, obj) {

        let result = [];
        for (let i in arr) if (obj === arr[i]) result.push(i);
        return result;

    }

}